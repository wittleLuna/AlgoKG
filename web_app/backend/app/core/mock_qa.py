"""
模拟问答系统模块
当原始问答系统不可用时使用此模块
"""

import asyncio
import json
import random
from typing import Dict, Any, List, Optional
from datetime import datetime

class MockQwenClient:
    """模拟Qwen客户端"""

    def __init__(self, api_key=None):
        self.api_key = api_key or "mock_key"
    
    def generate_response(self, prompt: str) -> str:
        """生成模拟响应"""
        if "动态规划" in prompt:
            return "动态规划是一种算法设计技术，通过将复杂问题分解为子问题来解决。"
        elif "二叉树" in prompt:
            return "二叉树是一种树形数据结构，每个节点最多有两个子节点。"
        elif "排序" in prompt:
            return "排序算法用于将数据按特定顺序排列，常见的有快速排序、归并排序等。"
        else:
            return f"这是关于'{prompt}'的模拟回答。在实际环境中，这里会调用真正的AI模型。"

class MockNeo4jKnowledgeGraphAPI:
    """模拟Neo4j知识图谱API"""
    
    def __init__(self, uri: str, user: str, password: str):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
    
    def get_problem_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """模拟获取题目信息"""
        return {
            "title": title,
            "difficulty": "中等",
            "platform": "LeetCode",
            "category": "动态规划",
            "algorithms": [{"name": "动态规划"}],
            "data_structures": [{"name": "数组"}],
            "techniques": [{"name": "状态转移"}]
        }
    
    def get_similar_problems(self, title: str, limit: int = 5) -> List[Dict[str, Any]]:
        """模拟获取相似题目"""
        similar_titles = [
            "爬楼梯",
            "斐波那契数列",
            "最长递增子序列",
            "背包问题",
            "最大子数组和"
        ]
        
        return [
            {
                "title": similar_title,
                "difficulty": random.choice(["简单", "中等", "困难"]),
                "category": "动态规划",
                "similarity_score": random.uniform(0.6, 0.9)
            }
            for similar_title in similar_titles[:limit]
        ]
    
    def get_algorithm_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """模拟获取算法信息"""
        return {
            "algorithm": {
                "name": name,
                "description": f"{name}的描述",
                "time_complexity": "O(n)",
                "space_complexity": "O(1)"
            },
            "problems": self.get_similar_problems(name, 3)
        }

    def get_node_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """模拟通用节点查询"""
        # 模拟不同类型的节点
        if "链表" in name or "节点" in name or "两两交换" in name:
            return {
                "node": {"title": name, "description": f"关于{name}的题目"},
                "type": "Problem",
                "labels": ["Problem"],
                "name": name,
                "title": name
            }
        elif "算法" in name or "排序" in name or "搜索" in name:
            return {
                "node": {"name": name, "description": f"{name}算法"},
                "type": "Algorithm",
                "labels": ["Algorithm"],
                "name": name,
                "title": name
            }
        elif "二叉树" in name or "链表" in name:
            return {
                "node": {"name": name, "description": f"{name}数据结构"},
                "type": "DataStructure",
                "labels": ["DataStructure"],
                "name": name,
                "title": name
            }
        else:
            return None
    
    def get_data_structure_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """模拟获取数据结构信息"""
        return {
            "data_structure": {
                "name": name,
                "description": f"{name}的描述",
                "operations": ["插入", "删除", "查找"]
            },
            "problems": self.get_similar_problems(name, 3)
        }
    
    def get_technique_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """模拟获取技巧信息"""
        return {
            "technique": {
                "name": name,
                "description": f"{name}的描述",
                "applications": ["场景1", "场景2"]
            },
            "problems": self.get_similar_problems(name, 3)
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """模拟获取统计信息"""
        return {
            "total_problems": 150,
            "total_algorithms": 25,
            "total_data_structures": 15,
            "difficulty_distribution": [
                {"difficulty": "简单", "count": 50},
                {"difficulty": "中等", "count": 70},
                {"difficulty": "困难", "count": 30}
            ],
            "top_categories": [
                {"category": "动态规划", "count": 30},
                {"category": "树", "count": 25},
                {"category": "图", "count": 20}
            ]
        }

class MockEnhancedRecommendationSystem:
    """模拟推荐系统"""

    def __init__(self, **kwargs):
        self.config = kwargs
        print("🔄 模拟推荐系统初始化完成")

    def recommend(self, query_title: str, top_k: int = 10, alpha: float = 0.7,
                 enable_diversity: bool = True, diversity_lambda: float = 0.3) -> Dict[str, Any]:
        """模拟推荐方法 - 与真实推荐系统接口保持一致"""
        try:
            # 模拟一些常见的算法题目
            mock_problems = [
                "两数之和", "三数之和", "四数之和", "最长公共子序列", "最长递增子序列",
                "爬楼梯", "斐波那契数列", "零钱兑换", "背包问题", "最短路径",
                "二分查找", "快速排序", "归并排序", "堆排序", "拓扑排序",
                "深度优先搜索", "广度优先搜索", "动态规划入门", "贪心算法", "分治算法"
            ]

            # 生成推荐结果
            recommendations = []
            for i in range(min(top_k, len(mock_problems))):
                problem_title = mock_problems[i]
                if problem_title == query_title:
                    continue

                recommendations.append({
                    "title": problem_title,
                    "hybrid_score": round(random.uniform(0.7, 0.95), 4),
                    "embedding_score": round(random.uniform(0.6, 0.9), 4),
                    "tag_score": round(random.uniform(0.5, 0.8), 4),
                    "shared_tags": random.sample(["动态规划", "数组", "哈希表", "双指针", "贪心"],
                                                random.randint(1, 3)),
                    "learning_path": {
                        "difficulty_progression": "简单 → 中等",
                        "concept_chain": ["基础概念", "算法思路", "代码实现"],
                        "estimated_time": f"{random.randint(30, 120)}分钟"
                    },
                    "recommendation_reason": f"与《{query_title}》在算法思路上相似，适合进阶学习"
                })

            return {
                "status": "success",
                "query_title": query_title,
                "algorithm_analysis": {
                    "primary_algorithm": "动态规划",
                    "complexity_analysis": "时间复杂度O(n)，空间复杂度O(n)",
                    "key_concepts": ["状态转移", "最优子结构"]
                },
                "recommendations": recommendations,
                "total_candidates": len(recommendations),
                "recommendation_strategy": {
                    "embedding_weight": alpha,
                    "diversity_enabled": enable_diversity,
                    "diversity_weight": diversity_lambda
                }
            }

        except Exception as e:
            print(f"模拟推荐系统错误: {e}")
            return {
                "status": "error",
                "error": str(e),
                "recommendations": []
            }

    def find_similar_problems(self, problem_title: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """模拟查找相似题目"""
        similar_problems = [
            {
                "title": f"相似题目{i+1}",
                "hybrid_score": random.uniform(0.7, 0.95),
                "similarity_analysis": {
                    "embedding_similarity": random.uniform(0.6, 0.9),
                    "tag_similarity": random.uniform(0.5, 0.8),
                    "shared_concepts": ["动态规划", "数组"]
                },
                "learning_path": {
                    "path_description": f"学习路径{i+1}",
                    "reasoning": f"推荐理由{i+1}"
                },
                "recommendation_reason": f"因为与{problem_title}在算法思路上相似",
                "recommendation_strength": "强推荐" if i < 2 else "推荐",
                "complete_info": {
                    "id": f"problem_{i+1}",
                    "title": f"相似题目{i+1}",
                    "difficulty": random.choice(["简单", "中等", "困难"]),
                    "platform": "LeetCode",
                    "algorithm_tags": ["动态规划"],
                    "data_structure_tags": ["数组"],
                    "technique_tags": ["状态转移"]
                }
            }
            for i in range(top_k)
        ]
        return similar_problems

class MockGraphEnhancedMultiAgentSystem:
    """模拟多智能体问答系统"""

    def __init__(self, rec_system=None, neo4j_api=None, entity_id_to_title_path=None, qwen_client=None, **kwargs):
        # 忽略所有可能导致初始化失败的参数
        self.rec_system = rec_system or MockEnhancedRecommendationSystem()
        self.neo4j_api = neo4j_api or MockNeo4jKnowledgeGraphAPI("", "", "")
        self.qwen_client = qwen_client or MockQwenClient()
        self.similar_problem_finder = self
        self.entity_id_to_title_path = entity_id_to_title_path
        print("🔄 模拟多智能体问答系统初始化完成")
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """模拟处理查询"""
        # 生成实时推理路径
        reasoning_path = []

        # 步骤1: 分析查询
        step_start = datetime.now()
        reasoning_path.append({
            "agent_name": "analyzer",
            "step_type": "analysis",
            "description": "分析查询意图和关键实体",
            "status": "processing",
            "start_time": step_start.isoformat(),
            "end_time": None,
            "confidence": None,
            "result": {}
        })

        # 模拟分析时间
        await asyncio.sleep(0.3)
        entities = self._extract_entities(query)

        step_end = datetime.now()
        reasoning_path[0].update({
            "status": "success",
            "end_time": step_end.isoformat(),
            "confidence": 0.92,
            "result": {
                "intent": "concept_explanation",
                "entities": entities,
                "difficulty": "中等"
            }
        })

        # 步骤2: 知识检索
        step_start = datetime.now()
        reasoning_path.append({
            "agent_name": "knowledge_retriever",
            "step_type": "retrieval",
            "description": "从知识图谱检索相关信息",
            "status": "processing",
            "start_time": step_start.isoformat(),
            "end_time": None,
            "confidence": None,
            "result": {}
        })

        # 模拟检索时间
        await asyncio.sleep(0.4)

        step_end = datetime.now()
        reasoning_path[1].update({
            "status": "success",
            "end_time": step_end.isoformat(),
            "confidence": 0.88,
            "result": {
                "count": 15,
                "sources": ["知识图谱", "题目库"],
                "concepts_found": entities
            }
        })

        # 步骤3: 概念解释
        step_start = datetime.now()
        reasoning_path.append({
            "agent_name": "concept_explainer",
            "step_type": "explanation",
            "description": "生成概念解释和示例",
            "status": "processing",
            "start_time": step_start.isoformat(),
            "end_time": None,
            "confidence": None,
            "result": {}
        })

        # 模拟解释时间
        await asyncio.sleep(0.5)
        concept_explanation = self._generate_concept_explanation(entities[0] if entities else "算法")
        example_problems = self._generate_example_problems()

        step_end = datetime.now()
        reasoning_path[2].update({
            "status": "success",
            "end_time": step_end.isoformat(),
            "confidence": 0.90,
            "result": {
                "concepts": entities,
                "examples_generated": len(example_problems),
                "explanation_sections": ["定义", "原理", "应用"]
            }
        })

        # 步骤4: 整合回答
        step_start = datetime.now()
        reasoning_path.append({
            "agent_name": "integrator",
            "step_type": "integration",
            "description": "整合所有信息生成最终回答",
            "status": "processing",
            "start_time": step_start.isoformat(),
            "end_time": None,
            "confidence": None,
            "result": {}
        })

        # 模拟整合时间
        await asyncio.sleep(0.3)
        similar_problems = self._generate_similar_problems()
        integrated_response = self._generate_integrated_response(query)

        step_end = datetime.now()
        reasoning_path[3].update({
            "status": "success",
            "end_time": step_end.isoformat(),
            "confidence": 0.94,
            "result": {
                "sections": ["概念解释", "示例题目", "相似推荐"],
                "final_confidence": 0.91,
                "response_length": len(integrated_response)
            }
        })

        result = {
            "intent": "concept_explanation",
            "entities": entities,
            "concept_explanation": concept_explanation,
            "example_problems": example_problems,
            "similar_problems": similar_problems,
            "integrated_response": integrated_response,
            "graph_data": self._generate_graph_data(entities),
            "reasoning_path": reasoning_path,
            "metadata": {
                "confidence": 0.91,
                "processing_time": sum([
                    (datetime.fromisoformat(step["end_time"]) - datetime.fromisoformat(step["start_time"])).total_seconds() * 1000
                    for step in reasoning_path if step["end_time"]
                ])
            }
        }

        # 调试信息
        print(f"生成的推理路径: {len(reasoning_path)} 个步骤")
        for i, step in enumerate(reasoning_path):
            print(f"步骤 {i+1}: {step['agent_name']} - {step['description']} - {step['status']}")

        return result
    
    def _extract_entities(self, query: str) -> List[str]:
        """提取实体"""
        entities = []
        keywords = ["动态规划", "二叉树", "排序", "图", "数组", "链表", "栈", "队列"]
        for keyword in keywords:
            if keyword in query:
                entities.append(keyword)
        return entities or ["算法"]
    
    def _generate_concept_explanation(self, concept: str) -> Dict[str, Any]:
        """生成概念解释"""
        return {
            "concept_name": concept,
            "definition": f"{concept}是一种重要的算法/数据结构概念。",
            "core_principles": [
                f"{concept}的核心原理1",
                f"{concept}的核心原理2",
                f"{concept}的核心原理3"
            ],
            "when_to_use": f"当需要{concept}相关操作时使用",
            "advantages": [f"{concept}的优点1", f"{concept}的优点2"],
            "disadvantages": [f"{concept}的缺点1"],
            "implementation_key_points": [
                f"{concept}实现要点1",
                f"{concept}实现要点2"
            ],
            "common_variations": [f"{concept}变种1", f"{concept}变种2"],
            "real_world_applications": [f"{concept}应用场景1", f"{concept}应用场景2"],
            "learning_progression": {
                "prerequisites": ["基础数学", "编程基础"],
                "next_concepts": [f"高级{concept}", f"{concept}优化"]
            },
            "visual_explanation": f"{concept}的可视化解释",
            "clickable_concepts": ["基础数学", "编程基础", f"高级{concept}"]
        }
    
    def _generate_example_problems(self) -> List[Dict[str, Any]]:
        """生成示例题目"""
        return [
            {
                "id": f"example_{i+1}",
                "title": f"示例题目{i+1}",
                "description": f"这是示例题目{i+1}的描述",
                "difficulty": random.choice(["简单", "中等", "困难"]),
                "platform": "LeetCode",
                "algorithm_tags": ["动态规划"],
                "data_structure_tags": ["数组"],
                "technique_tags": ["状态转移"],
                "solutions": [],
                "code_implementations": [],
                "key_insights": [],
                "step_by_step_explanation": [],
                "clickable": True
            }
            for i in range(3)
        ]
    
    def _generate_similar_problems(self) -> List[Dict[str, Any]]:
        """生成相似题目"""
        # 生成高质量的相似题目推荐
        problems = [
            {
                "title": "爬楼梯",
                "hybrid_score": 0.92,
                "embedding_score": 0.88,
                "tag_score": 0.85,
                "shared_tags": ["动态规划", "数学"],
                "learning_path": "基础动态规划 → 状态转移 → 优化空间复杂度",
                "recommendation_reason": "这是动态规划的经典入门题目，与您的问题在状态转移思想上高度相似，是理解动态规划核心概念的最佳起点。",
                "learning_path_explanation": "从简单的递推关系开始，逐步理解状态定义和转移方程的设计思路",
                "recommendation_strength": "强推荐",
                "complete_info": {
                    "id": "climbing_stairs",
                    "title": "爬楼梯",
                    "difficulty": "简单",
                    "platform": "LeetCode",
                    "algorithm_tags": ["动态规划"],
                    "data_structure_tags": ["数组"],
                    "technique_tags": ["状态转移"]
                },
                "clickable": True
            },
            {
                "title": "斐波那契数",
                "hybrid_score": 0.89,
                "embedding_score": 0.85,
                "tag_score": 0.82,
                "shared_tags": ["动态规划", "递归", "数学"],
                "learning_path": "递归思维 → 记忆化搜索 → 动态规划",
                "recommendation_reason": "斐波那契数列是理解从递归到动态规划转换的经典例子，能帮助您深入理解动态规划的本质。",
                "learning_path_explanation": "通过对比递归和动态规划两种解法，理解动态规划如何避免重复计算",
                "recommendation_strength": "强推荐",
                "complete_info": {
                    "id": "fibonacci",
                    "title": "斐波那契数",
                    "difficulty": "简单",
                    "platform": "LeetCode",
                    "algorithm_tags": ["动态规划", "递归"],
                    "data_structure_tags": ["数组"],
                    "technique_tags": ["记忆化"]
                },
                "clickable": True
            },
            {
                "title": "最大子数组和",
                "hybrid_score": 0.86,
                "embedding_score": 0.83,
                "tag_score": 0.78,
                "shared_tags": ["动态规划", "数组"],
                "learning_path": "一维动态规划 → 状态优化 → Kadane算法",
                "recommendation_reason": "这道题展示了动态规划在数组问题中的应用，状态定义更加灵活，是进阶学习的好选择。",
                "learning_path_explanation": "学习如何定义更复杂的状态，以及如何优化空间复杂度",
                "recommendation_strength": "推荐",
                "complete_info": {
                    "id": "max_subarray",
                    "title": "最大子数组和",
                    "difficulty": "中等",
                    "platform": "LeetCode",
                    "algorithm_tags": ["动态规划"],
                    "data_structure_tags": ["数组"],
                    "technique_tags": ["Kadane算法"]
                },
                "clickable": True
            }
        ]

        # 添加Neo4j节点对象到概念解释中，用于测试前端处理
        if len(problems) > 0:
            # 模拟Neo4j节点对象
            neo4j_node_example = "<Node element_id='79' labels=frozenset({'Algorithm'}) properties={'name': 'Dynamic Programming', 'description': '动态规划是一种算法设计技术', 'difficulty': 'medium', 'applications': ['最优化问题', '计数问题'], 'time_complexity': 'O(n)', 'space_complexity': 'O(n)'}>"

            # 将Neo4j节点添加到第一个问题的推荐理由中
            problems[0]["recommendation_reason"] += f"\n\n相关算法节点：{neo4j_node_example}"

        return problems
    
    def _generate_integrated_response(self, query: str) -> str:
        """生成整合回答"""
        return f"""
基于您的问题"{query}"，我为您提供以下解答：

这是一个关于算法和数据结构的问题。在实际的系统中，这里会调用多个智能体协作生成详细的回答，包括：

1. **概念解释**: 详细解释相关概念的定义、原理和应用场景
2. **示例题目**: 提供相关的练习题目帮助理解
3. **相似推荐**: 推荐相似的题目和学习路径
4. **代码实现**: 提供具体的代码示例和实现要点

目前您看到的是模拟响应。要获得完整功能，请确保：
- 原始问答系统模块可用
- 模型文件和数据文件已正确放置
- Neo4j数据库包含知识图谱数据

您可以继续测试界面功能，所有交互都会正常工作。
        """.strip()
    
    def _generate_graph_data(self, entities: List[str]) -> Dict[str, Any]:
        """生成图谱数据"""
        nodes = []
        edges = []

        # 添加中心节点
        if entities:
            center_entity = entities[0]
            center_id = f"concept_{center_entity.replace(' ', '_')}"
            nodes.append({
                "id": center_id,
                "label": center_entity,
                "type": "Concept",
                "properties": {"is_center": True},
                "clickable": True
            })

            # 添加相关概念节点
            related_concepts = ["基础概念", "高级应用", "相关算法", "实际应用"]
            for i, concept in enumerate(related_concepts):
                node_id = f"related_{i}"
                nodes.append({
                    "id": node_id,
                    "label": concept,
                    "type": "Concept",
                    "properties": {},
                    "clickable": True
                })

                edges.append({
                    "source": center_id,
                    "target": node_id,
                    "relationship": "RELATED_TO",
                    "properties": {}
                })

            # 添加示例题目节点
            for i in range(3):
                problem_id = f"problem_{i+1}"
                nodes.append({
                    "id": problem_id,
                    "label": f"示例题目{i+1}",
                    "type": "Problem",
                    "properties": {"difficulty": "中等"},
                    "clickable": True
                })

                edges.append({
                    "source": center_id,
                    "target": problem_id,
                    "relationship": "EXAMPLE_OF",
                    "properties": {}
                })

            # 添加算法节点
            algorithm_id = f"algorithm_{center_entity.replace(' ', '_')}"
            nodes.append({
                "id": algorithm_id,
                "label": f"{center_entity}算法",
                "type": "Algorithm",
                "properties": {},
                "clickable": True
            })

            edges.append({
                "source": center_id,
                "target": algorithm_id,
                "relationship": "IMPLEMENTS",
                "properties": {}
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "center_node": center_id if entities else None,
            "layout_type": "force"
        }
    
    def _generate_reasoning_path(self) -> List[Dict[str, Any]]:
        """生成推理路径"""
        return [
            {
                "agent_name": "analyzer",
                "step_type": "analysis",
                "description": "分析查询意图和关键实体",
                "status": "success",
                "start_time": datetime.now().isoformat(),
                "end_time": datetime.now().isoformat(),
                "confidence": 0.9,
                "result": {"entities": ["动态规划"]}
            },
            {
                "agent_name": "knowledge_retriever",
                "step_type": "retrieval",
                "description": "从知识图谱检索相关信息",
                "status": "success",
                "start_time": datetime.now().isoformat(),
                "end_time": datetime.now().isoformat(),
                "confidence": 0.85,
                "result": {"count": 15, "sources": ["知识图谱", "题目库"]}
            },
            {
                "agent_name": "concept_explainer",
                "step_type": "explanation",
                "description": "生成概念解释和示例",
                "status": "success",
                "start_time": datetime.now().isoformat(),
                "end_time": datetime.now().isoformat(),
                "confidence": 0.88,
                "result": {"concepts": ["动态规划", "状态转移"]}
            },
            {
                "agent_name": "integrator",
                "step_type": "integration",
                "description": "整合所有信息生成最终回答",
                "status": "success",
                "start_time": datetime.now().isoformat(),
                "end_time": datetime.now().isoformat(),
                "confidence": 0.92,
                "result": {"sections": ["概念解释", "示例题目", "相似推荐"]}
            }
        ]
    
    async def find_similar_problems(self, problem_title: str, count: int = 5):
        """模拟查找相似题目"""
        # 模拟异步处理
        await asyncio.sleep(0.3)
        
        class MockResponse:
            def __init__(self, content):
                self.content = content
        
        similar_data = self.rec_system.find_similar_problems(problem_title, count)
        return MockResponse(similar_data)
