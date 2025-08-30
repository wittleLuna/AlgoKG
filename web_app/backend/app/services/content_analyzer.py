"""
内容分析服务
用于分析笔记内容，提取关键信息
"""
import logging
import re
from typing import Dict, List, Any
import asyncio

logger = logging.getLogger(__name__)

class ContentAnalyzerService:
    """内容分析服务"""
    
    def __init__(self):
        # 算法关键词
        self.algorithm_keywords = [
            '动态规划', 'DP', '贪心', '分治', '回溯', 'DFS', 'BFS',
            '二分查找', '排序', '搜索', '递归', '迭代'
        ]
        
        # 数据结构关键词
        self.data_structure_keywords = [
            '数组', '链表', '栈', '队列', '树', '图', '哈希表', '堆'
        ]
        
        # 复杂度模式
        self.complexity_patterns = [
            r'O\([^)]+\)',
            r'时间复杂度[:：]\s*O\([^)]+\)',
            r'空间复杂度[:：]\s*O\([^)]+\)'
        ]
    
    async def analyze_content(self, content: str) -> Dict[str, Any]:
        """分析内容"""
        try:
            analysis = {
                'word_count': self._count_words(content),
                'algorithm_keywords': self._extract_algorithm_keywords(content),
                'complexity_mentions': self._extract_complexity_mentions(content),
                'code_blocks': self._extract_code_blocks(content),
                'difficulty_level': self._estimate_difficulty(content),
                'topics': self._extract_topics(content),
                'summary': self._generate_summary(content)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"内容分析失败: {e}")
            return {
                'word_count': 0,
                'algorithm_keywords': [],
                'complexity_mentions': [],
                'code_blocks': [],
                'difficulty_level': 'unknown',
                'topics': [],
                'summary': ''
            }
    
    def _count_words(self, content: str) -> int:
        """统计词数"""
        # 简单的词数统计
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', content))
        return chinese_chars + english_words
    
    def _extract_algorithm_keywords(self, content: str) -> List[str]:
        """提取算法关键词"""
        found_keywords = []
        content_lower = content.lower()
        
        for keyword in self.algorithm_keywords:
            if keyword.lower() in content_lower:
                found_keywords.append(keyword)
        
        for keyword in self.data_structure_keywords:
            if keyword.lower() in content_lower:
                found_keywords.append(keyword)
        
        return list(set(found_keywords))
    
    def _extract_complexity_mentions(self, content: str) -> List[str]:
        """提取复杂度提及"""
        complexities = []
        
        for pattern in self.complexity_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            complexities.extend(matches)
        
        return list(set(complexities))
    
    def _extract_code_blocks(self, content: str) -> List[Dict[str, str]]:
        """提取代码块"""
        code_blocks = []
        
        # Markdown 代码块
        markdown_pattern = r'```(\w+)?\n(.*?)\n```'
        matches = re.findall(markdown_pattern, content, re.DOTALL)
        
        for language, code in matches:
            code_blocks.append({
                'language': language or 'unknown',
                'code': code.strip(),
                'type': 'markdown'
            })
        
        # 简单的代码识别（包含常见编程关键词）
        code_indicators = ['def ', 'class ', 'function', 'int main', 'public class']
        lines = content.split('\n')
        
        current_block = []
        in_code_block = False
        
        for line in lines:
            line_stripped = line.strip()
            
            # 检查是否是代码行
            if any(indicator in line_stripped for indicator in code_indicators):
                in_code_block = True
                current_block = [line]
            elif in_code_block:
                if line_stripped == '' or line.startswith('    ') or line.startswith('\t'):
                    current_block.append(line)
                else:
                    if len(current_block) > 1:
                        code_blocks.append({
                            'language': 'unknown',
                            'code': '\n'.join(current_block),
                            'type': 'detected'
                        })
                    in_code_block = False
                    current_block = []
        
        return code_blocks
    
    def _estimate_difficulty(self, content: str) -> str:
        """估算难度级别"""
        content_lower = content.lower()
        
        # 简单的难度估算
        advanced_keywords = [
            '动态规划', '回溯', '图算法', '复杂度分析', '优化',
            'dp', 'dfs', 'bfs', '递归', '分治'
        ]
        
        basic_keywords = [
            '数组', '字符串', '循环', '条件', '基础'
        ]
        
        advanced_count = sum(1 for keyword in advanced_keywords if keyword in content_lower)
        basic_count = sum(1 for keyword in basic_keywords if keyword in content_lower)
        
        if advanced_count > basic_count and advanced_count >= 2:
            return 'hard'
        elif advanced_count > 0 or basic_count >= 3:
            return 'medium'
        else:
            return 'easy'
    
    def _extract_topics(self, content: str) -> List[str]:
        """提取主题"""
        topics = []
        content_lower = content.lower()
        
        topic_keywords = {
            '排序算法': ['排序', '冒泡', '快排', '归并'],
            '搜索算法': ['搜索', '查找', '二分', 'dfs', 'bfs'],
            '动态规划': ['动态规划', 'dp', '状态转移'],
            '图算法': ['图', '最短路径', 'dijkstra', '拓扑排序'],
            '树算法': ['树', '二叉树', '遍历', '平衡树'],
            '字符串算法': ['字符串', 'kmp', '正则', '匹配'],
            '数学算法': ['数学', '质数', '最大公约数', '组合']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _generate_summary(self, content: str) -> str:
        """生成摘要"""
        # 简单的摘要生成
        sentences = re.split(r'[。！？\n]', content)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        
        if not sentences:
            return content[:200] + "..." if len(content) > 200 else content
        
        # 取前两句作为摘要
        summary_sentences = sentences[:2]
        summary = '。'.join(summary_sentences)
        
        if len(summary) > 300:
            summary = summary[:300] + "..."
        
        return summary

# 全局实例
_content_analyzer = None

def get_content_analyzer() -> ContentAnalyzerService:
    """获取内容分析器实例"""
    global _content_analyzer
    if _content_analyzer is None:
        _content_analyzer = ContentAnalyzerService()
    return _content_analyzer
