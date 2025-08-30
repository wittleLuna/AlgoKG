import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATv2Conv
from torch_geometric.data import Data
from sklearn.preprocessing import MultiLabelBinarizer
import numpy as np
import pandas as pd
import json, os
from collections import defaultdict

# ========== 1. 数据加载 ==========
def load_all_data(features_path, edge_index_path, triplet_path, tag_label_path,
                  entity2id_path, id2title_path, eval_pairs_path, bert_feat_path=None):
    x = torch.load(features_path)
    edge_index = torch.load(edge_index_path)
    data = Data(x=x, edge_index=edge_index)
    triplets = torch.load(triplet_path)
    with open(tag_label_path, "r", encoding="utf-8") as f: raw_id2tags = json.load(f)
    with open(entity2id_path, "r", encoding="utf-8") as f: entity2id = json.load(f)
    with open(id2title_path, "r", encoding="utf-8") as f: id2title = json.load(f)
    id2tags = {f"problem_{k}": v for k, v in raw_id2tags.items()}
    all_tags = sorted(set(tag for tags in id2tags.values() for tag in tags))
    mlb = MultiLabelBinarizer(classes=all_tags)
    mlb.fit([all_tags])
    num_nodes, tag_dim = x.shape[0], len(all_tags)
    y_multihot = torch.zeros((num_nodes, tag_dim))
    for eid, tags in id2tags.items():
        if eid in entity2id:
            y_multihot[entity2id[eid]] = torch.tensor(mlb.transform([tags])[0], dtype=torch.float)
    # BERT特征
    if bert_feat_path and os.path.exists(bert_feat_path):
        text_feat = torch.load(bert_feat_path)
    else:
        text_feat = y_multihot.clone()
    return data, x, y_multihot, triplets, text_feat, tag_dim, all_tags, entity2id, id2title, eval_pairs_path

# ========== 2. 模型结构 ==========
class TextBERTEncoder(nn.Module):
    def __init__(self, bert_dim, out_dim, dropout=0.2):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(bert_dim, out_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(out_dim, out_dim)
        )
    def forward(self, bert_feat):
        return self.encoder(bert_feat)

class MultiTowerGNN(nn.Module):
    def __init__(self, in_dim, tag_dim, bert_dim, out_dim=128, hid_dim=256, num_heads=8, dropout=0.2):
        super().__init__()
        # GNN塔
        self.gnn_layers = nn.ModuleList([
            GATv2Conv(in_dim, hid_dim, heads=num_heads, dropout=dropout),
            GATv2Conv(hid_dim * num_heads, hid_dim, heads=num_heads, dropout=dropout),
            GATv2Conv(hid_dim * num_heads, out_dim, heads=1, dropout=dropout),
        ])
        self.bn = nn.ModuleList([nn.BatchNorm1d(hid_dim*num_heads), nn.BatchNorm1d(hid_dim*num_heads)])
        self.proj = nn.Linear(in_dim, hid_dim*num_heads)

        # 标签塔
        self.tag_encoder = nn.Sequential(
            nn.Linear(tag_dim, hid_dim), nn.ReLU(),
            nn.Linear(hid_dim, out_dim)
        )
        # BERT塔（可微调）
        self.txt_encoder = TextBERTEncoder(bert_dim, out_dim, dropout=dropout)
        # 多塔融合
        self.fusion = nn.Sequential(
            nn.Linear(out_dim * 3, out_dim * 2),
            nn.GELU(),
            nn.Linear(out_dim * 2, out_dim)
        )
        self.dropout = nn.Dropout(dropout)
        # 标签分类
        self.tag_pred = nn.Sequential(
            nn.Dropout(dropout), 
            nn.Linear(out_dim, tag_dim)
        )

    def forward(self, data, tag_feat, txt_feat):
        x, edge_index = data.x, data.edge_index
        h = x
        for i, conv in enumerate(self.gnn_layers):
            h = F.elu(conv(h, edge_index))
            if i < len(self.bn):
                h = self.bn[i](h)
            h = self.dropout(h)
            if i == 0:
                h = h + self.proj(x)
        z_struct = h
        z_tag = self.tag_encoder(tag_feat)
        z_txt = self.txt_encoder(txt_feat)
        z_fusion = self.fusion(torch.cat([z_struct, z_tag, z_txt], dim=1))
        tag_logits = self.tag_pred(z_fusion)
        return z_struct, z_tag, z_txt, z_fusion, tag_logits

# ========== 3. loss ==========
def supervised_contrastive_loss(emb, labels, temperature=0.2):
    emb = F.normalize(emb, p=2, dim=1)
    mask = (labels @ labels.t()) > 0
    logits = torch.mm(emb, emb.t()) / temperature
    logits = logits - torch.max(logits, dim=1, keepdim=True)[0]
    exp_logits = torch.exp(logits)
    log_prob = logits - torch.log(exp_logits.sum(dim=1, keepdim=True) + 1e-8)
    loss = - (mask.float() * log_prob).sum() / mask.float().sum().clamp_min(1.0)
    return loss

def focal_bce_loss(logits, targets, alpha=0.25, gamma=2.0):
    bce_loss = F.binary_cross_entropy_with_logits(logits, targets, reduction='none')
    pt = torch.exp(-bce_loss)
    focal_loss = alpha * (1 - pt) ** gamma * bce_loss
    return focal_loss.mean()

def embedding_variance_loss(emb):
    return ((emb - emb.mean(0)).pow(2).mean() - 1).abs()

def embedding_center_loss(emb):
    return emb.mean(0).abs().mean()

def mutual_consistency_loss(z1, z2):
    return F.mse_loss(z1, z2)

def proxy_nca_loss(emb, labels, num_classes=None, margin=0.1):
    emb = F.normalize(emb, p=2, dim=1)
    if num_classes is None:
        num_classes = labels.shape[1]
    mask = labels.sum(1) > 0
    emb = emb[mask]
    labels = labels[mask]
    if emb.size(0) == 0:
        return torch.tensor(0.0, device=emb.device)
    lbls = labels.argmax(1)
    if (lbls >= num_classes).any():
        print(f"标签超出proxy数量! lbls.max()={lbls.max()} num_classes={num_classes}")
        raise ValueError("标签超出proxy数量！")
    proxies = F.normalize(torch.randn(num_classes, emb.size(1), device=emb.device), p=2, dim=1)
    dists = (emb.unsqueeze(1) - proxies.unsqueeze(0)).pow(2).sum(-1)
    d_pos = dists[range(len(lbls)), lbls]
    d_neg = dists + torch.eye(num_classes, device=emb.device)[lbls]*1e5
    d_neg = d_neg.min(1)[0]
    return F.relu(d_pos + margin - d_neg).mean()

def smooth_labels(y, smoothing=0.1):
    return y * (1 - smoothing) + 0.5 * smoothing

def cluster_center_loss(emb, labels):
    mask = labels.sum(1) > 0
    centers = []
    loss = 0
    for i in range(labels.size(1)):
        group = emb[labels[:, i] > 0.5]
        if group.size(0) > 0:
            center = group.mean(0)
            loss += ((group - center).pow(2).sum(1)).mean()
    return loss / (labels.size(1) + 1e-8)

@torch.no_grad()
def advanced_hard_negative_mining(emb, y_multihot, topk=2):
    emb = F.normalize(emb, p=2, dim=1)
    N = emb.size(0)
    triplets = []
    for anchor_idx in range(N):
        anchor_emb = emb[anchor_idx]
        anchor_label = y_multihot[anchor_idx]
        overlaps = (y_multihot @ anchor_label) > 0
        overlaps[anchor_idx] = False
        positives = (anchor_label * y_multihot).sum(1) > 0.5
        for pos_idx in torch.where(positives & overlaps)[0].tolist():
            sims = torch.mv(emb, anchor_emb)
            sims[anchor_idx] = -10
            sims[pos_idx] = -10
            hard_negatives = sims.topk(topk)[1].tolist()
            for neg_idx in hard_negatives:
                triplets.append([anchor_idx, pos_idx, neg_idx])
    if len(triplets) == 0:
        # fallback
        triplets = [[i, i, (i+1)%N] for i in range(N)]
    return torch.tensor(triplets, dtype=torch.long, device=emb.device)

# ========== 4. 评估与推荐 ==========
def eval_hits(emb, eval_pairs_path, entity2id, id2title, topk=(1,3,5,10)):
    emb = F.normalize(emb, p=2, dim=1)
    df = pd.read_csv(eval_pairs_path, header=0)
    title2id = {v: k for k, v in id2title.items()}
    q_targets = defaultdict(set)
    for _, row in df.iterrows():
        q_title, t_title = str(row["query"]).strip(), str(row["target"]).strip()
        if q_title in title2id and t_title in title2id:
            q_eid, t_eid = title2id[q_title], title2id[t_title]
            if q_eid in entity2id and t_eid in entity2id:
                q_idx, t_idx = entity2id[q_eid], entity2id[t_eid]
                q_targets[q_idx].add(t_idx)
    hits = {k: 0 for k in topk}
    total = len(q_targets)
    for q_idx, tgt_idxs in q_targets.items():
        sims = F.cosine_similarity(emb[q_idx].unsqueeze(0), emb).cpu()
        top = sims.topk(max(topk)+1).indices.tolist()
        top = [i for i in top if i != q_idx][:max(topk)]
        for k in topk:
            if any(t in top[:k] for t in tgt_idxs):
                hits[k] += 1
    return {k: hits[k]/total for k in topk}

def recommend_online(query_idx, z_fusion, y_multihot, k=10, lambda_emb=0.7, lambda_tag=0.3, diversity=False, diversity_lambda=0.2):
    emb = F.normalize(z_fusion, p=2, dim=1)
    tag_vec = y_multihot
    query_emb = emb[query_idx]
    sim_emb = torch.mv(emb, query_emb)
    sim_tag = (tag_vec @ tag_vec[query_idx]) / (tag_vec[query_idx].sum()+1e-8)
    score = lambda_emb * sim_emb + lambda_tag * sim_tag
    if diversity:
        idxs = []
        candidates = score.argsort(descending=True).tolist()
        for idx in candidates:
            if len(idxs) >= k:
                break
            if not idxs:
                idxs.append(idx)
                continue
            diversity_score = 0
            for prev in idxs:
                diversity_score += 1 - F.cosine_similarity(emb[idx].unsqueeze(0), emb[prev].unsqueeze(0)).item()
            diversity_score = diversity_score / len(idxs)
            if diversity_score > diversity_lambda:
                idxs.append(idx)
        return idxs[:k]
    return score.topk(k).indices.tolist()

# ========== 5. 训练主循环 ==========
def train_and_eval(
    features_path, edge_index_path, triplet_path, tag_label_path, entity2id_path,
    id2title_path, eval_pairs_path, model_output_path, embedding_output_path,
    num_epochs=300, patience=50, device=None, bert_feat_path=None,
    ensemble_times=3
):
    data, x, y_multihot, triplets, text_feat, tag_dim, all_tags, entity2id, id2title, eval_pairs_path = load_all_data(
        features_path, edge_index_path, triplet_path, tag_label_path,
        entity2id_path, id2title_path, eval_pairs_path, bert_feat_path=bert_feat_path
    )
    if device is None:
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    all_embeddings = []
    best_hit10 = 0
    for round_seed in range(ensemble_times):
        print(f"==== 模型训练（第 {round_seed+1} 轮 Ensemble）====")
        torch.manual_seed(2333 + round_seed)
        np.random.seed(2333 + round_seed)
        model = MultiTowerGNN(x.shape[1], tag_dim, text_feat.shape[1]).to(device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=2e-4, weight_decay=2e-4)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, num_epochs)
        x_, y_multihot_, triplets_, text_feat_ = x.to(device), y_multihot.to(device), triplets.to(device), text_feat.to(device)
        data_ = data.to(device)

        best_local_hit10, no_improve, best_z = -1, 0, None
        for epoch in range(1, num_epochs+1):
            model.train()
            optimizer.zero_grad()
            tag_feat = y_multihot_
            z_struct, z_tag, z_txt, z_fusion, tag_logits = model(data_, tag_feat, text_feat_)
            z_struct, z_tag, z_txt, z_fusion = [F.normalize(x, p=2, dim=1) for x in [z_struct, z_tag, z_txt, z_fusion]]

            # 动态 hard negative mining
            if epoch % 10 == 1:
                with torch.no_grad():
                    triplets_hard = advanced_hard_negative_mining(z_struct, y_multihot_, topk=2)
            else:
                triplets_hard = triplets_
            anc, pos, neg = triplets_hard[:,0], triplets_hard[:,1], triplets_hard[:,2]

            # 多任务loss + cluster/label smoothing
            loss_rank = F.margin_ranking_loss(
                F.cosine_similarity(z_struct[anc], z_struct[pos]),
                F.cosine_similarity(z_struct[anc], z_struct[neg]),
                torch.ones_like(anc, dtype=torch.float, device=device),
                margin=0.8
            )
            mask = y_multihot_.sum(dim=1) > 0
            loss_tag = focal_bce_loss(tag_logits[mask], smooth_labels(y_multihot_[mask], 0.1)) if mask.sum()>0 else torch.tensor(0.0, device=device)
            loss_supcon = supervised_contrastive_loss(z_struct[mask], y_multihot_[mask]) if mask.sum()>1 else torch.tensor(0.0, device=device)
            loss_supcon_tag = supervised_contrastive_loss(z_tag[mask], y_multihot_[mask]) if mask.sum()>1 else torch.tensor(0.0, device=device)
            loss_align = mutual_consistency_loss(z_struct, z_tag) + mutual_consistency_loss(z_struct, z_txt) + mutual_consistency_loss(z_tag, z_txt)
            loss_proxy = proxy_nca_loss(z_struct[mask], y_multihot_[mask], num_classes=tag_dim, margin=0.1) if mask.sum()>1 else torch.tensor(0.0, device=device)
            loss_var = embedding_variance_loss(z_fusion)
            loss_center = embedding_center_loss(z_fusion)
            loss_cluster = cluster_center_loss(z_fusion, y_multihot_)

            total_loss = (
                1.0*loss_rank + 0.1*loss_tag + 0.06*loss_align +
                0.05*loss_supcon + 0.03*loss_supcon_tag + 0.05*loss_proxy +
                0.01*loss_var + 0.01*loss_center + 0.03*loss_cluster
            )
            total_loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            if epoch % 10 == 0 or epoch == 1 or epoch == num_epochs:
                mean, std = z_fusion.mean().item(), z_fusion.std().item()
                print(f"[Ep {epoch:03d}] loss={total_loss.item():.4f} rank={loss_rank.item():.4f} tag={loss_tag.item():.4f} "
                      f"align={loss_align.item():.4f} supcon={loss_supcon.item():.4f} proxy={loss_proxy.item():.4f} "
                      f"var={loss_var.item():.4f} center={loss_center.item():.4f} cluster={loss_cluster.item():.4f} | emb mean={mean:.4f} std={std:.4f}")
                if std < 0.04:
                    print("⚠️  embedding collapse（std极低）警告，请增大variance/cluster loss权重！")
                hits = eval_hits(z_fusion, eval_pairs_path, entity2id, id2title)
                print("    Hits@K: " + " ".join([f"H@{k}:{hits[k]:.3f}" for k in (1,3,5,10)]))
                if hits[10] > best_local_hit10:
                    best_local_hit10 = hits[10]
                    best_z = z_fusion.cpu()
                    torch.save(model.state_dict(), f"{model_output_path}.ensemble{round_seed}")
                    torch.save(z_fusion.cpu(), f"{embedding_output_path}.ensemble{round_seed}")
                    print(f"    ↑ Save best model! (Hit@10={best_local_hit10:.3f})")
                    no_improve = 0
                else:
                    no_improve += 1
            if no_improve >= patience:
                print(f"Early stopping at epoch {epoch}")
                break
        all_embeddings.append(best_z)
        best_hit10 = max(best_hit10, best_local_hit10)

    # Ensemble融合
    z_fusion = torch.stack(all_embeddings).mean(0)
    print(f"\n✔️ 训练完成，Ensemble Hit@10={best_hit10:.3f}")
    return z_fusion, y_multihot, all_tags, entity2id, id2title

# ========== 6. 导出 embedding ==========
def export_embedding(z_fusion, entity2id, id2title, save_path):
    id2embedding = {eid: z_fusion[idx].detach().cpu().numpy().tolist()
                for eid, idx in entity2id.items()}
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(id2embedding, f)
    print(f"导出embedding到 {save_path}")

# ========== 7. 在线推荐 ==========
def get_recommendations(query_title, z_fusion, y_multihot, entity2id, id2title, k=10):
    rev_id2title = {v: k for k, v in id2title.items()}
    if query_title in rev_id2title and rev_id2title[query_title] in entity2id:
        query_idx = entity2id[rev_id2title[query_title]]
        idxs = recommend_online(query_idx, z_fusion, y_multihot, k=k, diversity=True)
        print(f"\n推荐给《{query_title}》的相关题目：")
        for i, idx in enumerate(idxs, 1):
            print(f"Top{i}: {id2title.get(list(entity2id.keys())[list(entity2id.values()).index(idx)], idx)}")
    else:
        print(f"{query_title} 未找到对应节点")

# ========== 8. 脚本入口 ==========
if __name__ == "__main__":
    features_path = "F:/My_project/node_features_augmented.pt"
    edge_index_path = "F:/My_project/edge_index_with_problem_edges.pt"
    triplet_path = "F:/My_project/triplet_indices_hard_neg.pt"
    tag_label_path = "F:/My_project/problem_id_to_tags.json"
    entity2id_path = "F:/My_project/entity2id.json"
    id2title_path = "F:/My_project/entity_id_to_title.json"
    eval_pairs_path = "F:/My_project/gat_recommend_eval_pairs.csv"
    model_output_path = "F:/My_project/ensemble_gnn_model.pt"
    embedding_output_path = "F:/My_project/ensemble_gnn_embedding.pt"
    embedding_json_path = "F:/My_project/ensemble_gnn_embedding.json"
    bert_feat_path = "F:/My_project/bert_title_features.pt"   # 填你实际的BERT路径

    z_fusion, y_multihot, all_tags, entity2id, id2title = train_and_eval(
        features_path, edge_index_path, triplet_path, tag_label_path,
        entity2id_path, id2title_path, eval_pairs_path, model_output_path,
        embedding_output_path, num_epochs=300, patience=50, device=None,
        bert_feat_path=bert_feat_path, ensemble_times=3  # 多次模型融合
    )
    # 导出 embedding
    export_embedding(z_fusion, entity2id, id2title, embedding_json_path)
    # 推荐示例
    get_recommendations("跳跃游戏", z_fusion, y_multihot, entity2id, id2title, k=10)
