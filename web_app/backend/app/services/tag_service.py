"""
标签处理服务 - 统一处理和格式化各种类型的标签数据
"""

import re
import logging
from typing import List, Dict, Any, Union, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TagInfo:
    """标准化的标签信息"""
    name: str
    type: str  # algorithm, data_structure, technique, difficulty, platform, category
    category: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None

class TagService:
    """标签处理服务"""
    
    # 标签类型映射
    TAG_TYPE_MAPPING = {
        'algorithm': {
            'color': 'blue',
            'icon': '🔧',
            'category': '算法'
        },
        'data_structure': {
            'color': 'green', 
            'icon': '📊',
            'category': '数据结构'
        },
        'technique': {
            'color': 'purple',
            'icon': '💡',
            'category': '技巧'
        },
        'difficulty': {
            'color': 'orange',
            'icon': '⭐',
            'category': '难度'
        },
        'platform': {
            'color': 'cyan',
            'icon': '🌐',
            'category': '平台'
        },
        'category': {
            'color': 'magenta',
            'icon': '📂',
            'category': '分类'
        },
        'relationship': {
            'color': 'gold',
            'icon': '🔗',
            'category': '关系'
        }
    }
    
    # 难度映射
    DIFFICULTY_MAPPING = {
        '简单': {'color': 'green', 'icon': '🟢'},
        '中等': {'color': 'orange', 'icon': '🟡'},
        '困难': {'color': 'red', 'icon': '🔴'},
        'Easy': {'color': 'green', 'icon': '🟢'},
        'Medium': {'color': 'orange', 'icon': '🟡'},
        'Hard': {'color': 'red', 'icon': '🔴'}
    }
    
    def __init__(self):
        self.logger = logger
    
    def clean_and_standardize_tags(self, raw_tags: List[Any]) -> List[TagInfo]:
        """
        清理和标准化标签数据
        
        Args:
            raw_tags: 原始标签数据，可能包含字符串、Neo4j节点、字典等
            
        Returns:
            标准化的TagInfo列表
        """
        if not raw_tags:
            return []
        
        standardized_tags = []
        
        for raw_tag in raw_tags:
            try:
                tag_info = self._process_single_tag(raw_tag)
                if tag_info:
                    standardized_tags.append(tag_info)
            except Exception as e:
                self.logger.warning(f"处理标签失败: {raw_tag}, 错误: {e}")
                continue
        
        # 去重和排序
        return self._deduplicate_and_sort_tags(standardized_tags)
    
    def _process_single_tag(self, raw_tag: Any) -> Optional[TagInfo]:
        """处理单个标签"""
        if isinstance(raw_tag, str):
            return self._process_string_tag(raw_tag)
        elif isinstance(raw_tag, dict):
            return self._process_dict_tag(raw_tag)
        else:
            # 尝试转换为字符串处理
            tag_str = str(raw_tag)
            if self._is_neo4j_node(tag_str):
                return self._process_neo4j_node(tag_str)
            else:
                return self._process_string_tag(tag_str)
    
    def _process_string_tag(self, tag_str: str) -> Optional[TagInfo]:
        """处理字符串标签"""
        if not tag_str or tag_str.strip() == "":
            return None
        
        tag_str = tag_str.strip()
        
        # 检查是否是Neo4j节点字符串
        if self._is_neo4j_node(tag_str):
            return self._process_neo4j_node(tag_str)
        
        # 根据内容推断标签类型
        tag_type = self._infer_tag_type(tag_str)
        
        return TagInfo(
            name=tag_str,
            type=tag_type,
            category=self.TAG_TYPE_MAPPING.get(tag_type, {}).get('category'),
            color=self.TAG_TYPE_MAPPING.get(tag_type, {}).get('color', 'default'),
            icon=self.TAG_TYPE_MAPPING.get(tag_type, {}).get('icon')
        )
    
    def _process_dict_tag(self, tag_dict: Dict[str, Any]) -> Optional[TagInfo]:
        """处理字典格式的标签"""
        name = tag_dict.get('name') or tag_dict.get('title') or str(tag_dict)
        tag_type = tag_dict.get('type', 'category')
        category = tag_dict.get('category')
        description = tag_dict.get('description')
        
        return TagInfo(
            name=name,
            type=tag_type,
            category=category,
            description=description,
            color=self.TAG_TYPE_MAPPING.get(tag_type, {}).get('color', 'default'),
            icon=self.TAG_TYPE_MAPPING.get(tag_type, {}).get('icon')
        )
    
    def _process_neo4j_node(self, node_str: str) -> Optional[TagInfo]:
        """处理Neo4j节点字符串"""
        try:
            # 提取属性
            properties_match = re.search(r"properties=\{([^}]+)\}", node_str)
            if not properties_match:
                return None
            
            properties_str = properties_match.group(1)
            
            # 解析关键属性
            name_match = re.search(r"'name':\s*'([^']+)'", properties_str)
            title_match = re.search(r"'title':\s*'([^']+)'", properties_str)
            desc_match = re.search(r"'description':\s*'([^']+)'", properties_str)
            category_match = re.search(r"'category':\s*'([^']+)'", properties_str)
            
            # 提取标签类型
            labels_match = re.search(r"labels=frozenset\(\{'([^']+)'\}\)", node_str)
            node_type = labels_match.group(1).lower() if labels_match else 'unknown'
            
            # 获取名称
            name = (title_match.group(1) if title_match else 
                   name_match.group(1) if name_match else "未知")
            
            # 映射节点类型到标签类型
            type_mapping = {
                'algorithm': 'algorithm',
                'datastructure': 'data_structure',
                'technique': 'technique',
                'problem': 'category'
            }
            
            tag_type = type_mapping.get(node_type, 'category')
            
            return TagInfo(
                name=name,
                type=tag_type,
                category=category_match.group(1) if category_match else None,
                description=desc_match.group(1) if desc_match else None,
                color=self.TAG_TYPE_MAPPING.get(tag_type, {}).get('color', 'default'),
                icon=self.TAG_TYPE_MAPPING.get(tag_type, {}).get('icon')
            )
            
        except Exception as e:
            self.logger.error(f"解析Neo4j节点失败: {e}")
            return None
    
    def _is_neo4j_node(self, text: str) -> bool:
        """检查是否是Neo4j节点字符串"""
        return "<Node element_id=" in text and "properties=" in text
    
    def _infer_tag_type(self, tag_name: str) -> str:
        """根据标签名称推断类型"""
        tag_lower = tag_name.lower()
        
        # 算法关键词
        algorithm_keywords = [
            '动态规划', '贪心', '回溯', '分治', '双指针', '滑动窗口', 
            '二分查找', '深度优先', '广度优先', 'dfs', 'bfs', 'dp',
            '排序', '搜索', '递归', '迭代'
        ]
        
        # 数据结构关键词
        data_structure_keywords = [
            '数组', '链表', '栈', '队列', '树', '图', '哈希表', '堆',
            '二叉树', '平衡树', '字典树', 'trie', 'hash', 'heap'
        ]
        
        # 难度关键词
        difficulty_keywords = ['简单', '中等', '困难', 'easy', 'medium', 'hard']
        
        # 平台关键词
        platform_keywords = ['leetcode', '牛客', 'codeforces', 'atcoder']
        
        for keyword in algorithm_keywords:
            if keyword in tag_lower:
                return 'algorithm'
        
        for keyword in data_structure_keywords:
            if keyword in tag_lower:
                return 'data_structure'
        
        for keyword in difficulty_keywords:
            if keyword in tag_lower:
                return 'difficulty'
        
        for keyword in platform_keywords:
            if keyword in tag_lower:
                return 'platform'
        
        # 默认为分类
        return 'category'
    
    def _deduplicate_and_sort_tags(self, tags: List[TagInfo]) -> List[TagInfo]:
        """去重和排序标签"""
        # 去重（基于名称）
        seen_names = set()
        unique_tags = []
        
        for tag in tags:
            if tag.name not in seen_names:
                seen_names.add(tag.name)
                unique_tags.append(tag)
        
        # 排序（按类型和名称）
        type_priority = {
            'difficulty': 0,
            'algorithm': 1,
            'data_structure': 2,
            'technique': 3,
            'platform': 4,
            'category': 5,
            'relationship': 6
        }
        
        unique_tags.sort(key=lambda x: (type_priority.get(x.type, 999), x.name))
        
        return unique_tags
    
    def format_tags_for_display(self, tags: List[TagInfo]) -> List[Dict[str, Any]]:
        """格式化标签用于前端显示"""
        return [
            {
                'name': tag.name,
                'type': tag.type,
                'category': tag.category,
                'description': tag.description,
                'color': tag.color,
                'icon': tag.icon,
                'display_name': f"{tag.icon} {tag.name}" if tag.icon else tag.name
            }
            for tag in tags
        ]

# 全局标签服务实例
tag_service = TagService()
