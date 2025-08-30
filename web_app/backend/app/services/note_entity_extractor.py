"""
用户笔记实体抽取服务
基于 extract_problem_entity.py 的方法，专门用于从用户笔记中抽取算法相关实体
"""
import logging
import json
import re
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from extractors.extract_knowledgePoint import  QwenClientNative
# 导入原有的实体抽取相关类
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../extractors'))

try:
    from extract_problem_entity import (
        AlgorithmProblemWithSolution, 
        ComprehensiveAlgorithmExtractor,
        # QwenClientNative,
        ResourceType,
        LanguageType
    )
    EXTRACTOR_AVAILABLE = True
except ImportError as e:
    logging.warning(f"无法导入实体抽取器: {e}")
    EXTRACTOR_AVAILABLE = False

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

@dataclass
class NoteEntity:
    """笔记实体"""
    id: str
    name: str
    type: str  # algorithm, data_structure, technique, problem_type, etc.
    description: str
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    source_note_id: str = ""
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class NoteEntityRelation:
    """笔记实体关系"""
    source_entity: str
    target_entity: str
    relation_type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    source_note_id: str = ""

@dataclass
class NoteExtractionResult:
    """笔记抽取结果"""
    note_id: str
    entities: List[NoteEntity]
    relations: List[NoteEntityRelation]
    raw_extraction: Optional[Dict] = None
    extraction_metadata: Dict[str, Any] = field(default_factory=dict)

class QwenClient:
    """Qwen模型客户端（简化版本）"""
    
    def __init__(self, api_key: str = None, base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.base_url = base_url
        # 这里可以初始化实际的客户端
        
    async def chat_completion_async(self, messages: List[Dict], model: str = "qwen-max") -> str:
        """异步聊天完成（简化实现）"""
        # 这里应该实现实际的API调用
        # 暂时返回模拟结果
        return '{"entities": [], "relations": []}'

class NoteEntityExtractor:
    """用户笔记实体抽取器"""
    
    def __init__(self):
        self.qwen_client = QwenClient()
        self.extractor_available = EXTRACTOR_AVAILABLE

        # 强制使用简单方法进行测试
        self.extractor_available = False
        logger.info(f"实体抽取器初始化，完整抽取器可用: {self.extractor_available}，强制使用简单方法")

        # 算法相关关键词
        self.algorithm_keywords = {
            'algorithm_paradigm': [
                '动态规划', 'DP', '贪心算法', '贪心策略', '分治算法', '分治法',
                '回溯算法', '回溯法', '深度优先搜索', 'DFS', '广度优先搜索', 'BFS',
                '枚举算法', '暴力搜索', '递归算法', '迭代算法'
            ],
            'data_structure': [
                '数组', '链表', '单链表', '双链表', '环形链表',
                '栈', '队列', '优先队列', '双端队列',
                '树', '二叉树', '二叉搜索树', '平衡树', 'AVL树', '红黑树',
                '图', '有向图', '无向图', '加权图',
                '哈希表', '散列表', '字典', '集合',
                '堆', '最大堆', '最小堆', '二叉堆'
            ],
            'technique': [
                '双指针', '快慢指针', '左右指针', '对撞指针',
                '滑动窗口', '固定窗口', '可变窗口',
                '前缀和', '前缀积', '差分数组', '二维前缀和',
                '单调栈', '单调递增栈', '单调递减栈', '单调队列'
            ],
            'problem_type': [
                '01背包问题', '完全背包问题', '多重背包问题',
                '最短路径问题', '最长路径问题',
                '最长公共子序列问题', '最长递增子序列问题',
                '字符串匹配问题', '模式匹配问题'
            ]
        }
    
    async def extract_entities_from_note(self, note_id: str, content: str, title: str = "") -> NoteExtractionResult:
        """从笔记中抽取实体"""
        logger.info(f"开始从笔记 {note_id} 抽取实体")
        
        try:
            # 如果可用，使用完整的实体抽取器
            if self.extractor_available:
                result = await self._extract_with_full_extractor(note_id, content, title)
            else:
                result = await self._extract_with_simple_method(note_id, content, title)
            
            logger.info(f"笔记 {note_id} 实体抽取完成，发现 {len(result.entities)} 个实体")
            return result
            
        except Exception as e:
            logger.error(f"笔记 {note_id} 实体抽取失败: {e}")
            return NoteExtractionResult(
                note_id=note_id,
                entities=[],
                relations=[],
                extraction_metadata={'error': str(e)}
            )
    
    async def _extract_with_full_extractor(self, note_id: str, content: str, title: str) -> NoteExtractionResult:
        """使用完整的实体抽取器"""
        try:
            extractor = ComprehensiveAlgorithmExtractor()
            
            # 使用原有的抽取器
            problem_solution = await extractor.extract(content, source_file=f"note_{note_id}")
            
            # 转换为笔记实体格式
            entities = []
            relations = []
            
            # 转换算法标签
            for tag in problem_solution.algorithm_tags:
                entities.append(NoteEntity(
                    id=f"alg_{hash(tag) % 10000}",
                    name=tag,
                    type="algorithm_paradigm",
                    description=f"算法范式: {tag}",
                    source_note_id=note_id
                ))
            
            # 转换数据结构标签
            for tag in problem_solution.data_structure_tags:
                entities.append(NoteEntity(
                    id=f"ds_{hash(tag) % 10000}",
                    name=tag,
                    type="data_structure",
                    description=f"数据结构: {tag}",
                    source_note_id=note_id
                ))
            
            # 转换技巧标签
            for tag in problem_solution.technique_tags:
                entities.append(NoteEntity(
                    id=f"tech_{hash(tag) % 10000}",
                    name=tag,
                    type="technique",
                    description=f"算法技巧: {tag}",
                    source_note_id=note_id
                ))
            
            return NoteExtractionResult(
                note_id=note_id,
                entities=entities,
                relations=relations,
                raw_extraction=problem_solution.to_dict(),
                extraction_metadata={
                    'method': 'full_extractor',
                    'title': problem_solution.title,
                    'solution_approach': problem_solution.solution_approach
                }
            )
            
        except Exception as e:
            logger.error(f"完整抽取器失败: {e}")
            return await self._extract_with_simple_method(note_id, content, title)
    
    async def _extract_with_simple_method(self, note_id: str, content: str, title: str) -> NoteExtractionResult:
        """使用简单的关键词匹配方法"""
        entities = []
        relations = []
        
        content_lower = content.lower()
        
        # 关键词匹配
        for entity_type, keywords in self.algorithm_keywords.items():
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    entities.append(NoteEntity(
                        id=f"{entity_type}_{hash(keyword) % 10000}",
                        name=keyword,
                        type=entity_type,
                        description=f"从笔记中识别的{entity_type}: {keyword}",
                        confidence=0.8,  # 简单匹配的置信度较低
                        source_note_id=note_id
                    ))

        # 额外的模式匹配
        # 匹配括号相关的内容
        if '括号' in content_lower:
            entities.append(NoteEntity(
                id=f"problem_type_{hash('括号匹配') % 10000}",
                name="括号匹配",
                type="problem_type",
                description="括号匹配问题",
                confidence=0.9,
                source_note_id=note_id
            ))

        # 匹配栈相关的内容
        if any(word in content_lower for word in ['栈', 'stack', '后进先出']):
            entities.append(NoteEntity(
                id=f"data_structure_{hash('栈') % 10000}",
                name="栈",
                type="data_structure",
                description="栈数据结构",
                confidence=0.9,
                source_note_id=note_id
            ))

        # 匹配字符串相关的内容
        if any(word in content_lower for word in ['字符串', 'string', '字符']):
            entities.append(NoteEntity(
                id=f"data_structure_{hash('字符串') % 10000}",
                name="字符串",
                type="data_structure",
                description="字符串数据结构",
                confidence=0.8,
                source_note_id=note_id
            ))
        
        # 去重
        seen_entities = set()
        unique_entities = []
        for entity in entities:
            entity_key = (entity.name, entity.type)
            if entity_key not in seen_entities:
                seen_entities.add(entity_key)
                unique_entities.append(entity)

        # 添加一些基本的关系
        entity_names = [e.name for e in unique_entities]
        if "括号匹配" in entity_names and "栈" in entity_names:
            relations.append(NoteEntityRelation(
                source_entity="括号匹配",
                target_entity="栈",
                relation_type="uses",
                confidence=0.9,
                source_note_id=note_id
            ))
        
        return NoteExtractionResult(
            note_id=note_id,
            entities=unique_entities,
            relations=relations,
            extraction_metadata={
                'method': 'simple_keyword_matching',
                'total_matches': len(entities),
                'unique_entities': len(unique_entities)
            }
        )
    
    def should_merge_with_existing_node(self, entity: NoteEntity, existing_nodes: List[Dict]) -> Tuple[bool, Optional[str]]:
        """判断是否应该与现有节点合并"""
        for node in existing_nodes:
            # 名称完全匹配
            if entity.name.lower() == node.get('name', '').lower():
                return True, node.get('id')
            
            # 同义词匹配（可以扩展）
            if self._are_synonyms(entity.name, node.get('name', '')):
                return True, node.get('id')
        
        return False, None
    
    def _are_synonyms(self, name1: str, name2: str) -> bool:
        """判断两个名称是否为同义词"""
        # 简单的同义词判断，可以扩展
        synonyms_map = {
            'dp': '动态规划',
            'dfs': '深度优先搜索',
            'bfs': '广度优先搜索',
            '哈希表': '散列表',
            '字典': '哈希表'
        }
        
        name1_lower = name1.lower()
        name2_lower = name2.lower()
        
        return (synonyms_map.get(name1_lower) == name2_lower or 
                synonyms_map.get(name2_lower) == name1_lower)

# 全局实例
_note_extractor = None

def get_note_entity_extractor() -> NoteEntityExtractor:
    """获取笔记实体抽取器实例"""
    global _note_extractor
    if _note_extractor is None:
        _note_extractor = NoteEntityExtractor()
    return _note_extractor
