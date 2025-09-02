# 批量LeetCode知识图谱构建系统
# 支持从文件夹结构批量读取题目并构建知识图谱

import os
import json
import re
import asyncio
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Generator
from concurrent.futures import ThreadPoolExecutor, as_completed
from neo4j import GraphDatabase
import logging
from collections import defaultdict, Counter
import hashlib
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('knowledge_graph_builder.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ===== 1. 扩展的实体和本体定义 =====

@dataclass
class Entity:
    """基础实体类"""
    id: str
    name: str
    type: str
    properties: Dict = field(default_factory=dict)
    source_file: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
@dataclass
class Relationship:
    """关系类"""
    source: str
    target: str
    type: str
    properties: Dict = field(default_factory=dict)
    confidence: float = 1.0
    source_file: Optional[str] = None

@dataclass
class CategoryInfo:
    """分类信息"""
    name: str
    path: str
    problem_count: int = 0
    parent_category: Optional[str] = None

class ExtendedLeetCodeOntology:
    """扩展的LeetCode领域本体定义"""
    
    # 实体类型定义
    ENTITY_TYPES = {
        'Problem': {
            'properties': ['title', 'description', 'difficulty', 'url', 'platform', 'category', 'subcategory'],
            'description': '算法题目'
        },
        'Category': {
            'properties': ['name', 'path', 'problem_count', 'level'],
            'description': '题目分类'
        },
        'Algorithm': {
            'properties': ['name', 'category', 'time_complexity', 'space_complexity', 'description'],
            'description': '算法类型'
        },
        'DataStructure': {
            'properties': ['name', 'category', 'operations', 'complexity_characteristics'],
            'description': '数据结构'
        },
        'Technique': {
            'properties': ['name', 'description', 'complexity_impact', 'difficulty_level'],
            'description': '编程技巧'
        },
        'Solution': {
            'properties': ['language', 'code', 'explanation', 'time_complexity', 'space_complexity', 'approach'],
            'description': '解决方案'
        },
        'Complexity': {
            'properties': ['notation', 'type', 'value', 'description'],
            'description': '复杂度'
        },
        'Language': {
            'properties': ['name', 'paradigm', 'syntax_family', 'performance_characteristics'],
            'description': '编程语言'
        },
        'Insight': {
            'properties': ['content', 'importance', 'category', 'applicability'],
            'description': '关键洞察'
        },
        'Pattern': {
            'properties': ['name', 'description', 'applications', 'related_algorithms'],
            'description': '算法模式'
        },
        'Difficulty': {
            'properties': ['level', 'description', 'typical_complexity'],
            'description': '难度等级'
        }
    }
    
    # 扩展的关系类型定义
    RELATIONSHIP_TYPES = {
        # 原有关系
        'USES_ALGORITHM': {'domain': 'Problem', 'range': 'Algorithm'},
        'REQUIRES_DATA_STRUCTURE': {'domain': 'Problem', 'range': 'DataStructure'},
        'APPLIES_TECHNIQUE': {'domain': 'Problem', 'range': 'Technique'},
        'HAS_SOLUTION': {'domain': 'Problem', 'range': 'Solution'},
        'IMPLEMENTED_IN': {'domain': 'Solution', 'range': 'Language'},
        'HAS_TIME_COMPLEXITY': {'domain': ['Problem', 'Solution', 'Algorithm'], 'range': 'Complexity'},
        'HAS_SPACE_COMPLEXITY': {'domain': ['Problem', 'Solution', 'Algorithm'], 'range': 'Complexity'},
        'PROVIDES_INSIGHT': {'domain': 'Problem', 'range': 'Insight'},
        'FOLLOWS_PATTERN': {'domain': 'Problem', 'range': 'Pattern'},
        
        # 新增关系
        'BELONGS_TO_CATEGORY': {'domain': 'Problem', 'range': 'Category'},
        'SUBCATEGORY_OF': {'domain': 'Category', 'range': 'Category'},
        'SIMILAR_TO': {'domain': 'Problem', 'range': 'Problem'},
        'PREREQUISITE_OF': {'domain': 'Problem', 'range': 'Problem'},
        'HARDER_THAN': {'domain': 'Problem', 'range': 'Problem'},
        'ALGORITHM_USES_DATA_STRUCTURE': {'domain': 'Algorithm', 'range': 'DataStructure'},
        'TECHNIQUE_OPTIMIZES': {'domain': 'Technique', 'range': 'Algorithm'},
        'HAS_DIFFICULTY': {'domain': 'Problem', 'range': 'Difficulty'},
        'PATTERN_USES_ALGORITHM': {'domain': 'Pattern', 'range': 'Algorithm'},
        'ALGORITHM_CATEGORY': {'domain': 'Algorithm', 'range': 'Category'},
        'CO_OCCURS_WITH': {'domain': ['Algorithm', 'DataStructure', 'Technique'], 'range': ['Algorithm', 'DataStructure', 'Technique']},
    }

class BatchEntityExtractor:
    """批量实体识别器"""
    
    def __init__(self):
        self.ontology = ExtendedLeetCodeOntology()
        self.category_cache = {}
        self.algorithm_stats = Counter()
        self.data_structure_stats = Counter()
        self.technique_stats = Counter()
        
    def extract_category_from_path(self, file_path: str) -> CategoryInfo:
        """从文件路径提取分类信息"""
        path = Path(file_path)
        
        # 提取分类层次：F:\My_project\problem_extration\单调栈\下一个更大元素 I.json
        parts = path.parts
        if len(parts) >= 2:
            # 找到problem_extration后的路径部分
            try:
                extraction_index = parts.index('problem_extration')
                if extraction_index + 1 < len(parts):
                    category_name = parts[extraction_index + 1]
                    return CategoryInfo(
                        name=category_name,
                        path=str(path.parent),
                        parent_category=None  # 可以进一步扩展层次结构
                    )
            except ValueError:
                pass
        
        # 默认分类
        return CategoryInfo(name="未分类", path=str(path.parent))
    
    def extract_entities_batch(self, problem_data_list: List[Tuple[Dict, str]]) -> Tuple[List[Entity], Dict[str, CategoryInfo]]:
        """批量提取实体"""
        all_entities = []
        categories = {}
        
        logger.info(f"开始批量提取 {len(problem_data_list)} 个题目的实体...")
        
        for problem_data, file_path in problem_data_list:
            try:
                # 提取分类信息
                category_info = self.extract_category_from_path(file_path)
                if category_info.name not in categories:
                    categories[category_info.name] = category_info
                categories[category_info.name].problem_count += 1
                
                # 提取单个题目的实体
                entities = self.extract_entities_single(problem_data, file_path, category_info)
                all_entities.extend(entities)
                
                # 更新统计信息
                self._update_stats(problem_data)
                
            except Exception as e:
                logger.error(f"提取实体失败: {file_path}, 错误: {e}")
        
        # 创建分类实体
        category_entities = self._create_category_entities(categories)
        all_entities.extend(category_entities)
        
        # 创建统计相关的实体（如高频算法、数据结构等）
        stat_entities = self._create_statistical_entities()
        all_entities.extend(stat_entities)
        
        logger.info(f"批量实体提取完成，共提取 {len(all_entities)} 个实体")
        return all_entities, categories
    
    def extract_entities_single(self, problem_data: Dict, file_path: str, category_info: CategoryInfo) -> List[Entity]:
        """提取单个题目的实体"""
        entities = []
        
        # 1. 提取问题实体
        problem_entity = self._extract_problem_entity(problem_data, file_path, category_info)
        entities.append(problem_entity)
        
        # 2. 提取算法实体
        algorithm_entities = self._extract_algorithm_entities(problem_data, file_path)
        entities.extend(algorithm_entities)
        
        # 3. 提取数据结构实体
        data_structure_entities = self._extract_data_structure_entities(problem_data, file_path)
        entities.extend(data_structure_entities)
        
        # 4. 提取技术实体
        technique_entities = self._extract_technique_entities(problem_data, file_path)
        entities.extend(technique_entities)
        
        # 5. 提取解决方案实体
        solution_entities = self._extract_solution_entities(problem_data, file_path)
        entities.extend(solution_entities)
        
        # 6. 提取复杂度实体
        complexity_entities = self._extract_complexity_entities(problem_data, file_path)
        entities.extend(complexity_entities)
        
        # 7. 提取编程语言实体
        language_entities = self._extract_language_entities(problem_data, file_path)
        entities.extend(language_entities)
        
        # 8. 提取洞察实体
        insight_entities = self._extract_insight_entities(problem_data, file_path)
        entities.extend(insight_entities)
        
        # 9. 提取难度实体
        difficulty_entity = self._extract_difficulty_entity(problem_data, file_path)
        if difficulty_entity:
            entities.append(difficulty_entity)
        
        return entities
    
    def _extract_problem_entity(self, data: Dict, file_path: str, category_info: CategoryInfo) -> Entity:
        """提取问题实体"""
        return Entity(
            id=f"problem_{self._generate_problem_id(data)}",
            name=data.get('title', '未知题目'),
            type='Problem',
            properties={
                'title': data.get('title', ''),
                'description': data.get('description', ''),
                'difficulty': data.get('difficulty', ''),
                'url': data.get('url', ''),
                'platform': data.get('platform', 'leetcode'),
                'category': category_info.name,
                'solution_approach': data.get('solution_approach', ''),
                'problem_id': data.get('id', '')
            },
            source_file=file_path
        )
    
    def _extract_algorithm_entities(self, data: Dict, file_path: str) -> List[Entity]:
        """提取算法实体"""
        entities = []
        for tag in data.get('algorithm_tags', []):
            entity_id = f"algorithm_{self._normalize_name(tag)}"
            entity = Entity(
                id=entity_id,
                name=tag,
                type='Algorithm',
                properties={
                    'name': tag,
                    'category': self._get_algorithm_category(tag),
                    'description': self._get_algorithm_description(tag)
                },
                source_file=file_path
            )
            entities.append(entity)
        return entities
    
    def _extract_data_structure_entities(self, data: Dict, file_path: str) -> List[Entity]:
        """提取数据结构实体"""
        entities = []
        for tag in data.get('data_structure_tags', []):
            entity_id = f"ds_{self._normalize_name(tag)}"
            entity = Entity(
                id=entity_id,
                name=tag,
                type='DataStructure',
                properties={
                    'name': tag,
                    'category': self._get_data_structure_category(tag),
                    'operations': self._get_data_structure_operations(tag)
                },
                source_file=file_path
            )
            entities.append(entity)
        return entities
    
    def _extract_technique_entities(self, data: Dict, file_path: str) -> List[Entity]:
        """提取技术实体"""
        entities = []
        for tag in data.get('technique_tags', []):
            entity_id = f"technique_{self._normalize_name(tag)}"
            entity = Entity(
                id=entity_id,
                name=tag,
                type='Technique',
                properties={
                    'name': tag,
                    'description': self._get_technique_description(tag),
                    'difficulty_level': self._get_technique_difficulty(tag)
                },
                source_file=file_path
            )
            entities.append(entity)
        return entities
    
    def _extract_solution_entities(self, data: Dict, file_path: str) -> List[Entity]:
        """提取解决方案实体"""
        entities = []
        problem_id = self._generate_problem_id(data)
        
        for i, solution in enumerate(data.get('code_solutions', [])):
            entity_id = f"solution_{problem_id}_{self._normalize_name(solution.get('language', ''))}_#{i}"
            entity = Entity(
                id=entity_id,
                name=f"{solution.get('language', '未知')}解决方案",
                type='Solution',
                properties={
                    'language': solution.get('language', ''),
                    'code': solution.get('code', ''),
                    'description': solution.get('description', ''),
                    'approach': solution.get('approach', ''),
                    'problem_id': problem_id
                },
                source_file=file_path
            )
            entities.append(entity)
        return entities
    
    def _extract_complexity_entities(self, data: Dict, file_path: str) -> List[Entity]:
        """提取复杂度实体"""
        entities = []
        complexity_analysis = data.get('complexity_analysis', {})
        problem_id = self._generate_problem_id(data)
        
        if 'time_complexity' in complexity_analysis:
            entity = Entity(
                id=f"time_complexity_{self._normalize_complexity(complexity_analysis['time_complexity'])}",
                name=complexity_analysis['time_complexity'],
                type='Complexity',
                properties={
                    'notation': complexity_analysis['time_complexity'],
                    'type': 'time',
                    'description': self._get_complexity_description(complexity_analysis['time_complexity']),
                    'problem_id': problem_id
                },
                source_file=file_path
            )
            entities.append(entity)
        
        if 'space_complexity' in complexity_analysis:
            entity = Entity(
                id=f"space_complexity_{self._normalize_complexity(complexity_analysis['space_complexity'])}",
                name=complexity_analysis['space_complexity'],
                type='Complexity',
                properties={
                    'notation': complexity_analysis['space_complexity'],
                    'type': 'space',
                    'description': self._get_complexity_description(complexity_analysis['space_complexity']),
                    'problem_id': problem_id
                },
                source_file=file_path
            )
            entities.append(entity)
        
        return entities
    
    def _extract_language_entities(self, data: Dict, file_path: str) -> List[Entity]:
        """提取编程语言实体"""
        entities = []
        languages = set()
        
        # 从解决方案中提取语言
        for solution in data.get('code_solutions', []):
            languages.add(solution.get('language', ''))
        
        for lang in languages:
            if lang:  # 排除空字符串
                entity = Entity(
                    id=f"language_{self._normalize_name(lang)}",
                    name=lang,
                    type='Language',
                    properties={
                        'name': lang,
                        'paradigm': self._get_language_paradigm(lang),
                        'syntax_family': self._get_language_syntax_family(lang)
                    },
                    source_file=file_path
                )
                entities.append(entity)
        
        return entities
    
    def _extract_insight_entities(self, data: Dict, file_path: str) -> List[Entity]:
        """提取洞察实体"""
        entities = []
        problem_id = self._generate_problem_id(data)
        
        for i, insight in enumerate(data.get('key_insights', [])):
            if isinstance(insight, dict):
                content = insight.get('content', '')
            else:
                content = str(insight)
            
            if content:  # 只有非空内容才创建实体
                entity = Entity(
                    id=f"insight_{problem_id}_{i}",
                    name=f"洞察{i+1}",
                    type='Insight',
                    properties={
                        'content': content,
                        'problem_id': problem_id,
                        'importance': insight.get('importance', 'medium') if isinstance(insight, dict) else 'medium',
                        'category': self._categorize_insight(content)
                    },
                    source_file=file_path
                )
                entities.append(entity)
        
        return entities
    
    def _extract_difficulty_entity(self, data: Dict, file_path: str) -> Optional[Entity]:
        """提取难度实体"""
        difficulty = data.get('difficulty') or []
        if difficulty:
            return Entity(
                id=f"difficulty_{self._normalize_name(difficulty)}",
                name=difficulty,
                type='Difficulty',
                properties={
                    'level': difficulty,
                    'description': self._get_difficulty_description(difficulty)
                },
                source_file=file_path
            )
        return None
    
    def _create_category_entities(self, categories: Dict[str, CategoryInfo]) -> List[Entity]:
        """创建分类实体"""
        entities = []
        for category_name, category_info in categories.items():
            entity = Entity(
                id=f"category_{self._normalize_name(category_name)}",
                name=category_name,
                type='Category',
                properties={
                    'name': category_name,
                    'path': category_info.path,
                    'problem_count': category_info.problem_count,
                    'level': 1  # 可以扩展为多层级
                }
            )
            entities.append(entity)
        return entities
    
    def _create_statistical_entities(self) -> List[Entity]:
        """创建统计相关的实体"""
        entities = []
        
        # 创建高频算法模式实体
        for algorithm, count in self.algorithm_stats.most_common(10):
            if count >= 3:  # 至少出现3次才认为是重要模式
                entity = Entity(
                    id=f"pattern_{self._normalize_name(algorithm)}",
                    name=f"{algorithm}模式",
                    type='Pattern',
                    properties={
                        'name': f"{algorithm}模式",
                        'description': f"基于{algorithm}的常见解题模式",
                        'frequency': count,
                        'related_algorithms': [algorithm]
                    }
                )
                entities.append(entity)
        
        return entities
    
    def _update_stats(self, problem_data: Dict):
        """更新统计信息"""
        for tag in problem_data.get('algorithm_tags', []):
            self.algorithm_stats[tag] += 1
        for tag in problem_data.get('data_structure_tags', []):
            self.data_structure_stats[tag] += 1
        for tag in problem_data.get('technique_tags', []):
            self.technique_stats[tag] += 1
    
    def _generate_problem_id(self, data: Dict) -> str:
        """生成问题ID"""
        if 'id' in data and data['id']:
            return str(data['id'])
        # 使用标题生成唯一ID
        title = data.get('title', 'unknown')
        return hashlib.md5(title.encode('utf-8')).hexdigest()[:12]
    
    def _normalize_name(self, name: str) -> str:
        """标准化名称用于ID"""
        return re.sub(r'[^\w\u4e00-\u9fff]', '_', str(name).lower())
    
    def _normalize_complexity(self, complexity: str) -> str:
        """标准化复杂度"""
        return re.sub(r'[^\w]', '_', str(complexity).lower())
    
    # 辅助方法
    def _get_algorithm_category(self, algorithm: str) -> str:
        categories = {
            '哈希': '查找算法', '数组': '基础操作', '双指针': '数组技巧',
            '排序': '排序算法', '搜索': '搜索算法', '动态规划': '优化算法',
            '贪心': '优化算法', '回溯': '搜索算法', '分治': '分治算法',
            '单调栈': '栈相关', '滑动窗口': '数组技巧', '二分查找': '查找算法'
        }
        return categories.get(algorithm, '其他')
    
    def _get_algorithm_description(self, algorithm: str) -> str:
        descriptions = {
            '哈希': '基于散列的快速查找算法',
            '双指针': '使用两个指针优化数组操作',
            '动态规划': '通过子问题最优解构建全局最优解',
            '单调栈': '维护单调性质的栈结构'
        }
        return descriptions.get(algorithm, f'{algorithm}算法')
    
    def _get_data_structure_category(self, ds: str) -> str:
        categories = {
            '哈希表': '散列结构', '映射(map)': '键值存储', '数组': '线性结构',
            '链表': '线性结构', '树': '层次结构', '栈': '线性结构',
            '队列': '线性结构', '堆': '树形结构'
        }
        return categories.get(ds, '其他')
    
    def _get_data_structure_operations(self, ds: str) -> List[str]:
        operations = {
            '哈希表': ['insert', 'delete', 'search'],
            '数组': ['access', 'insert', 'delete'],
            '栈': ['push', 'pop', 'top'],
            '队列': ['enqueue', 'dequeue', 'front']
        }
        return operations.get(ds, [])
    
    def _get_technique_description(self, technique: str) -> str:
        descriptions = {
            '一次遍历': '通过单次遍历解决问题，提高效率',
            '空间换时间': '使用额外空间来减少时间复杂度',
            '哈希查找': '利用哈希表实现O(1)查找',
            '双指针': '使用两个指针优化搜索和操作'
        }
        return descriptions.get(technique, technique)
    
    def _get_technique_difficulty(self, technique: str) -> str:
        difficulties = {
            '一次遍历': '简单',
            '双指针': '中等',
            '滑动窗口': '中等',
            '单调栈': '困难'
        }
        return difficulties.get(technique, '中等')
    
    def _get_language_paradigm(self, language: str) -> str:
        paradigms = {
            'Python': '多范式', 'Java': '面向对象', 'C++': '多范式',
            'JavaScript': '多范式', 'Go': '过程式', 'Rust': '系统编程'
        }
        return paradigms.get(language, '未知')
    
    def _get_language_syntax_family(self, language: str) -> str:
        families = {
            'Python': 'Python', 'Java': 'C-like', 'C++': 'C-like',
            'JavaScript': 'C-like', 'Go': 'C-like', 'Rust': 'Rust'
        }
        return families.get(language, '其他')
    
    def _get_complexity_description(self, complexity: str) -> str:
        descriptions = {
            'O(1)': '常数时间复杂度',
            'O(n)': '线性时间复杂度',
            'O(log n)': '对数时间复杂度',
            'O(n log n)': '线性对数时间复杂度',
            'O(n^2)': '平方时间复杂度'
        }
        return descriptions.get(complexity, f'复杂度为{complexity}')
    
    def _categorize_insight(self, content: str) -> str:
        """洞察内容分类"""
        content_lower = content.lower()
        if '哈希' in content_lower or 'hash' in content_lower:
            return '数据结构'
        elif '复杂度' in content_lower or 'complexity' in content_lower:
            return '性能优化'
        elif '算法' in content_lower or 'algorithm' in content_lower:
            return '算法设计'
        else:
            return '通用技巧'
    
    def _get_difficulty_description(self, difficulty: str) -> str:
        descriptions = {
            '简单': '基础算法和数据结构应用',
            '中等': '需要一定的算法思维和技巧',
            '困难': '复杂的算法设计和优化'
        }
        return descriptions.get(difficulty, difficulty)

class BatchRelationshipExtractor:
    """批量关系提取器"""
    
    def __init__(self):
        self.ontology = ExtendedLeetCodeOntology()
        self.similarity_threshold = 0.7
    
    def extract_relationships_batch(self, entities: List[Entity], categories: Dict[str, CategoryInfo]) -> List[Relationship]:
        """批量提取关系"""
        relationships = []
        
        # 按类型分组实体
        entities_by_type = defaultdict(list)
        entities_by_id = {}
        
        for entity in entities:
            entities_by_type[entity.type].append(entity)
            entities_by_id[entity.id] = entity
        
        logger.info("开始批量关系提取...")
        
        # 1. 提取基本关系（问题与其组件的关系）
        basic_relationships = self._extract_basic_relationships(entities_by_type, entities_by_id)
        relationships.extend(basic_relationships)
        
        # 2. 提取分类关系
        category_relationships = self._extract_category_relationships(entities_by_type, categories)
        relationships.extend(category_relationships)
        
        # 3. 提取相似性关系
        similarity_relationships = self._extract_similarity_relationships(entities_by_type)
        relationships.extend(similarity_relationships)
        
        # 4. 提取统计关系
        statistical_relationships = self._extract_statistical_relationships(entities_by_type)
        relationships.extend(statistical_relationships)
        
        # 5. 提取共现关系
        cooccurrence_relationships = self._extract_cooccurrence_relationships(entities_by_type)
        relationships.extend(cooccurrence_relationships)
        
        logger.info(f"批量关系提取完成，共提取 {len(relationships)} 个关系")
        return relationships
    
    def _extract_basic_relationships(self, entities_by_type: Dict, entities_by_id: Dict) -> List[Relationship]:
        """提取基本关系"""
        relationships = []
        
        problems = entities_by_type.get('Problem', [])
        
        for problem in problems:
            problem_id = problem.properties.get('problem_id', problem.id.replace('problem_', ''))
            
            # 问题与算法
            for algorithm in entities_by_type.get('Algorithm', []):
                if self._entity_belongs_to_problem(algorithm, problem_id):
                    relationships.append(Relationship(
                        source=problem.id,
                        target=algorithm.id,
                        type='USES_ALGORITHM',
                        confidence=1.0,
                        source_file=problem.source_file
                    ))
            
            # 问题与数据结构
            for ds in entities_by_type.get('DataStructure', []):
                if self._entity_belongs_to_problem(ds, problem_id):
                    relationships.append(Relationship(
                        source=problem.id,
                        target=ds.id,
                        type='REQUIRES_DATA_STRUCTURE',
                        confidence=1.0,
                        source_file=problem.source_file
                    ))
            
            # 问题与技术
            for technique in entities_by_type.get('Technique', []):
                if self._entity_belongs_to_problem(technique, problem_id):
                    relationships.append(Relationship(
                        source=problem.id,
                        target=technique.id,
                        type='APPLIES_TECHNIQUE',
                        confidence=1.0,
                        source_file=problem.source_file
                    ))
            
            # 问题与解决方案
            for solution in entities_by_type.get('Solution', []):
                if self._entity_belongs_to_problem(solution, problem_id):
                    relationships.append(Relationship(
                        source=problem.id,
                        target=solution.id,
                        type='HAS_SOLUTION',
                        confidence=1.0,
                        source_file=problem.source_file
                    ))
            
            # 问题与复杂度
            for complexity in entities_by_type.get('Complexity', []):
                if self._entity_belongs_to_problem(complexity, problem_id):
                    if complexity.properties.get('type') == 'time':
                        relationships.append(Relationship(
                            source=problem.id,
                            target=complexity.id,
                            type='HAS_TIME_COMPLEXITY',
                            confidence=1.0,
                            source_file=problem.source_file
                        ))
                    elif complexity.properties.get('type') == 'space':
                        relationships.append(Relationship(
                            source=problem.id,
                            target=complexity.id,
                            type='HAS_SPACE_COMPLEXITY',
                            confidence=1.0,
                            source_file=problem.source_file
                        ))
            
            # 问题与洞察
            for insight in entities_by_type.get('Insight', []):
                if self._entity_belongs_to_problem(insight, problem_id):
                    relationships.append(Relationship(
                        source=problem.id,
                        target=insight.id,
                        type='PROVIDES_INSIGHT',
                        confidence=1.0,
                        source_file=problem.source_file
                    ))
            
            # 问题与难度
            for difficulty in entities_by_type.get('Difficulty', []):
                difficulty_val = (problem.properties.get('difficulty') or '').strip()
                if difficulty.name and difficulty_val == difficulty.name:
                    relationships.append(Relationship(
                        source=problem.id,
                        target=difficulty.id,
                        type='HAS_DIFFICULTY',
                        confidence=1.0,
                        source_file=problem.source_file
                    ))
        
        # 解决方案与编程语言
        for solution in entities_by_type.get('Solution', []):
            for language in entities_by_type.get('Language', []):
                if solution.properties.get('language') == language.name:
                    relationships.append(Relationship(
                        source=solution.id,
                        target=language.id,
                        type='IMPLEMENTED_IN',
                        confidence=1.0,
                        source_file=solution.source_file
                    ))
        
        return relationships
    
    def _extract_category_relationships(self, entities_by_type: Dict, categories: Dict) -> List[Relationship]:
        """提取分类关系"""
        relationships = []
        
        # 问题与分类
        for problem in entities_by_type.get('Problem', []):
            category_name = problem.properties.get('category')
            if category_name:
                category_id = f"category_{self._normalize_name(category_name)}"
                relationships.append(Relationship(
                    source=problem.id,
                    target=category_id,
                    type='BELONGS_TO_CATEGORY',
                    confidence=1.0,
                    source_file=problem.source_file
                ))
        
        return relationships
    
    def _extract_similarity_relationships(self, entities_by_type: Dict) -> List[Relationship]:
        """提取相似性关系"""
        relationships = []
        problems = entities_by_type.get('Problem', [])
        
        # 基于算法标签的相似性
        for i, problem1 in enumerate(problems):
            for problem2 in problems[i+1:]:
                similarity = self._calculate_problem_similarity(problem1, problem2, entities_by_type)
                if similarity >= self.similarity_threshold:
                    relationships.append(Relationship(
                        source=problem1.id,
                        target=problem2.id,
                        type='SIMILAR_TO',
                        confidence=similarity,
                        properties={'similarity_score': similarity}
                    ))
        
        return relationships
    
    def _extract_statistical_relationships(self, entities_by_type: Dict) -> List[Relationship]:
        """提取统计关系"""
        relationships = []
        
        # 模式与算法的关系
        patterns = entities_by_type.get('Pattern', [])
        algorithms = entities_by_type.get('Algorithm', [])
        
        for pattern in patterns:
            related_algorithms = pattern.properties.get('related_algorithms', [])
            for algorithm in algorithms:
                if algorithm.name in related_algorithms:
                    relationships.append(Relationship(
                        source=pattern.id,
                        target=algorithm.id,
                        type='PATTERN_USES_ALGORITHM',
                        confidence=0.9
                    ))
        
        return relationships
    
    def _extract_cooccurrence_relationships(self, entities_by_type: Dict) -> List[Relationship]:
        """提取共现关系"""
        relationships = []
        
        # 分析算法、数据结构、技术的共现关系
        problems = entities_by_type.get('Problem', [])
        
        cooccurrence_count = defaultdict(int)
        total_problems = len(problems)
        
        # 统计共现次数
        for problem in problems:
            problem_id = problem.properties.get('problem_id', problem.id.replace('problem_', ''))
            
            # 获取该问题相关的算法、数据结构、技术
            related_entities = []
            
            for entity_type in ['Algorithm', 'DataStructure', 'Technique']:
                for entity in entities_by_type.get(entity_type, []):
                    if self._entity_belongs_to_problem(entity, problem_id):
                        related_entities.append(entity)
            
            # 计算两两共现
            for i, entity1 in enumerate(related_entities):
                for entity2 in related_entities[i+1:]:
                    pair = tuple(sorted([entity1.id, entity2.id]))
                    cooccurrence_count[pair] += 1
        
        # 创建共现关系（只保留高频共现）
        min_cooccurrence = max(2, total_problems * 0.1)  # 至少2次或10%的问题中共现
        
        for (entity1_id, entity2_id), count in cooccurrence_count.items():
            if entity1_id == entity2_id:
                continue  # 跳过自指
            if count >= min_cooccurrence:
                confidence = min(1.0, count / (total_problems * 0.5))
                relationships.append(Relationship(
                    source=entity1_id,
                    target=entity2_id,
                    type='CO_OCCURS_WITH',
                    confidence=confidence,
                    properties={
                        'cooccurrence_count': count,
                        'cooccurrence_ratio': count / total_problems
                    }
                ))
        
        return relationships
    
    def _entity_belongs_to_problem(self, entity: Entity, problem_id: str) -> bool:
        """判断实体是否属于特定问题"""
        entity_problem_id = entity.properties.get('problem_id', '')
        return entity_problem_id == problem_id or entity_problem_id in entity.source_file
    
    def _calculate_problem_similarity(self, problem1: Entity, problem2: Entity, entities_by_type: Dict) -> float:
        """计算问题相似度"""
        # 基于共同的算法、数据结构、技术计算相似度
        p1_id = problem1.properties.get('problem_id', problem1.id.replace('problem_', ''))
        p2_id = problem2.properties.get('problem_id', problem2.id.replace('problem_', ''))
        
        p1_components = set()
        p2_components = set()
        
        # 收集问题1的组件
        for entity_type in ['Algorithm', 'DataStructure', 'Technique']:
            for entity in entities_by_type.get(entity_type, []):
                if self._entity_belongs_to_problem(entity, p1_id):
                    p1_components.add(entity.name)
                if self._entity_belongs_to_problem(entity, p2_id):
                    p2_components.add(entity.name)
        
        # 计算Jaccard相似度
        if not p1_components and not p2_components:
            return 0.0
        
        intersection = len(p1_components.intersection(p2_components))
        union = len(p1_components.union(p2_components))
        
        return intersection / union if union > 0 else 0.0
    
    def _normalize_name(self, name: str) -> str:
        """标准化名称用于ID"""
        return re.sub(r'[^\w\u4e00-\u9fff]', '_', str(name).lower())

class BatchKnowledgeGraphBuilder:
    """批量知识图谱构建器"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.entity_extractor = BatchEntityExtractor()
        self.relationship_extractor = BatchRelationshipExtractor()
        self.graph_db = ExtendedNeo4jKnowledgeGraph(neo4j_uri, neo4j_user, neo4j_password)
        self.processed_files = set()
    
    def build_from_directory(self, root_directory: str, file_pattern: str = "*.json", 
                           batch_size: int = 50, max_workers: int = 4) -> Dict:
        """从目录批量构建知识图谱"""
        logger.info(f"开始从目录构建知识图谱: {root_directory}")
        
        # 1. 扫描文件
        json_files = list(Path(root_directory).rglob(file_pattern))
        logger.info(f"发现 {len(json_files)} 个JSON文件")

        # 打印找到的文件路径，便于调试
        for file_path in json_files:
            logger.info(f"找到文件: {file_path}")
        
        if not json_files:
            raise ValueError(f"在目录 {root_directory} 中没有找到匹配的JSON文件")
        
        # 2. 批量处理文件
        all_entities = []
        all_relationships = []
        categories = {}
        
        # 创建数据库模式
        self.graph_db.create_schema()
        
        # 分批处理文件
        for i in range(0, len(json_files), batch_size):
            batch_files = json_files[i:i+batch_size]
            logger.info(f"处理批次 {i//batch_size + 1}/{(len(json_files)-1)//batch_size + 1}")
            
            # 并行读取文件
            problem_data_list = self._load_files_parallel(batch_files, max_workers)
            
            if problem_data_list:
                # 提取实体和关系
                batch_entities, batch_categories = self.entity_extractor.extract_entities_batch(problem_data_list)
                batch_relationships = self.relationship_extractor.extract_relationships_batch(batch_entities, batch_categories)
                
                # 累积结果
                all_entities.extend(batch_entities)
                all_relationships.extend(batch_relationships)
                categories.update(batch_categories)
                
                # 存储到数据库
                self._store_batch(batch_entities, batch_relationships)
        
        # 3. 后处理：添加全局关系
        global_relationships = self._extract_global_relationships(all_entities)
        all_relationships.extend(global_relationships)
        self.graph_db.store_relationships(global_relationships)
        
        logger.info("知识图谱构建完成")
        
        return {
            'total_entities': len(all_entities),
            'total_relationships': len(all_relationships),
            'categories': categories,
            'processed_files': len(json_files),
            'statistics': self._generate_statistics(all_entities, all_relationships)
        }
    
    def add_single_problem(self, json_file_path: str) -> Dict:
        """添加单个题目到现有知识图谱"""
        logger.info(f"添加单个题目: {json_file_path}")
        
        if json_file_path in self.processed_files:
            logger.warning(f"文件已处理过: {json_file_path}")
            return {'status': 'already_processed'}
        
        try:
            # 读取文件
            with open(json_file_path, 'r', encoding='utf-8') as f:
                problem_data = json.load(f)
            
            # 提取实体和关系
            problem_data_list = [(problem_data, json_file_path)]
            entities, categories = self.entity_extractor.extract_entities_batch(problem_data_list)
            relationships = self.relationship_extractor.extract_relationships_batch(entities, categories)
            
            # 查找与现有问题的关系
            existing_relationships = self._find_relationships_with_existing(entities)
            relationships.extend(existing_relationships)
            
            # 存储到数据库
            self._store_batch(entities, relationships)
            
            # 标记为已处理
            self.processed_files.add(json_file_path)
            
            logger.info(f"成功添加题目: {problem_data.get('title', 'Unknown')}")
            
            return {
                'status': 'success',
                'entities_added': len(entities),
                'relationships_added': len(relationships),
                'problem_title': problem_data.get('title', 'Unknown')
            }
            
        except Exception as e:
            logger.error(f"添加题目失败: {json_file_path}, 错误: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _load_files_parallel(self, json_files: List[Path], max_workers: int) -> List[Tuple[Dict, str]]:
        """并行加载JSON文件"""
        problem_data_list = []
        
        def load_single_file(file_path: Path) -> Optional[Tuple[Dict, str]]:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return (data, str(file_path))
            except Exception as e:
                logger.error(f"加载文件失败: {file_path}, 错误: {e}")
                return None
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(load_single_file, file_path): file_path 
                             for file_path in json_files}
            
            for future in as_completed(future_to_file):
                result = future.result()
                if result:
                    problem_data_list.append(result)
        
        return problem_data_list
    
    def _store_batch(self, entities: List[Entity], relationships: List[Relationship]):
        """批量存储实体和关系"""
        logger.info(f"存储批次数据: {len(entities)} 个实体, {len(relationships)} 个关系")
        
        # 去重
        unique_entities = self._deduplicate_entities(entities)
        unique_relationships = self._deduplicate_relationships(relationships)
        
        # 存储
        self.graph_db.store_entities(unique_entities)
        self.graph_db.store_relationships(unique_relationships)
    
    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """实体去重"""
        seen = set()
        unique_entities = []
        
        for entity in entities:
            if entity.id not in seen:
                seen.add(entity.id)
                unique_entities.append(entity)
        
        return unique_entities
    
    def _deduplicate_relationships(self, relationships: List[Relationship]) -> List[Relationship]:
        """关系去重"""
        seen = set()
        unique_relationships = []
        
        for rel in relationships:
            key = (rel.source, rel.target, rel.type)
            if key not in seen:
                seen.add(key)
                unique_relationships.append(rel)
        
        return unique_relationships
    
    def _extract_global_relationships(self, all_entities: List[Entity]) -> List[Relationship]:
        """提取全局关系（跨题目的关系）"""
        relationships = []
        
        # 基于难度的前置关系
        problems_by_difficulty = defaultdict(list)
        for entity in all_entities:
            if entity.type == 'Problem':
                difficulty = entity.properties.get('difficulty', '')
                if difficulty:
                    problems_by_difficulty[difficulty].append(entity)
        
        # 简单题目可能是中等题目的前置
        simple_problems = problems_by_difficulty.get('简单', [])
        medium_problems = problems_by_difficulty.get('中等', [])
        
        for simple in simple_problems[:5]:  # 限制数量避免过多关系
            for medium in medium_problems[:5]:
                if self._is_prerequisite(simple, medium, all_entities):
                    relationships.append(Relationship(
                        source=simple.id,
                        target=medium.id,
                        type='PREREQUISITE_OF',
                        confidence=0.6
                    ))
        
        return relationships
    
    def _find_relationships_with_existing(self, new_entities: List[Entity]) -> List[Relationship]:
        """查找新实体与现有实体的关系"""
        relationships = []
        
        # 查询现有相似问题
        for entity in new_entities:
            if entity.type == 'Problem':
                similar_problems = self.graph_db.find_similar_problems(entity.id)
                for similar in similar_problems:
                    if similar['similarity_score'] >= 0.7:
                        relationships.append(Relationship(
                            source=entity.id,
                            target=similar['p2'].id,
                            type='SIMILAR_TO',
                            confidence=similar['similarity_score']
                        ))
        
        return relationships
    
    def _is_prerequisite(self, simple_problem: Entity, medium_problem: Entity, all_entities: List[Entity]) -> bool:
        """判断是否为前置关系"""
        # 简单的启发式规则
        simple_algorithms = set()
        medium_algorithms = set()
        
        simple_id = simple_problem.properties.get('problem_id', simple_problem.id.replace('problem_', ''))
        medium_id = medium_problem.properties.get('problem_id', medium_problem.id.replace('problem_', ''))
        
        for entity in all_entities:
            if entity.type == 'Algorithm':
                if entity.properties.get('problem_id') == simple_id:
                    simple_algorithms.add(entity.name)
                elif entity.properties.get('problem_id') == medium_id:
                    medium_algorithms.add(entity.name)
        
        # 如果简单问题的算法是中等问题算法的子集，可能是前置
        return simple_algorithms and simple_algorithms.issubset(medium_algorithms)
    
    def _generate_statistics(self, entities: List[Entity], relationships: List[Relationship]) -> Dict:
        """生成统计信息"""
        stats = {
            'entity_counts': Counter(e.type for e in entities),
            'relationship_counts': Counter(r.type for r in relationships),
            'top_algorithms': Counter(e.name for e in entities if e.type == 'Algorithm').most_common(10),
            'top_data_structures': Counter(e.name for e in entities if e.type == 'DataStructure').most_common(10),
            'difficulty_distribution': Counter(e.properties.get('difficulty', '未知') 
                                             for e in entities if e.type == 'Problem'),
            'category_distribution': Counter(e.properties.get('category', '未分类') 
                                           for e in entities if e.type == 'Problem')
        }
        return stats
    
    def close(self):
        """关闭连接"""
        self.graph_db.close()

class ExtendedNeo4jKnowledgeGraph:
    """扩展的Neo4j知识图谱存储"""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.ontology = ExtendedLeetCodeOntology()
    
    def close(self):
        self.driver.close()
    
    def create_schema(self):
        """创建图谱模式"""
        with self.driver.session() as session:
            # 创建约束和索引
            constraints = [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Problem) REQUIRE p.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Algorithm) REQUIRE a.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (d:DataStructure) REQUIRE d.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Technique) REQUIRE t.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Solution) REQUIRE s.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Complexity) REQUIRE c.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (l:Language) REQUIRE l.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Insight) REQUIRE i.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (cat:Category) REQUIRE cat.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (pat:Pattern) REQUIRE pat.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (dif:Difficulty) REQUIRE dif.id IS UNIQUE"
            ]
            
            # 创建索引
            indexes = [
                "CREATE INDEX IF NOT EXISTS FOR (p:Problem) ON p.title",
                "CREATE INDEX IF NOT EXISTS FOR (p:Problem) ON p.difficulty",
                "CREATE INDEX IF NOT EXISTS FOR (p:Problem) ON p.category",
                "CREATE INDEX IF NOT EXISTS FOR (a:Algorithm) ON a.name",
                "CREATE INDEX IF NOT EXISTS FOR (d:DataStructure) ON d.name",
                "CREATE INDEX IF NOT EXISTS FOR (c:Category) ON c.name"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"创建约束: {constraint}")
                except Exception as e:
                    logger.warning(f"约束已存在或创建失败: {e}")
            
            for index in indexes:
                try:
                    session.run(index)
                    logger.info(f"创建索引: {index}")
                except Exception as e:
                    logger.warning(f"索引已存在或创建失败: {e}")
    
    def store_entities(self, entities: List[Entity]):
        """批量存储实体"""
        with self.driver.session() as session:
            # 按类型分组批量插入
            entities_by_type = defaultdict(list)
            for entity in entities:
                entities_by_type[entity.type].append(entity)
            
            for entity_type, type_entities in entities_by_type.items():
                self._batch_insert_entities(session, entity_type, type_entities)
    
    def _batch_insert_entities(self, session, entity_type: str, entities: List[Entity]):
        """批量插入同类型实体"""
        if not entities:
            return
        
        # 构建批量插入查询
        cypher = f"""
        UNWIND $entities AS entity
        MERGE (n:{entity_type} {{id: entity.id}})
        SET n.name = entity.name,
            n.created_at = entity.created_at
        """
        
        # 添加属性设置
        if entities:
            sample_entity = entities[0]
            for key in sample_entity.properties.keys():
                cypher += f", n.{key} = entity.properties.{key}"
        
        # 准备数据
        entity_data = []
        for entity in entities:
            entity_data.append({
                'id': entity.id,
                'name': entity.name,
                'created_at': entity.created_at,
                'properties': entity.properties
            })
        
        try:
            session.run(cypher, entities=entity_data)
            logger.info(f"批量插入 {len(entities)} 个 {entity_type} 实体")
        except Exception as e:
            logger.error(f"批量插入 {entity_type} 实体失败: {e}")
    
    def store_relationships(self, relationships: List[Relationship]):
        """批量存储关系"""
        with self.driver.session() as session:
            # 按类型分组批量插入
            relationships_by_type = defaultdict(list)
            for rel in relationships:
                relationships_by_type[rel.type].append(rel)
            
            for rel_type, type_relationships in relationships_by_type.items():
                self._batch_insert_relationships(session, rel_type, type_relationships)
    
    def _batch_insert_relationships(self, session, rel_type: str, relationships: List[Relationship]):
        """批量插入同类型关系"""
        if not relationships:
            return
        
        cypher = f"""
        UNWIND $relationships AS rel
        MATCH (a {{id: rel.source}})
        MATCH (b {{id: rel.target}})
        MERGE (a)-[r:{rel_type}]->(b)
        SET r.confidence = rel.confidence
        """
        
        # 添加关系属性
        if relationships and relationships[0].properties:
            sample_rel = relationships[0]
            for key in sample_rel.properties.keys():
                cypher += f", r.{key} = rel.properties.{key}"
        
        # 准备数据
        rel_data = []
        for rel in relationships:
            rel_data.append({
                'source': rel.source,
                'target': rel.target,
                'confidence': rel.confidence,
                'properties': rel.properties
            })
        
        try:
            session.run(cypher, relationships=rel_data)
            logger.info(f"批量插入 {len(relationships)} 个 {rel_type} 关系")
        except Exception as e:
            logger.error(f"批量插入 {rel_type} 关系失败: {e}")
    
    def find_similar_problems(self, problem_id: str, limit: int = 10) -> List[Dict]:
        """查找相似问题"""
        with self.driver.session() as session:
            cypher = """
            MATCH (p1:Problem {id: $problem_id})
            MATCH (p1)-[:USES_ALGORITHM]->(a:Algorithm)<-[:USES_ALGORITHM]-(p2:Problem)
            WHERE p1 <> p2
            WITH p2, count(DISTINCT a) as common_algorithms
            OPTIONAL MATCH (p1)-[:REQUIRES_DATA_STRUCTURE]->(d:DataStructure)<-[:REQUIRES_DATA_STRUCTURE]-(p2)
            WITH p2, common_algorithms, count(DISTINCT d) as common_ds
            OPTIONAL MATCH (p1)-[:APPLIES_TECHNIQUE]->(t:Technique)<-[:APPLIES_TECHNIQUE]-(p2)
            WITH p2, common_algorithms, common_ds, count(DISTINCT t) as common_techniques
            RETURN p2, (common_algorithms * 0.5 + common_ds * 0.3 + common_techniques * 0.2) as similarity_score
            ORDER BY similarity_score DESC
            LIMIT $limit
            """
            
            result = session.run(cypher, problem_id=problem_id, limit=limit)
            return [{'p2': record['p2'], 'similarity_score': record['similarity_score']} 
                   for record in result]
    
    def get_problem_statistics(self) -> Dict:
        """获取问题统计信息"""
        with self.driver.session() as session:
            queries = {
                'total_problems': "MATCH (p:Problem) RETURN count(p) as count",
                'difficulty_distribution': """
                    MATCH (p:Problem) 
                    RETURN p.difficulty as difficulty, count(p) as count 
                    ORDER BY count DESC
                """,
                'category_distribution': """
                    MATCH (p:Problem) 
                    RETURN p.category as category, count(p) as count 
                    ORDER BY count DESC
                """,
                'top_algorithms': """
                    MATCH (a:Algorithm)<-[:USES_ALGORITHM]-(p:Problem) 
                    RETURN a.name as algorithm, count(p) as usage_count 
                    ORDER BY usage_count DESC LIMIT 10
                """,
                'algorithm_complexity': """
                    MATCH (p:Problem)-[:USES_ALGORITHM]->(a:Algorithm)
                    MATCH (p)-[:HAS_TIME_COMPLEXITY]->(tc:Complexity)
                    RETURN a.name as algorithm, tc.notation as time_complexity, count(p) as count
                    ORDER BY count DESC
                """
            }
            
            stats = {}
            for key, query in queries.items():
                try:
                    result = session.run(query)
                    if key in ['total_problems']:
                        stats[key] = result.single()['count']
                    else:
                        stats[key] = [dict(record) for record in result]
                except Exception as e:
                    logger.error(f"统计查询失败 {key}: {e}")
                    stats[key] = []
            
            return stats

# ===== 使用示例和工具函数 =====

def main():
    """主函数示例"""
    
    # Neo4j连接配置
    NEO4J_URI = "bolt://1.117.77.19:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "Abcd1234!"  # 请替换为实际密码
    
    # 题目文件根目录
    ROOT_DIRECTORY = r"/www/wwwroot/algokg_platform/data/raw/problem_extration"
    
    # 创建知识图谱构建器
    builder = BatchKnowledgeGraphBuilder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        # 批量构建知识图谱
        logger.info("开始批量构建知识图谱...")
        result = builder.build_from_directory(
            root_directory=ROOT_DIRECTORY,
            file_pattern="*.json",
            batch_size=20,  # 每批处理20个文件
            max_workers=4   # 4个并发工作线程
        )
        
        # 输出结果
        print("\n=== 知识图谱构建完成 ===")
        print(f"总实体数: {result['total_entities']}")
        print(f"总关系数: {result['total_relationships']}")
        print(f"处理文件数: {result['processed_files']}")
        print(f"发现分类数: {len(result['categories'])}")
        
        print("\n=== 分类统计 ===")
        for category, info in result['categories'].items():
            print(f"{category}: {info.problem_count} 个题目")
        
        print("\n=== 实体统计 ===")
        for entity_type, count in result['statistics']['entity_counts'].items():
            print(f"{entity_type}: {count}")
        
        print("\n=== 热门算法 ===")
        for algorithm, count in result['statistics']['top_algorithms']:
            print(f"{algorithm}: {count} 个题目")
        
        # 查询示例
        print("\n=== 查询示例 ===")
        stats = builder.graph_db.get_problem_statistics()
        print(f"数据库中总题目数: {stats.get('total_problems', 0)}")
        
        if stats.get('top_algorithms'):
            print("最常用算法:")
            for algo in stats['top_algorithms'][:5]:
                print(f"  {algo['algorithm']}: {algo['usage_count']} 次使用")
        
    except Exception as e:
        logger.error(f"构建知识图谱时发生错误: {e}")
        raise
    finally:
        builder.close()

def add_new_problem_example():
    """添加新题目的示例"""
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "your_password"
    
    builder = BatchKnowledgeGraphBuilder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        # 添加单个新题目
        new_problem_path = r"F:\My_project\problem_extraction\动态规划\爬楼梯.json"
        result = builder.add_single_problem(new_problem_path)
        
        if result['status'] == 'success':
            print(f"成功添加题目: {result['problem_title']}")
            print(f"添加实体数: {result['entities_added']}")
            print(f"添加关系数: {result['relationships_added']}")
        else:
            print(f"添加失败: {result}")
            
    finally:
        builder.close()

def query_examples():
    """查询示例"""
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "your_password"
    
    graph_db = ExtendedNeo4jKnowledgeGraph(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        with graph_db.driver.session() as session:
            # 1. 查询所有使用哈希算法的题目
            print("=== 使用哈希算法的题目 ===")
            result = session.run("""
                MATCH (p:Problem)-[:USES_ALGORITHM]->(a:Algorithm {name: '哈希'})
                RETURN p.title as title, p.difficulty as difficulty, p.category as category
                ORDER BY p.difficulty, p.title
            """)
            for record in result:
                print(f"{record['title']} ({record['difficulty']}) - {record['category']}")
            
            # 2. 查询每个分类的题目数量
            print("\n=== 分类题目统计 ===")
            result = session.run("""
                MATCH (p:Problem)-[:BELONGS_TO_CATEGORY]->(c:Category)
                RETURN c.name as category, count(p) as problem_count
                ORDER BY problem_count DESC
            """)
            for record in result:
                print(f"{record['category']}: {record['problem_count']} 个题目")
            
            # 3. 查询算法与数据结构的共现关系
            print("\n=== 算法与数据结构共现 ===")
            result = session.run("""
                MATCH (p:Problem)-[:USES_ALGORITHM]->(a:Algorithm)
                MATCH (p)-[:REQUIRES_DATA_STRUCTURE]->(d:DataStructure)
                RETURN a.name as algorithm, d.name as data_structure, count(p) as cooccurrence
                ORDER BY cooccurrence DESC
                LIMIT 10
            """)
            for record in result:
                print(f"{record['algorithm']} + {record['data_structure']}: {record['cooccurrence']} 次")
            
            # 4. 查询难度递进路径
            print("\n=== 难度递进推荐 ===")
            result = session.run("""
                MATCH (easy:Problem {difficulty: '简单'})-[:USES_ALGORITHM]->(a:Algorithm)
                MATCH (medium:Problem {difficulty: '中等'})-[:USES_ALGORITHM]->(a)
                WHERE easy <> medium
                RETURN easy.title as easy_problem, medium.title as medium_problem, 
                       a.name as common_algorithm
                LIMIT 5
            """)
            for record in result:
                print(f"{record['easy_problem']} → {record['medium_problem']} (通过 {record['common_algorithm']})")
            
            # 5. 查询高价值洞察（出现在多个题目中的洞察）
            print("\n=== 高价值洞察 ===")
            result = session.run("""
                MATCH (i:Insight)
                WHERE i.content CONTAINS '哈希' OR i.content CONTAINS '复杂度' OR i.content CONTAINS '优化'
                RETURN i.content as insight, i.category as category
                LIMIT 5
            """)
            for record in result:
                print(f"[{record['category']}] {record['insight']}")
    
    finally:
        graph_db.close()

class KnowledgeGraphAPI:
    """知识图谱API接口"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.graph_db = ExtendedNeo4jKnowledgeGraph(neo4j_uri, neo4j_user, neo4j_password)
    
    def get_learning_path(self, start_algorithm: str, target_difficulty: str = "中等") -> List[Dict]:
        """获取学习路径"""
        with self.graph_db.driver.session() as session:
            cypher = """
            MATCH (start_algo:Algorithm {name: $start_algorithm})
            MATCH (start_prob:Problem)-[:USES_ALGORITHM]->(start_algo)
            WHERE start_prob.difficulty = '简单'
            
            MATCH (target_prob:Problem)-[:USES_ALGORITHM]->(start_algo)
            WHERE target_prob.difficulty = $target_difficulty
            
            MATCH path = shortestPath((start_prob)-[:SIMILAR_TO|PREREQUISITE_OF*1..3]-(target_prob))
            RETURN nodes(path) as learning_path
            LIMIT 5
            """
            
            result = session.run(cypher, start_algorithm=start_algorithm, target_difficulty=target_difficulty)
            paths = []
            for record in result:
                path_nodes = []
                for node in record['learning_path']:
                    if 'Problem' in list(node.labels):
                        path_nodes.append({
                            'title': node['title'],
                            'difficulty': node['difficulty'],
                            'category': node['category']
                        })
                paths.append(path_nodes)
            return paths
    
    def recommend_problems(self, solved_problems: List[str], limit: int = 5) -> List[Dict]:
        """基于已解决题目推荐新题目"""
        with self.graph_db.driver.session() as session:
            cypher = """
            MATCH (solved:Problem)
            WHERE solved.title IN $solved_problems
            
            MATCH (solved)-[:USES_ALGORITHM]->(algo:Algorithm)<-[:USES_ALGORITHM]-(recommended:Problem)
            WHERE NOT recommended.title IN $solved_problems
            
            WITH recommended, count(DISTINCT algo) as common_algorithms
            
            MATCH (solved)-[:REQUIRES_DATA_STRUCTURE]->(ds:DataStructure)<-[:REQUIRES_DATA_STRUCTURE]-(recommended)
            WHERE NOT recommended.title IN $solved_problems
            
            WITH recommended, common_algorithms, count(DISTINCT ds) as common_ds
            
            RETURN recommended.title as title, 
                   recommended.difficulty as difficulty,
                   recommended.category as category,
                   (common_algorithms + common_ds) as relevance_score
            ORDER BY relevance_score DESC
            LIMIT $limit
            """
            
            result = session.run(cypher, solved_problems=solved_problems, limit=limit)
            return [dict(record) for record in result]
    
    def get_algorithm_mastery_map(self, user_solved_problems: List[str]) -> Dict:
        """获取算法掌握图谱"""
        with self.graph_db.driver.session() as session:
            cypher = """
            MATCH (algo:Algorithm)
            OPTIONAL MATCH (solved:Problem)-[:USES_ALGORITHM]->(algo)
            WHERE solved.title IN $solved_problems
            
            OPTIONAL MATCH (all_prob:Problem)-[:USES_ALGORITHM]->(algo)
            
            RETURN algo.name as algorithm,
                   algo.category as category,
                   count(DISTINCT solved) as solved_count,
                   count(DISTINCT all_prob) as total_count,
                   (count(DISTINCT solved) * 1.0 / count(DISTINCT all_prob)) as mastery_ratio
            ORDER BY mastery_ratio DESC, solved_count DESC
            """
            
            result = session.run(cypher, solved_problems=user_solved_problems)
            mastery_map = {}
            for record in result:
                algorithm = record['algorithm']
                mastery_map[algorithm] = {
                    'category': record['category'],
                    'solved_count': record['solved_count'],
                    'total_count': record['total_count'],
                    'mastery_ratio': record['mastery_ratio'] or 0.0,
                    'mastery_level': self._get_mastery_level(record['mastery_ratio'] or 0.0)
                }
            
            return mastery_map
    
    def _get_mastery_level(self, ratio: float) -> str:
        """根据掌握比例确定掌握等级"""
        if ratio >= 0.8:
            return "精通"
        elif ratio >= 0.6:
            return "熟练"
        elif ratio >= 0.3:
            return "入门"
        else:
            return "未掌握"
    
    def close(self):
        self.graph_db.close()

def api_usage_example():
    """API使用示例"""
    NEO4J_URI = "bolt://1.117.77.19:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "Abcd1234!"
    
    api = KnowledgeGraphAPI(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        # 1. 获取学习路径
        print("=== 哈希算法学习路径 ===")
        paths = api.get_learning_path("哈希", "中等")
        for i, path in enumerate(paths):
            print(f"路径 {i+1}:")
            for step in path:
                print(f"  {step['title']} ({step['difficulty']}) - {step['category']}")
        
        # 2. 推荐题目
        print("\n=== 题目推荐 ===")
        solved = ["两数之和", "有效的字母异位词"]
        recommendations = api.recommend_problems(solved, limit=5)
        for rec in recommendations:
            print(f"{rec['title']} ({rec['difficulty']}) - 相关度: {rec['relevance_score']}")
        
        # 3. 算法掌握图谱
        print("\n=== 算法掌握情况 ===")
        mastery = api.get_algorithm_mastery_map(solved)
        for algorithm, info in mastery.items():
            if info['total_count'] > 0:
                print(f"{algorithm}: {info['mastery_level']} "
                      f"({info['solved_count']}/{info['total_count']}, "
                      f"{info['mastery_ratio']:.1%})")
    
    finally:
        api.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "build":
            main()
        elif command == "add":
            add_new_problem_example()
        elif command == "query":
            query_examples()
        elif command == "api":
            api_usage_example()
        else:
            print("可用命令: build, add, query, api")
    else:
        # 默认执行构建
        main()