"""
增强的推荐系统服务 - 基于混合相似度和学习路径的智能推荐
"""

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

logger = logging.getLogger(__name__)

class EnhancedRecommendationSystem:
    """增强的推荐系统服务"""
    
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
            (hybrid_similarity, embedding_similarity, tag_similarity)
        """
        # 1. Embedding相似度
        q_vec = self.embeddings[query_idx].unsqueeze(0)
        t_vec = self.embeddings[target_idx].unsqueeze(0)
        embedding_sim = F.cosine_similarity(q_vec, t_vec).item()
        
        # 2. 标签相似度
        if query_entity_id in self.tag_vectors and target_entity_id in self.tag_vectors:
            q_tags = self.tag_vectors[query_entity_id]
            t_tags = self.tag_vectors[target_entity_id]
            
            # 加权标签相似度
            weighted_q_tags = q_tags * np.array([self.tag_weights.get(tag, 1.0) for tag in self.all_tags])
            weighted_t_tags = t_tags * np.array([self.tag_weights.get(tag, 1.0) for tag in self.all_tags])
            
            if np.linalg.norm(weighted_q_tags) > 0 and np.linalg.norm(weighted_t_tags) > 0:
                tag_sim = cosine_similarity([weighted_q_tags], [weighted_t_tags])[0][0]
            else:
                tag_sim = 0.0
        else:
            tag_sim = 0.0
            
        # 混合相似度
        hybrid_sim = alpha * embedding_sim + (1 - alpha) * tag_sim
        
        return hybrid_sim, embedding_sim, tag_sim
        
    def _generate_learning_path(self, 
                              query_title: str,
                              target_title: str, 
                              shared_tags: List[str]) -> Dict[str, Any]:
        """
        生成学习路径解释
        """
        if not shared_tags:
            return {
                "path_type": "探索性学习",
                "description": f"从《{query_title}》拓展到《{target_title}》，探索新的解题思路",
                "reasoning": "基于embedding相似度推荐，有助于拓展解题视野"
            }
            
        # 按权重排序标签
        weighted_tags = [(tag, self.tag_weights.get(tag, 1.0)) for tag in shared_tags]
        weighted_tags.sort(key=lambda x: x[1], reverse=True)
        
        primary_tag = weighted_tags[0][0]
        secondary_tags = [tag for tag, _ in weighted_tags[1:3]]  # 最多取3个主要标签
        
        path_description = f"《{query_title}》→ [{primary_tag}] → 《{target_title}》"
        
        reasoning_parts = [f"核心知识点: {primary_tag}"]
        if secondary_tags:
            reasoning_parts.append(f"相关技能: {', '.join(secondary_tags)}")
            
        return {
            "path_type": "渐进式学习",
            "primary_concept": primary_tag,
            "secondary_concepts": secondary_tags,
            "path_description": path_description,
            "reasoning": "; ".join(reasoning_parts)
        }
        
    def _diversify_results(self, 
                          candidates: List[Tuple[int, float, Dict]], 
                          diversity_lambda: float = 0.3) -> List[Tuple[int, float, Dict]]:
        """
        使用MMR算法增加结果多样性
        """
        if len(candidates) <= 1:
            return candidates
            
        selected = []
        remaining = candidates.copy()
        
        # 选择第一个（相似度最高的）
        selected.append(remaining.pop(0))
        
        while remaining and len(selected) < len(candidates):
            best_score = -1
            best_idx = -1
            
            for i, (cand_idx, cand_sim, cand_info) in enumerate(remaining):
                # 计算与已选择项目的最大相似度
                max_sim_to_selected = 0
                cand_vec = self.embeddings[cand_idx]
                
                for sel_idx, _, _ in selected:
                    sel_vec = self.embeddings[sel_idx]
                    sim = F.cosine_similarity(cand_vec.unsqueeze(0), sel_vec.unsqueeze(0)).item()
                    max_sim_to_selected = max(max_sim_to_selected, sim)
                
                # MMR分数
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
            learning_path = self._generate_learning_path(
                query_title, info['title'], info['shared_tags']
            )

            results.append({
                "title": info['title'],
                "hybrid_score": round(hybrid_sim, 4),
                "embedding_score": round(info['embedding_similarity'], 4),
                "tag_score": round(info['tag_similarity'], 4),
                "shared_tags": info['shared_tags'],
                "learning_path": learning_path,
                "recommendation_reason": self._generate_recommendation_reason(
                    info['shared_tags'],
                    info['embedding_similarity'],
                    info['tag_similarity']
                )
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
                                      tag_sim: float) -> str:
        """生成推荐理由"""
        reasons = []

        if shared_tags:
            if len(shared_tags) == 1:
                reasons.append(f"同属{shared_tags[0]}类问题")
            else:
                reasons.append(f"涉及{len(shared_tags)}个共同知识点")

        if emb_sim > 0.8:
            reasons.append("解题思路高度相似")
        elif emb_sim > 0.6:
            reasons.append("解题思路相关")

        if tag_sim > 0.5:
            reasons.append("技能要求匹配")

        if not reasons:
            reasons.append("拓展练习推荐")

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
