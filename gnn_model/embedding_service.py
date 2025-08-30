import torch
import numpy as np

# 假设嵌入已保存为字典: {entity_id: np.ndarray}
def load_embeddings(path='F:\algokg_platform\models\ensemble_gnn_embedding.pt'):
    emb_dict = torch.load(path, map_location='cpu')
    return {k: v.numpy() for k, v in emb_dict.items()}

def get_embedding(entity_id, emb_dict):
    return emb_dict.get(entity_id, None)
