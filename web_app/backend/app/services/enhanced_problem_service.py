"""
增强的题目服务 - 处理题目详情和智能推荐
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class EnhancedProblemService:
    """增强的题目服务"""
    
    def __init__(self):
        self.problem_data_path = Path("data/raw/problem_extration")
        self.cache = {}
    
    def get_problem_detail(self, problem_title: str) -> Optional[Dict[str, Any]]:
        """获取题目详细信息"""
        try:
            # 从缓存中获取
            if problem_title in self.cache:
                return self.cache[problem_title]
            
            # 搜索题目文件
            problem_file = self._find_problem_file(problem_title)
            if not problem_file:
                return None
            
            # 读取题目数据
            with open(problem_file, 'r', encoding='utf-8') as f:
                problem_data = json.load(f)
            
            # 处理和增强数据
            enhanced_data = self._enhance_problem_data(problem_data)
            
            # 缓存结果
            self.cache[problem_title] = enhanced_data
            
            return enhanced_data
            
        except Exception as e:
            logger.error(f"获取题目详情失败: {e}")
            return None
    
    def _find_problem_file(self, problem_title: str) -> Optional[Path]:
        """查找题目文件"""
        try:
            # 遍历所有算法分类目录
            for category_dir in self.problem_data_path.iterdir():
                if category_dir.is_dir():
                    # 查找匹配的JSON文件
                    for json_file in category_dir.glob("*.json"):
                        if problem_title.lower() in json_file.stem.lower():
                            return json_file
                        
                        # 检查文件内容中的标题
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                if data.get('title', '').lower() == problem_title.lower():
                                    return json_file
                        except:
                            continue
            
            return None
            
        except Exception as e:
            logger.error(f"查找题目文件失败: {e}")
            return None
    
    def _enhance_problem_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """增强题目数据"""
        try:
            enhanced = {
                "id": raw_data.get("id", ""),
                "title": raw_data.get("title", ""),
                "description": raw_data.get("description", ""),
                "platform": raw_data.get("platform", "LeetCode"),
                "url": raw_data.get("url", ""),
                "difficulty": raw_data.get("difficulty", ""),
                "algorithm_tags": self._extract_tags(raw_data, "algorithm"),
                "data_structure_tags": self._extract_tags(raw_data, "data_structure"),
                "technique_tags": self._extract_tags(raw_data, "technique"),
                "solution_approach": self._extract_solution_approach(raw_data),
                "key_insights": self._extract_key_insights(raw_data),
                "step_by_step_explanation": self._extract_step_explanation(raw_data),
                "code_implementations": self._extract_code_implementations(raw_data),
                "time_complexity": raw_data.get("time_complexity", ""),
                "space_complexity": raw_data.get("space_complexity", ""),
                "related_problems": self._extract_related_problems(raw_data),
            }
            
            return enhanced
            
        except Exception as e:
            logger.error(f"增强题目数据失败: {e}")
            return raw_data
    
    def _extract_tags(self, data: Dict[str, Any], tag_type: str) -> List[str]:
        """提取标签"""
        tags = []
        
        # 从不同字段提取标签
        tag_fields = [
            f"{tag_type}_tags",
            "tags",
            "categories",
            "topics"
        ]
        
        for field in tag_fields:
            if field in data:
                field_data = data[field]
                if isinstance(field_data, list):
                    tags.extend([str(tag) for tag in field_data])
                elif isinstance(field_data, str):
                    tags.append(field_data)
        
        # 从解题思路中推断标签
        if tag_type == "algorithm":
            solution_text = str(data.get("solution_approach", "")).lower()
            algorithm_keywords = {
                "动态规划": ["dp", "动态规划", "dynamic programming"],
                "贪心算法": ["贪心", "greedy"],
                "回溯算法": ["回溯", "backtrack"],
                "深度优先搜索": ["dfs", "深度优先"],
                "广度优先搜索": ["bfs", "广度优先"],
                "二分查找": ["二分", "binary search"],
                "双指针": ["双指针", "two pointer"],
                "滑动窗口": ["滑动窗口", "sliding window"],
            }
            
            for algo, keywords in algorithm_keywords.items():
                if any(keyword in solution_text for keyword in keywords):
                    tags.append(algo)
        
        return list(set(tags))  # 去重
    
    def _extract_solution_approach(self, data: Dict[str, Any]) -> str:
        """提取解题思路"""
        approach_fields = [
            "solution_approach",
            "approach",
            "思路",
            "解题思路",
            "algorithm_description"
        ]
        
        for field in approach_fields:
            if field in data and data[field]:
                return str(data[field])
        
        # 从步骤解释中提取
        steps = data.get("step_by_step_explanation", [])
        if steps and isinstance(steps, list) and len(steps) > 0:
            first_step = steps[0]
            if isinstance(first_step, dict) and "text" in first_step:
                return first_step["text"]
        
        return "暂无解题思路"
    
    def _extract_key_insights(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """提取关键洞察"""
        insights = []
        
        # 从key_insights字段提取
        if "key_insights" in data:
            key_insights = data["key_insights"]
            if isinstance(key_insights, list):
                for insight in key_insights:
                    if isinstance(insight, str):
                        insights.append({"content": insight})
                    elif isinstance(insight, dict):
                        content = insight.get("content") or insight.get("text") or str(insight)
                        insights.append({"content": content})
        
        # 从其他字段提取
        insight_fields = ["insights", "key_points", "重点", "关键点"]
        for field in insight_fields:
            if field in data and isinstance(data[field], list):
                for item in data[field]:
                    content = str(item) if not isinstance(item, dict) else item.get("content", str(item))
                    insights.append({"content": content})
        
        # 如果没有洞察，生成默认的
        if not insights:
            insights = [
                {"content": "理解题目要求和约束条件"},
                {"content": "选择合适的算法和数据结构"},
                {"content": "注意边界情况的处理"},
                {"content": "优化时间和空间复杂度"}
            ]
        
        return insights
    
    def _extract_step_explanation(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取步骤解释"""
        steps = []
        
        # 从step_by_step_explanation字段提取
        if "step_by_step_explanation" in data:
            step_data = data["step_by_step_explanation"]
            if isinstance(step_data, list):
                for i, step in enumerate(step_data):
                    if isinstance(step, dict):
                        steps.append({
                            "name": step.get("name", f"步骤 {i+1}"),
                            "text": step.get("text", ""),
                            "code_snippets": self._extract_code_from_step(step),
                            "subsections": step.get("subsections", [])
                        })
                    elif isinstance(step, str):
                        steps.append({
                            "name": f"步骤 {i+1}",
                            "text": step,
                            "code_snippets": [],
                            "subsections": []
                        })
        
        # 如果没有步骤，从其他字段生成
        if not steps:
            solution = data.get("solution_approach", "")
            if solution:
                steps.append({
                    "name": "解题思路",
                    "text": solution,
                    "code_snippets": [],
                    "subsections": []
                })
        
        return steps
    
    def _extract_code_from_step(self, step: Dict[str, Any]) -> List[Dict[str, str]]:
        """从步骤中提取代码片段"""
        code_snippets = []
        
        # 从code_snippets字段提取
        if "code_snippets" in step:
            snippets = step["code_snippets"]
            if isinstance(snippets, list):
                for snippet in snippets:
                    if isinstance(snippet, dict):
                        code_snippets.append({
                            "language": snippet.get("language", "python"),
                            "code": snippet.get("code", ""),
                            "description": snippet.get("description", "")
                        })
        
        # 从code字段提取
        if "code" in step:
            code_snippets.append({
                "language": "python",
                "code": step["code"],
                "description": "实现代码"
            })
        
        return code_snippets
    
    def _extract_code_implementations(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """提取代码实现"""
        implementations = []
        
        # 从solutions字段提取
        if "solutions" in data:
            solutions = data["solutions"]
            if isinstance(solutions, list):
                for solution in solutions:
                    if isinstance(solution, dict) and "code" in solution:
                        implementations.append({
                            "language": solution.get("language", "python"),
                            "code": solution["code"],
                            "description": solution.get("approach", "解法实现"),
                            "time_complexity": solution.get("time_complexity", ""),
                            "space_complexity": solution.get("space_complexity", "")
                        })
        
        # 从code字段提取
        if "code" in data:
            implementations.append({
                "language": "python",
                "code": data["code"],
                "description": "主要实现",
                "time_complexity": data.get("time_complexity", ""),
                "space_complexity": data.get("space_complexity", "")
            })
        
        return implementations
    
    def _extract_related_problems(self, data: Dict[str, Any]) -> List[str]:
        """提取相关题目"""
        related = []
        
        related_fields = ["related_problems", "similar_problems", "相关题目"]
        for field in related_fields:
            if field in data and isinstance(data[field], list):
                related.extend([str(problem) for problem in data[field]])
        
        return list(set(related))  # 去重
    
    def get_fallback_recommendations(self, query: str) -> List[str]:
        """获取备用推荐（基于LLM）"""
        # 这里可以集成LLM来生成推荐
        # 暂时返回一些通用推荐
        fallback_recommendations = [
            "尝试从简单的相关题目开始练习",
            "复习相关的算法和数据结构基础知识",
            "查看官方题解和优秀的社区解答",
            "练习类似的题目模式和解题技巧",
            "关注时间复杂度和空间复杂度的优化"
        ]
        
        return fallback_recommendations
    
    def search_problems_by_tags(self, tags: List[str]) -> List[Dict[str, Any]]:
        """根据标签搜索题目"""
        try:
            results = []
            
            # 遍历所有题目文件
            for category_dir in self.problem_data_path.iterdir():
                if category_dir.is_dir():
                    for json_file in category_dir.glob("*.json"):
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            # 检查标签匹配
                            problem_tags = []
                            problem_tags.extend(self._extract_tags(data, "algorithm"))
                            problem_tags.extend(self._extract_tags(data, "data_structure"))
                            problem_tags.extend(self._extract_tags(data, "technique"))
                            
                            # 计算匹配度
                            matches = sum(1 for tag in tags if any(tag.lower() in ptag.lower() for ptag in problem_tags))
                            
                            if matches > 0:
                                results.append({
                                    "title": data.get("title", ""),
                                    "difficulty": data.get("difficulty", ""),
                                    "match_score": matches / len(tags),
                                    "matched_tags": [tag for tag in tags if any(tag.lower() in ptag.lower() for ptag in problem_tags)]
                                })
                        
                        except Exception as e:
                            continue
            
            # 按匹配度排序
            results.sort(key=lambda x: x["match_score"], reverse=True)
            return results[:10]  # 返回前10个
            
        except Exception as e:
            logger.error(f"根据标签搜索题目失败: {e}")
            return []
