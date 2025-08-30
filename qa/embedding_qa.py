import torch
import json
import numpy as np
import torch.nn.functional as F
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict, Counter
import logging
from typing import Dict, List, Tuple, Optional, Any
import warnings
warnings.filterwarnings('ignore')

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedRecommendationSystem:
    def __init__(self, 
                 embedding_path: str,
                 entity2id_path: str,
                 id2title_path: str,
                 tag_label_path: str):
        """
        初始化推荐系统
        """
        self.embedding_path = embedding_path
        self.entity2id_path = entity2id_path
        self.id2title_path = id2title_path
        self.tag_label_path = tag_label_path
        
        # 加载数据
        self._load_data()
        self._prepare_tag_features()
        self._calculate_tag_weights()
        
    def _load_data(self):
        """加载所有数据文件"""
        try:
            # 加载embeddings
            self.embeddings = torch.load(self.embedding_path).cpu()
            self.embeddings = F.normalize(self.embeddings, p=2, dim=1)
            logger.info(f"加载embeddings: {self.embeddings.shape}")
            
            # 加载映射文件
            with open(self.entity2id_path, "r", encoding="utf-8") as f:
                self.entity2id = json.load(f)
                
            with open(self.id2title_path, "r", encoding="utf-8") as f:
                self.id2title = json.load(f)
                
            with open(self.tag_label_path, "r", encoding="utf-8") as f:
                raw_id2tags = json.load(f)
                
            # 创建反向映射
            self.id2entity = {v: k for k, v in self.entity2id.items()}
            self.title2id = {v: k for k, v in self.id2title.items()}
            self.id2tags = {f"problem_{k}": v for k, v in raw_id2tags.items()}
            
            logger.info(f"数据加载完成: {len(self.entity2id)} 个实体")
            
        except Exception as e:
            logger.error(f"数据加载失败: {e}")
            raise
            
    def _prepare_tag_features(self):
        """准备标签特征"""
        # 收集所有标签
        all_tags = sorted(set(tag for tags in self.id2tags.values() for tag in tags))
        self.all_tags = all_tags
        
        # 创建多标签编码器
        self.mlb = MultiLabelBinarizer(classes=all_tags)
        self.mlb.fit([all_tags])
        
        # 为每个实体创建标签向量
        self.tag_vectors = {}
        for entity_id, tags in self.id2tags.items():
            if tags:
                tag_vector = self.mlb.transform([tags])[0]
                self.tag_vectors[entity_id] = tag_vector
            else:
                self.tag_vectors[entity_id] = np.zeros(len(all_tags))
                
        logger.info(f"标签特征准备完成: {len(all_tags)} 个标签")
        
    def _calculate_tag_weights(self):
        """计算标签权重（基于逆文档频率）"""
        tag_counts = Counter()
        total_problems = len(self.id2tags)
        
        for tags in self.id2tags.values():
            for tag in tags:
                tag_counts[tag] += 1
                
        # 计算IDF权重
        self.tag_weights = {}
        for tag in self.all_tags:
            count = tag_counts.get(tag, 1)
            idf = np.log(total_problems / count)
            self.tag_weights[tag] = idf
            
        logger.info("标签权重计算完成")
        
    def _calculate_hybrid_similarity(self,
                                   query_idx: int,
                                   target_idx: int,
                                   query_entity_id: str,
                                   target_entity_id: str,
                                   alpha: float = 0.7) -> Tuple[float, float, float]:
        """
        计算混合相似度（embedding + 标签）

        Args:
            query_idx: 查询实体在embedding中的索引
            target_idx: 目标实体在embedding中的索引
            query_entity_id: 查询实体ID
            target_entity_id: 目标实体ID
            alpha: embedding相似度的权重

        Returns:
            Tuple[hybrid_sim, embedding_sim, tag_sim]
        """
        # 1. Embedding相似度 - 使用归一化的embedding
        q_vec = self.embeddings[query_idx].unsqueeze(0)
        t_vec = self.embeddings[target_idx].unsqueeze(0)
        embedding_sim = F.cosine_similarity(q_vec, t_vec).item()

        # 2. 标签相似度 - 使用加权的标签向量
        tag_sim = 0.0
        if query_entity_id in self.tag_vectors and target_entity_id in self.tag_vectors:
            q_tags = self.tag_vectors[query_entity_id]
            t_tags = self.tag_vectors[target_entity_id]

            # 应用IDF权重
            tag_weights_array = np.array([self.tag_weights.get(tag, 1.0) for tag in self.all_tags])
            weighted_q_tags = q_tags * tag_weights_array
            weighted_t_tags = t_tags * tag_weights_array

            # 计算加权余弦相似度
            q_norm = np.linalg.norm(weighted_q_tags)
            t_norm = np.linalg.norm(weighted_t_tags)

            if q_norm > 0 and t_norm > 0:
                tag_sim = np.dot(weighted_q_tags, weighted_t_tags) / (q_norm * t_norm)
            else:
                tag_sim = 0.0

        # 3. 混合相似度计算
        hybrid_sim = alpha * embedding_sim + (1 - alpha) * tag_sim

        return hybrid_sim, embedding_sim, tag_sim
        
    def _generate_learning_path(self,
                              query_title: str,
                              target_title: str,
                              shared_tags: List[str],
                              embedding_sim: float,
                              tag_sim: float) -> Dict[str, Any]:
        """
        生成详细的学习路径解释

        Args:
            query_title: 查询题目
            target_title: 目标题目
            shared_tags: 共同标签
            embedding_sim: embedding相似度
            tag_sim: 标签相似度
        """
        if not shared_tags:
            # 基于embedding相似度的探索性推荐
            if embedding_sim > 0.8:
                path_type = "深度相似学习"
                description = f"从《{query_title}》深入到《{target_title}》，解题思路高度相似"
                reasoning = "基于深度学习模型识别的相似解题模式，有助于巩固核心算法思维"
            elif embedding_sim > 0.6:
                path_type = "拓展性学习"
                description = f"从《{query_title}》拓展到《{target_title}》，探索相关解题思路"
                reasoning = "基于语义相似度推荐，有助于拓展解题视野和思维模式"
            else:
                path_type = "探索性学习"
                description = f"从《{query_title}》探索到《{target_title}》，发现新的解题领域"
                reasoning = "基于潜在语义关联推荐，有助于跨领域学习"

            return {
                "path_type": path_type,
                "path_description": description,
                "reasoning": reasoning,
                "primary_concept": "算法思维",
                "secondary_concepts": []
            }

        # 有共同标签的情况
        # 按IDF权重排序标签（权重越高越重要）
        weighted_tags = [(tag, self.tag_weights.get(tag, 1.0)) for tag in shared_tags]
        weighted_tags.sort(key=lambda x: x[1], reverse=True)

        primary_tag = weighted_tags[0][0]
        secondary_tags = [tag for tag, _ in weighted_tags[1:4]]  # 最多取3个次要标签

        # 根据共同标签数量确定学习路径类型
        if len(shared_tags) >= 3:
            path_type = "系统性学习"
            description = f"《{query_title}》→ [{primary_tag}等{len(shared_tags)}个知识点] → 《{target_title}》"
        elif len(shared_tags) == 2:
            path_type = "关联性学习"
            description = f"《{query_title}》→ [{primary_tag}+{secondary_tags[0] if secondary_tags else ''}] → 《{target_title}》"
        else:
            path_type = "专项学习"
            description = f"《{query_title}》→ [{primary_tag}] → 《{target_title}》"

        # 生成详细的推理说明
        reasoning_parts = [f"核心知识点: {primary_tag}"]
        if secondary_tags:
            reasoning_parts.append(f"相关技能: {', '.join(secondary_tags[:2])}")
        if embedding_sim > 0.7:
            reasoning_parts.append("解题模式高度相似")
        if tag_sim > 0.5:
            reasoning_parts.append("技能要求匹配度高")

        return {
            "path_type": path_type,
            "primary_concept": primary_tag,
            "secondary_concepts": secondary_tags,
            "path_description": description,
            "reasoning": "; ".join(reasoning_parts),
            "similarity_analysis": {
                "embedding_similarity": embedding_sim,
                "tag_similarity": tag_sim,
                "shared_concept_count": len(shared_tags)
            }
        }
        
    def _diversify_results(self,
                          candidates: List[Tuple[int, float, Dict]],
                          diversity_lambda: float = 0.3) -> List[Tuple[int, float, Dict]]:
        """
        使用改进的MMR算法增加结果多样性

        Args:
            candidates: 候选结果列表 [(idx, score, info), ...]
            diversity_lambda: 多样性权重，越大越注重相似度，越小越注重多样性
        """
        if len(candidates) <= 1:
            return candidates

        selected = []
        remaining = candidates.copy()

        # 选择第一个（相似度最高的）
        selected.append(remaining.pop(0))

        while remaining and len(selected) < len(candidates):
            best_score = -float('inf')
            best_idx = -1

            for i, (cand_idx, cand_sim, _) in enumerate(remaining):
                # 计算与已选择项目的最大相似度
                max_sim_to_selected = 0.0
                cand_vec = self.embeddings[cand_idx]

                for sel_idx, _, _ in selected:
                    sel_vec = self.embeddings[sel_idx]
                    sim = F.cosine_similarity(cand_vec.unsqueeze(0), sel_vec.unsqueeze(0)).item()
                    max_sim_to_selected = max(max_sim_to_selected, sim)

                # MMR分数：平衡相似度和多样性
                mmr_score = diversity_lambda * cand_sim - (1 - diversity_lambda) * max_sim_to_selected

                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i

            if best_idx >= 0:
                selected.append(remaining.pop(best_idx))
            else:
                break

        return selected
        
    def recommend(self, 
                 query_title: str, 
                 top_k: int = 10,
                 alpha: float = 0.7,
                 enable_diversity: bool = True,
                 diversity_lambda: float = 0.3) -> Dict[str, Any]:
        """
        主推荐函数
        
        Args:
            query_title: 查询题目标题
            top_k: 返回推荐数量
            alpha: embedding相似度权重 (0-1)
            enable_diversity: 是否启用多样性优化
            diversity_lambda: 多样性权重 (0-1)
        """
        # 输入验证
        if query_title not in self.title2id:
            return {
                "error": f"题目《{query_title}》未找到",
                "suggestions": self._get_similar_titles(query_title)
            }
            
        query_entity_id = self.title2id[query_title]
        if query_entity_id not in self.entity2id:
            return {"error": f"实体ID未找到：{query_entity_id}"}
            
        query_idx = self.entity2id[query_entity_id]
        query_tags = set(self.id2tags.get(query_entity_id, []))
        
        # 计算所有相似度
        candidates = []
        for idx in range(len(self.embeddings)):
            if idx == query_idx:
                continue
                
            target_entity_id = self.id2entity.get(idx)
            if not target_entity_id:
                continue
                
            # 计算混合相似度
            hybrid_sim, emb_sim, tag_sim = self._calculate_hybrid_similarity(
                query_idx, idx, query_entity_id, target_entity_id, alpha
            )
            
            target_title = self.id2title.get(target_entity_id, target_entity_id)
            target_tags = set(self.id2tags.get(target_entity_id, []))
            shared_tags = list(query_tags & target_tags)
            
            candidates.append((idx, hybrid_sim, {
                'entity_id': target_entity_id,
                'title': target_title,
                'embedding_similarity': emb_sim,
                'tag_similarity': tag_sim,
                'shared_tags': shared_tags
            }))
            
        # 排序
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # 多样性优化
        if enable_diversity:
            candidates = self._diversify_results(candidates[:top_k*2], diversity_lambda)
            
        # 取前top_k个
        top_candidates = candidates[:top_k]
        
        # 生成结果
        results = []
        for idx, hybrid_sim, info in top_candidates:
            # 生成学习路径
            learning_path = self._generate_learning_path(
                query_title,
                info['title'],
                info['shared_tags'],
                info['embedding_similarity'],
                info['tag_similarity']
            )

            # 生成推荐理由
            recommendation_reason = self._generate_recommendation_reason(
                info['shared_tags'],
                info['embedding_similarity'],
                info['tag_similarity'],
                hybrid_sim
            )

            results.append({
                "title": info['title'],
                "hybrid_score": round(hybrid_sim, 4),
                "embedding_score": round(info['embedding_similarity'], 4),
                "tag_score": round(info['tag_similarity'], 4),
                "shared_tags": info['shared_tags'],
                "learning_path": learning_path,
                "recommendation_reason": recommendation_reason,
                "learning_path_explanation": learning_path.get("reasoning", ""),
                "clickable": True,  # 标记为可点击
                "complete_info": {
                    "entity_id": info['entity_id'],
                    "difficulty": "未知",  # 可以从其他数据源获取
                    "algorithm_tags": info['shared_tags'],
                    "data_structure_tags": []
                }
            })
            
        return {
            "query": query_title,
            "query_tags": list(query_tags),
            "algorithm_config": {
                "embedding_weight": alpha,
                "tag_weight": 1 - alpha,
                "diversity_enabled": enable_diversity,
                "diversity_lambda": diversity_lambda if enable_diversity else None
            },
            "recommendations": results,
            "total_candidates": len(candidates)
        }
        
    def _generate_recommendation_reason(self,
                                      shared_tags: List[str],
                                      emb_sim: float,
                                      tag_sim: float,
                                      hybrid_score: float) -> str:
        """
        生成详细的推荐理由

        Args:
            shared_tags: 共同标签
            emb_sim: embedding相似度
            tag_sim: 标签相似度
            hybrid_score: 混合得分
        """
        reasons = []

        # 基于共同标签的理由
        if shared_tags:
            if len(shared_tags) >= 3:
                # 选择最重要的标签（基于IDF权重）
                weighted_tags = [(tag, self.tag_weights.get(tag, 1.0)) for tag in shared_tags]
                weighted_tags.sort(key=lambda x: x[1], reverse=True)
                top_tags = [tag for tag, _ in weighted_tags[:2]]
                reasons.append(f"核心技能匹配({', '.join(top_tags)}等{len(shared_tags)}项)")
            elif len(shared_tags) == 2:
                reasons.append(f"双重技能匹配({', '.join(shared_tags)})")
            else:
                reasons.append(f"专项技能匹配({shared_tags[0]})")

        # 基于embedding相似度的理由
        if emb_sim > 0.85:
            reasons.append("解题模式高度相似")
        elif emb_sim > 0.7:
            reasons.append("解题思路相关")
        elif emb_sim > 0.5:
            reasons.append("算法逻辑相近")

        # 基于标签相似度的理由
        if tag_sim > 0.6:
            reasons.append("技能要求高度匹配")
        elif tag_sim > 0.3:
            reasons.append("技能要求部分匹配")

        # 基于综合得分的理由
        if hybrid_score > 0.8:
            reasons.append("强烈推荐")
        elif hybrid_score > 0.6:
            reasons.append("推荐练习")

        # 如果没有明确理由，基于得分给出通用理由
        if not reasons:
            if hybrid_score > 0.4:
                reasons.append("拓展练习推荐")
            else:
                reasons.append("探索性学习推荐")

        return "，".join(reasons)
        
    def _get_similar_titles(self, query: str, max_suggestions: int = 3) -> List[str]:
        """获取相似标题建议"""
        suggestions = []
        query_lower = query.lower()
        
        for title in self.title2id.keys():
            if query_lower in title.lower() or title.lower() in query_lower:
                suggestions.append(title)
                if len(suggestions) >= max_suggestions:
                    break
                    
        return suggestions
        
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        return {
            "total_problems": len(self.id2title),
            "total_tags": len(self.all_tags),
            "embedding_dimension": self.embeddings.shape[1],
            "most_common_tags": Counter(
                tag for tags in self.id2tags.values() for tag in tags
            ).most_common(10)
        }

# === 使用示例 ===
def main():
    # 配置路径
    config = {
        # "embedding_path": "industrial_gnn_embedding.pt",
        "embedding_path": "ensemble_gnn_embedding.pt",
        "entity2id_path": "entity2id.json", 
        "id2title_path": "entity_id_to_title.json",
        "tag_label_path": "problem_id_to_tags.json"
    }
    
    try:
        # 初始化推荐系统
        rec_system = EnhancedRecommendationSystem(**config)
        
        # 显示系统统计信息
        stats = rec_system.get_system_stats()
        print("=== 系统统计信息 ===")
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        print()
        
        # 推荐示例
        test_queries = ["爬楼梯", "跳跃游戏", "两数之和"]

        for query in test_queries:
            print(f"=== 为《{query}》推荐相关题目 ===")

            result = rec_system.recommend(
                query_title=query,
                top_k=5,
                alpha=0.7,  # 70%权重给embedding相似度
                enable_diversity=True,
                diversity_lambda=0.3
            )
        
            if "error" in result:
                print(f"错误: {result['error']}")
                if "suggestions" in result and result["suggestions"]:
                    print(f"建议题目: {', '.join(result['suggestions'])}")
            else:
                print(f"查询题目: {result['query']}")
                print(f"题目标签: {', '.join(result['query_tags'])}")
                print(f"算法配置: {result['algorithm_config']}")
                print(f"候选题目总数: {result['total_candidates']}")
                print()

                for i, rec in enumerate(result['recommendations'], 1):
                    print(f"推荐 {i}: {rec['title']}")
                    print(f"  综合得分: {rec['hybrid_score']}")
                    print(f"  相似度分解: Embedding({rec['embedding_score']}) + 标签({rec['tag_score']})")
                    print(f"  共同标签: {', '.join(rec['shared_tags']) if rec['shared_tags'] else '无'}")
                    print(f"  学习路径: {rec['learning_path']['path_description']}")
                    print(f"  推荐理由: {rec['recommendation_reason']}")
                    print(f"  路径说明: {rec['learning_path']['reasoning']}")
                    print()
            print("=" * 60)
                
    except Exception as e:
        logger.error(f"运行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()