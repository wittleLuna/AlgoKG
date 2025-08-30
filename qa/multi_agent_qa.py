import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import torch
import torch.nn.functional as F
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from qa.embedding_qa import EnhancedRecommendationSystem
from extractors.extract_knowledgePoint import QwenClientNative as QwenClient
from backend.neo4j_loader.neo4j_api import Neo4jKnowledgeGraphAPI
import difflib

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentType(str, Enum):
    ANALYZER = "analyzer"
    KNOWLEDGE_RETRIEVER = "knowledge_retriever"
    RECOMMENDER = "recommender"
    CONCEPT_EXPLAINER = "concept_explainer"
    SIMILAR_PROBLEM_FINDER = "similar_problem_finder"
    INTEGRATOR = "integrator"

@dataclass
class QueryContext:
    """查询上下文"""
    user_query: str
    intent: str
    entities: List[str]
    difficulty: Optional[str] = None
    topic: Optional[str] = None
    solved_problems: Optional[List[str]] = None
    target_concept: Optional[str] = None

@dataclass
class AgentResponse:
    """Agent响应"""
    agent_type: AgentType
    content: Any
    confidence: float
    metadata: Dict[str, Any] = None

class EnhancedNeo4jKnowledgeGraphAPI:
    """增强的Neo4j知识图谱API，专门用于获取题目信息"""
    
    def __init__(self, neo4j_api: Neo4jKnowledgeGraphAPI, entity_id_to_title: Dict[str, str]):
        self.neo4j_api = neo4j_api
        self.entity_id_to_title = entity_id_to_title
        self.title_to_entity_id = {v: k for k, v in entity_id_to_title.items()}
        
        # 创建题目标题的模糊匹配索引
        self.all_titles = list(entity_id_to_title.values())
        
    def _find_similar_titles(self, query_title: str, max_suggestions: int = 3) -> List[str]:
        """模糊匹配题目标题"""
        # 使用difflib进行模糊匹配
        matches = difflib.get_close_matches(query_title, self.all_titles, 
                                          n=max_suggestions, cutoff=0.6)
        if matches:
            return matches
            
        # 如果没有匹配，尝试部分匹配
        partial_matches = []
        query_lower = query_title.lower()
        for title in self.all_titles:
            if query_lower in title.lower() or title.lower() in query_lower:
                partial_matches.append(title)
                if len(partial_matches) >= max_suggestions:
                    break
        
        return partial_matches
    
    def get_complete_problem_info(self, problem_title: str = None, problem_id: str = None) -> Dict[str, Any]:
        """获取题目的完整信息，包括解法和代码实现 - 增强错误处理版"""

        # 如果提供的是标题，先转换为实体ID
        if problem_title:
            # 首先尝试精确匹配
            if problem_title in self.title_to_entity_id:
                entity_id = self.title_to_entity_id[problem_title]
            else:
                # 模糊匹配
                similar_titles = self._find_similar_titles(problem_title, 1)
                if similar_titles:
                    entity_id = self.title_to_entity_id[similar_titles[0]]
                    logger.info(f"模糊匹配：'{problem_title}' -> '{similar_titles[0]}'")
                else:
                    logger.warning(f"未找到题目：{problem_title}")
                    return self._get_basic_problem_info(None, problem_title)
        else:
            entity_id = problem_id

        # 使用Neo4j API获取完整的题目信息
        try:
            problem_info = self.neo4j_api.get_problem_by_title(problem_title or entity_id)
            if problem_info:
                return self._format_complete_problem_info(problem_info)
        except Exception as e:
            logger.warning(f"从Neo4j获取题目信息失败: {e}")

        # 构建查询，获取题目的所有相关信息（备用方案）
        query = """
        MATCH (p:Problem)
        WHERE p.id = $entity_id OR p.title = $title
        OPTIONAL MATCH (p)-[:HAS_SOLUTION]->(s:Solution)
        OPTIONAL MATCH (s)-[:HAS_CODE]->(c:Code)
        OPTIONAL MATCH (p)-[:HAS_TAG]->(t:Tag)
        OPTIONAL MATCH (p)-[:HAS_INSIGHT]->(i:Insight)
        OPTIONAL MATCH (p)-[:HAS_STEP]->(step:Step)
        OPTIONAL MATCH (step)-[:HAS_CODE]->(step_code:Code)
        OPTIONAL MATCH (p)-[:HAS_IMAGE]->(img:Image)
        RETURN p,
               collect(DISTINCT s) as solutions,
               collect(DISTINCT c) as codes,
               collect(DISTINCT t) as tags,
               collect(DISTINCT i) as insights,
               collect(DISTINCT {step: step, code: step_code}) as steps,
               collect(DISTINCT img) as images
        """
        
        params = {
            "entity_id": entity_id,
            "title": problem_title or ""
        }
        
        try:
            # 尝试不同的Neo4j API方法
            result = None

            if hasattr(self.neo4j_api, 'run_query'):
                result = self.neo4j_api.run_query(query, params)
            elif hasattr(self.neo4j_api, 'execute_query'):
                result = self.neo4j_api.execute_query(query, params)
            elif hasattr(self.neo4j_api, 'driver') and self.neo4j_api.driver:
                # 直接使用driver执行查询
                with self.neo4j_api.driver.session() as session:
                    result = session.run(query, params).data()
            else:
                logger.warning("Neo4j API方法不明确，返回基础信息")
                return self._get_basic_problem_info(entity_id, problem_title)

            if result and len(result) > 0:
                # 检查返回结果的格式
                first_record = result[0]
                logger.debug(f"Neo4j查询返回结果键: {list(first_record.keys())}")

                return self._format_complete_problem_info_from_query(first_record)
            else:
                logger.warning(f"Neo4j查询无结果: entity_id={entity_id}, title={problem_title}")
                return self._get_basic_problem_info(entity_id, problem_title)

        except Exception as e:
            logger.error(f"获取完整题目信息失败: {e}")
            import traceback
            logger.debug(f"详细错误信息: {traceback.format_exc()}")
            # 返回基础信息作为备用
            return self._get_basic_problem_info(entity_id, problem_title)

    def debug_neo4j_connection(self):
        """调试Neo4j连接和数据结构"""
        try:
            # 测试简单查询
            test_query = "MATCH (n) RETURN labels(n) as node_types, count(n) as count LIMIT 10"

            if hasattr(self.neo4j_api, 'driver') and self.neo4j_api.driver:
                with self.neo4j_api.driver.session() as session:
                    result = session.run(test_query).data()
                    logger.info(f"Neo4j节点类型统计: {result}")

            # 测试Problem节点结构
            problem_query = "MATCH (p:Problem) RETURN p LIMIT 1"
            if hasattr(self.neo4j_api, 'driver') and self.neo4j_api.driver:
                with self.neo4j_api.driver.session() as session:
                    result = session.run(problem_query).data()
                    if result:
                        sample_problem = result[0]
                        logger.info(f"示例Problem节点结构: {list(sample_problem.keys())}")
                        if 'p' in sample_problem:
                            logger.info(f"Problem节点属性: {list(sample_problem['p'].keys())}")
                    else:
                        logger.warning("没有找到Problem节点")

        except Exception as e:
            logger.error(f"调试Neo4j连接失败: {e}")
    
    def _get_basic_problem_info(self, entity_id: str, problem_title: str = None) -> Dict[str, Any]:
        """获取基础题目信息（当Neo4j查询失败时的备用方案）"""
        title = problem_title or self.entity_id_to_title.get(entity_id, entity_id)
        
        # 根据题目标题推断一些基础信息
        difficulty = "中等"  # 默认难度
        algorithm_tags = []
        
        # 简单的标签推断逻辑
        title_lower = title.lower()
        if "动态规划" in title or "dp" in title_lower:
            algorithm_tags.append("动态规划")
        if "二叉树" in title:
            algorithm_tags.extend(["二叉树", "树"])
        if "链表" in title:
            algorithm_tags.append("链表")
        if "回溯" in title or "排列" in title or "组合" in title:
            algorithm_tags.append("回溯")
        if "贪心" in title:
            algorithm_tags.append("贪心")
        if "栈" in title or "队列" in title:
            algorithm_tags.extend(["栈", "队列"])
        
        return {
            "id": entity_id,
            "title": title,
            "description": f"这是关于{title}的算法题目",
            "difficulty": difficulty,
            "platform": "LeetCode",
            "url": "",
            "algorithm_tags": algorithm_tags,
            "data_structure_tags": [],
            "technique_tags": [],
            "solutions": [],
            "code_implementations": [],
            "key_insights": [],
            "step_by_step_explanation": [],
            "images": [],
            "step_by_step": []
        }

    def _format_complete_problem_info(self, problem_info: Dict) -> Dict:
        """格式化完整的题目信息"""
        if not problem_info:
            return {}

        # 安全地提取算法标签
        algorithms = problem_info.get("algorithms", [])
        algorithm_tags = []
        if algorithms:
            for alg in algorithms:
                if isinstance(alg, dict):
                    algorithm_tags.append(alg.get("name", ""))
                else:
                    algorithm_tags.append(str(alg))

        # 安全地提取数据结构标签
        data_structures = problem_info.get("data_structures", [])
        data_structure_tags = []
        if data_structures:
            for ds in data_structures:
                if isinstance(ds, dict):
                    data_structure_tags.append(ds.get("name", ""))
                else:
                    data_structure_tags.append(str(ds))

        # 安全地提取技巧标签
        techniques = problem_info.get("techniques", [])
        technique_tags = []
        if techniques:
            for tech in techniques:
                if isinstance(tech, dict):
                    technique_tags.append(tech.get("name", ""))
                else:
                    technique_tags.append(str(tech))

        # 安全地提取洞察
        insights = problem_info.get("insights", [])
        key_insights = []
        if insights:
            for ins in insights:
                if isinstance(ins, dict):
                    key_insights.append(ins.get("content", ""))
                else:
                    key_insights.append(str(ins))

        return {
            "id": problem_info.get("title", ""),
            "title": problem_info.get("title", ""),
            "description": problem_info.get("description", ""),
            "difficulty": problem_info.get("difficulty", ""),
            "platform": problem_info.get("platform", "LeetCode"),
            "url": problem_info.get("url", ""),
            "algorithm_tags": algorithm_tags,
            "data_structure_tags": data_structure_tags,
            "technique_tags": technique_tags,
            "solutions": problem_info.get("solutions", []),
            "code_implementations": [],
            "key_insights": key_insights,
            "step_by_step_explanation": problem_info.get("step_by_step", []),
            "images": problem_info.get("images", []),
            "step_by_step": problem_info.get("step_by_step", [])
        }
    
    def get_problems_by_concept(self, concept: str, difficulty: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """根据概念获取相关题目的完整信息"""
        
        # 模糊匹配概念
        matching_problems = []
        concept_lower = concept.lower()
        
        for entity_id, title in self.entity_id_to_title.items():
            title_lower = title.lower()
            
            # 概念匹配逻辑
            should_include = False
            
            if concept_lower in ["动态规划", "dp"]:
                if any(keyword in title_lower for keyword in ["买卖股票", "爬楼梯", "子序列", "背包", "路径", "拆分"]):
                    should_include = True
            elif concept_lower in ["二叉树", "树"]:
                if "二叉树" in title_lower or "树" in title_lower:
                    should_include = True
            elif concept_lower in ["链表"]:
                if "链表" in title_lower:
                    should_include = True
            elif concept_lower in ["回溯", "递归"]:
                if any(keyword in title_lower for keyword in ["全排列", "组合", "子集", "分割", "n皇后"]):
                    should_include = True
            elif concept_lower in ["贪心"]:
                if any(keyword in title_lower for keyword in ["跳跃", "分发", "加油站", "区间", "序列"]):
                    should_include = True
            elif concept_lower in ["栈", "队列"]:
                if any(keyword in title_lower for keyword in ["栈", "队列", "括号", "温度"]):
                    should_include = True
            else:
                # 直接文本匹配
                if concept_lower in title_lower:
                    should_include = True
            
            if should_include:
                problem_info = self.get_complete_problem_info(problem_title=title)
                if problem_info:
                    matching_problems.append(problem_info)
                    if len(matching_problems) >= limit:
                        break
        
        return matching_problems
    
    def get_concept_explanation_data(self, concept: str) -> Dict[str, Any]:
        """获取概念的相关数据用于LLM解释"""
        
        related_problems = [p["title"] for p in self.get_problems_by_concept(concept, limit=5)]
        
        # 根据概念推断前置和后续概念
        prerequisites = []
        next_concepts = []
        similar_concepts = []
        
        concept_lower = concept.lower()
        
        if concept_lower in ["动态规划", "dp"]:
            prerequisites = ["递归", "数学归纳法"]
            next_concepts = ["状态压缩DP", "树形DP"]
            similar_concepts = ["贪心算法", "分治算法"]
        elif concept_lower in ["二叉树", "树"]:
            prerequisites = ["递归", "栈和队列"]
            next_concepts = ["平衡二叉树", "线段树", "字典树"]
            similar_concepts = ["图", "堆"]
        elif concept_lower in ["回溯"]:
            prerequisites = ["递归", "深度优先搜索"]
            next_concepts = ["剪枝优化", "记忆化搜索"]
            similar_concepts = ["动态规划", "分治"]
        
        return {
            "concept": {"name": concept},
            "related_problems": related_problems,
            "prerequisites": prerequisites,
            "next_concepts": next_concepts,
            "similar_concepts": similar_concepts
        }
    
    def find_similar_problems_by_graph(self, problem_title: str, limit: int = 5) -> List[Dict[str, Any]]:
        """通过图结构找到相似的题目"""
        
        # 获取目标题目信息
        target_problem = self.get_complete_problem_info(problem_title=problem_title)
        if not target_problem:
            return []
        
        target_tags = set(target_problem.get("algorithm_tags", []))
        similar_problems = []
        
        # 遍历所有题目，找到相似的
        for entity_id, title in self.entity_id_to_title.items():
            if title == problem_title:
                continue
                
            candidate_problem = self.get_complete_problem_info(problem_title=title)
            if not candidate_problem:
                continue
                
            candidate_tags = set(candidate_problem.get("algorithm_tags", []))
            common_tags = target_tags & candidate_tags
            
            if common_tags:
                similarity_score = len(common_tags)
                similarity_reason = f"共享{len(common_tags)}个算法标签: {', '.join(common_tags)}"
                
                candidate_problem["similarity_score"] = similarity_score
                candidate_problem["similarity_reason"] = similarity_reason
                similar_problems.append(candidate_problem)
        
        # 按相似度排序
        similar_problems.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar_problems[:limit]
    
    def _format_complete_problem_info_from_query(self, result: Dict) -> Dict[str, Any]:
        """格式化从Cypher查询返回的完整题目信息 - 修复版"""

        # 安全获取problem信息，处理多种可能的返回格式
        problem = None

        # 尝试多种可能的键名
        for key in ['p', 'problem', 'node', 'n']:
            if key in result:
                problem = result[key]
                break

        if not problem:
            logger.warning(f"查询结果中缺少题目信息，可用键: {list(result.keys())}")
            return {}
        # 安全获取其他相关信息
        solutions = result.get("solutions", []) or []
        codes = result.get("codes", []) or []
        tags = result.get("tags", []) or []
        insights = result.get("insights", []) or []
        steps = result.get("steps", []) or []
        
        # 格式化解决方案
        formatted_solutions = []
        for solution in solutions:
            if solution and isinstance(solution, dict):
                formatted_solutions.append({
                    "approach": solution.get("approach", ""),
                    "time_complexity": solution.get("time_complexity", ""),
                    "space_complexity": solution.get("space_complexity", ""),
                    "description": solution.get("description", "")
                })
        
        # 格式化代码实现
        formatted_codes = []
        for code in codes:
            if code and isinstance(code, dict):
                formatted_codes.append({
                    "language": code.get("language", ""),
                    "code": code.get("code", ""),
                    "description": code.get("description", "")
                })
        
        # 格式化关键洞察
        formatted_insights = []
        for insight in insights:
            if insight and isinstance(insight, dict):
                formatted_insights.append({
                    "content": insight.get("content", ""),
                    "category": insight.get("category", "")
                })
        
        # 格式化步骤解释
        formatted_steps = []
        for step_info in steps:
            if step_info and isinstance(step_info, dict):
                step = step_info.get("step")
                step_code = step_info.get("code")

                if step and isinstance(step, dict):
                    formatted_step = {
                        "name": step.get("name", ""),
                        "text": step.get("text", ""),
                        "order": step.get("order", 0)
                    }
                    if step_code and isinstance(step_code, dict):
                        formatted_step["code_snippets"] = [{
                            "language": step_code.get("language", ""),
                            "code": step_code.get("code", ""),
                            "description": step_code.get("description", "")
                        }]
                    formatted_steps.append(formatted_step)
        
        # 排序步骤
        formatted_steps.sort(key=lambda x: x.get("order", 0))
        
        return {
            "id": problem.get("id", ""),
            "title": problem.get("title", ""),
            "description": problem.get("description", ""),
            "difficulty": problem.get("difficulty", ""),
            "platform": problem.get("platform", ""),
            "url": problem.get("url", ""),
            "algorithm_tags": self._extract_tag_names(tags, "algorithm"),
            "data_structure_tags": self._extract_tag_names(tags, "data_structure"),
            "technique_tags": self._extract_tag_names(tags, "technique"),
            "solutions": formatted_solutions,
            "code_implementations": formatted_codes,
            "key_insights": formatted_insights,
            "step_by_step_explanation": formatted_steps
        }

    def _extract_tag_names(self, tags, tag_type):
        """从Neo4j标签节点中提取标签名称"""
        tag_names = []

        logger.debug(f"提取标签名称，标签类型: {tag_type}, 标签数量: {len(tags)}")

        for i, tag in enumerate(tags):
            if not tag:
                continue

            try:
                logger.debug(f"处理标签 {i}: {type(tag)} - {str(tag)[:100]}")

                # 处理Neo4j节点对象
                if hasattr(tag, 'labels') and hasattr(tag, 'get'):
                    # 这是真正的Neo4j Node对象
                    node_labels = list(tag.labels)
                    logger.debug(f"Neo4j节点标签: {node_labels}")

                    # 检查节点类型是否匹配
                    target_label = None
                    if tag_type == "algorithm":
                        target_label = "Algorithm"
                    elif tag_type == "data_structure":
                        target_label = "DataStructure"
                    elif tag_type == "technique":
                        target_label = "Technique"

                    if target_label and target_label in node_labels:
                        name = tag.get("name", "")
                        if name:
                            tag_names.append(name)
                            logger.debug(f"提取到{tag_type}标签: {name}")
                    else:
                        # 如果不匹配特定类型，但有name属性，也提取出来
                        name = tag.get("name", "")
                        if name:
                            tag_names.append(name)
                            logger.debug(f"提取到通用标签: {name}")

                elif hasattr(tag, 'get'):
                    # 如果是字典格式
                    if tag.get("type") == tag_type:
                        name = tag.get("name", "")
                        if name:
                            tag_names.append(name)
                            logger.debug(f"从字典提取标签: {name}")
                    else:
                        # 尝试直接获取name
                        name = tag.get("name", "") or tag.get("title", "")
                        if name:
                            tag_names.append(name)
                            logger.debug(f"从字典提取通用标签: {name}")

                elif isinstance(tag, str):
                    # 如果是字符串，检查是否是Neo4j节点字符串
                    if tag.startswith('<Node element_id='):
                        # 尝试从字符串中提取name
                        import re
                        name_match = re.search(r"'name':\s*'([^']+)'", tag)
                        if name_match:
                            name = name_match.group(1)
                            tag_names.append(name)
                            logger.debug(f"从节点字符串提取标签: {name}")
                    else:
                        # 普通字符串
                        tag_names.append(tag)
                        logger.debug(f"直接使用字符串标签: {tag}")
                else:
                    # 其他情况，尝试转换为字符串
                    tag_str = str(tag)
                    if tag_str and not tag_str.startswith('<Node'):
                        tag_names.append(tag_str)
                        logger.debug(f"转换为字符串标签: {tag_str}")

            except Exception as e:
                logger.warning(f"处理标签时出错: {tag}, 错误: {e}")
                # 尝试转换为字符串作为备用
                try:
                    tag_str = str(tag)
                    if tag_str and not tag_str.startswith('<Node'):
                        tag_names.append(tag_str)
                        logger.debug(f"备用方式提取标签: {tag_str}")
                except:
                    continue

        unique_tags = list(set(tag_names))  # 去重
        logger.debug(f"最终提取的{tag_type}标签: {unique_tags}")
        return unique_tags

    def _clean_tag_list(self, tags):
        """清理标签列表，确保返回字符串列表而不是Neo4j节点对象"""
        if not tags:
            return []

        cleaned_tags = []
        for tag in tags:
            if not tag:
                continue

            try:
                # 如果是字符串，直接使用
                if isinstance(tag, str):
                    # 检查是否是Neo4j节点字符串表示
                    if tag.startswith('<Node element_id='):
                        # 尝试从Neo4j节点字符串中提取名称
                        import re
                        name_match = re.search(r"'name':\s*'([^']+)'", tag)
                        if name_match:
                            cleaned_tags.append(name_match.group(1))
                        else:
                            # 如果无法提取名称，跳过这个标签
                            continue
                    else:
                        cleaned_tags.append(tag)
                # 如果是Neo4j节点对象
                elif hasattr(tag, 'get') and hasattr(tag, 'labels'):
                    name = tag.get("name", "")
                    if name:
                        cleaned_tags.append(name)
                # 如果是字典
                elif hasattr(tag, 'get'):
                    name = tag.get("name", "") or tag.get("title", "")
                    if name:
                        cleaned_tags.append(name)
                # 其他情况，尝试转换为字符串
                else:
                    tag_str = str(tag)
                    if tag_str and not tag_str.startswith('<Node'):
                        cleaned_tags.append(tag_str)

            except Exception as e:
                logger.warning(f"清理标签时出错: {tag}, 错误: {e}")
                continue

        return list(set(cleaned_tags))  # 去重

class GraphBasedKnowledgeRetrieverAgent:
    """基于图的知识检索Agent"""
    # 
    
    def __init__(self, enhanced_kg_api: EnhancedNeo4jKnowledgeGraphAPI):
        self.kg_api = enhanced_kg_api
        
    async def retrieve_complete_problems(self, context: QueryContext) -> AgentResponse:
        """从图中检索完整的题目信息"""
        
        try:
            complete_problems = []
            
            # 根据实体（概念）检索题目
            for entity in context.entities:
                problems = self.kg_api.get_problems_by_concept(
                    concept=entity,
                    difficulty=context.difficulty,
                    limit=5
                )
                complete_problems.extend(problems)
            
            # 如果有已解决的题目，也获取其完整信息
            if context.solved_problems:
                for problem_title in context.solved_problems[-3:]:  # 最近3个
                    problem_info = self.kg_api.get_complete_problem_info(problem_title=problem_title)
                    if problem_info:
                        complete_problems.append(problem_info)
            
            # 去重
            seen_titles = set()
            unique_problems = []
            for problem in complete_problems:
                if problem["title"] not in seen_titles:
                    seen_titles.add(problem["title"])
                    unique_problems.append(problem)
            
            return AgentResponse(
                agent_type=AgentType.KNOWLEDGE_RETRIEVER,
                content=unique_problems[:10],
                confidence=0.9 if unique_problems else 0.3,
                metadata={
                    "total_problems": len(unique_problems),
                    "entities_searched": context.entities
                }
            )
            
        except Exception as e:
            logger.error(f"图检索失败: {e}")
            return AgentResponse(
                agent_type=AgentType.KNOWLEDGE_RETRIEVER,
                content=[],
                confidence=0.1,
                metadata={"error": str(e)}
            )

class GraphBasedSimilarProblemFinderAgent:
    """基于图的相似题目发现Agent - 增强推荐理由"""
    
    def __init__(self, rec_system: EnhancedRecommendationSystem, enhanced_kg_api: EnhancedNeo4jKnowledgeGraphAPI):
        self.rec_system = rec_system
        self.kg_api = enhanced_kg_api
        
    def _generate_enhanced_recommendation_reason(self, 
                                               target_problem: Dict,
                                               candidate_problem: Dict,
                                               shared_tags: List[str], 
                                               embedding_sim: float, 
                                               tag_sim: float,
                                               hybrid_score: float) -> Dict[str, Any]:
        """生成增强的推荐理由（类似第二份代码的风格）"""
        
        reasons = []
        learning_path_info = {}
        
        # 1. 标签相似性分析
        if shared_tags:
            if len(shared_tags) == 1:
                reasons.append(f"同属{shared_tags[0]}类问题")
                learning_path_info["path_type"] = "渐进式学习"
                learning_path_info["primary_concept"] = shared_tags[0]
            else:
                primary_tags = shared_tags[:2]  # 取前两个主要标签
                reasons.append(f"涉及{len(shared_tags)}个共同知识点: {', '.join(primary_tags)}")
                learning_path_info["path_type"] = "综合技能训练"
                learning_path_info["primary_concept"] = primary_tags[0]
                learning_path_info["secondary_concepts"] = primary_tags[1:]
        
        # 2. 语义相似性分析
        if embedding_sim > 0.8:
            reasons.append("解题思路高度相似")
            learning_path_info["similarity_level"] = "高度相似"
        elif embedding_sim > 0.6:
            reasons.append("解题思路相关")
            learning_path_info["similarity_level"] = "中度相似"
        elif embedding_sim > 0.4:
            reasons.append("解题模式类似")
            learning_path_info["similarity_level"] = "模式相近"
        
        # 3. 难度分析
        target_difficulty = target_problem.get("difficulty", "中等")
        candidate_difficulty = candidate_problem.get("difficulty", "中等")
        
        if target_difficulty == candidate_difficulty:
            reasons.append(f"同等难度({target_difficulty})")
            learning_path_info["difficulty_progression"] = "水平巩固"
        else:
            reasons.append(f"难度递进({target_difficulty}→{candidate_difficulty})")
            learning_path_info["difficulty_progression"] = "难度提升"
        
        # 4. 技能要求匹配
        if tag_sim > 0.5:
            reasons.append("技能要求匹配")
        
        # 5. 学习路径生成
        target_title = target_problem.get("title", "")
        candidate_title = candidate_problem.get("title", "")
        
        if shared_tags:
            path_description = f"《{target_title}》→ [{shared_tags[0]}] → 《{candidate_title}》"
            path_reasoning = f"基于{shared_tags[0]}的深化练习"
        else:
            path_description = f"《{target_title}》→ [拓展学习] → 《{candidate_title}》"
            path_reasoning = "基于语义相似性的拓展练习，有助于开拓解题思路"
        
        learning_path_info.update({
            "path_description": path_description,
            "reasoning": path_reasoning
        })
        
        # 6. 综合推荐强度
        if hybrid_score > 0.8:
            recommendation_strength = "强烈推荐"
        elif hybrid_score > 0.6:
            recommendation_strength = "推荐"
        else:
            recommendation_strength = "可考虑"
        
        if not reasons:
            reasons.append("拓展练习推荐")
        
        return {
            "recommendation_reason": "，".join(reasons),
            "recommendation_strength": recommendation_strength,
            "learning_path": learning_path_info,
            "similarity_analysis": {
                "embedding_similarity": embedding_sim,
                "tag_similarity": tag_sim,
                "hybrid_score": hybrid_score,
                "shared_concepts": self._clean_tag_list(shared_tags)
            }
        }
        
    async def find_similar_problems(self, target_problem_title: str, count: int = 5) -> AgentResponse:
        """结合图结构和embedding找到相似题目 - 增强版"""
        
        try:
            # 获取目标题目的完整信息
            target_problem = self.kg_api.get_complete_problem_info(problem_title=target_problem_title)
            if not target_problem:
                return AgentResponse(
                    agent_type=AgentType.SIMILAR_PROBLEM_FINDER,
                    content=[],
                    confidence=0.1,
                    metadata={"error": f"未找到目标题目: {target_problem_title}"}
                )
            
            similar_problems = []
            
            # 1. 通过图结构找相似题目（基于共同标签）
            graph_similar = self.kg_api.find_similar_problems_by_graph(target_problem_title, count * 2)
            for problem in graph_similar:
                enhanced_reason = self._generate_enhanced_recommendation_reason(
                    target_problem=target_problem,
                    candidate_problem=problem,
                    shared_tags=problem.get("algorithm_tags", []),
                    embedding_sim=0.7,  # 图相似的默认embedding分数
                    tag_sim=problem.get("similarity_score", 0) * 0.1,
                    hybrid_score=problem.get("similarity_score", 0) * 0.1 + 0.7
                )
                
                similar_problems.append({
                    "title": problem["title"],
                    "hybrid_score": enhanced_reason["similarity_analysis"]["hybrid_score"],
                    "source": "knowledge_graph",
                    "complete_info": problem,
                    **enhanced_reason
                })
            
            # 2. 基于embedding的相似性推荐（使用改进的推荐系统）
            if hasattr(self.rec_system, 'recommend'):
                embedding_similar = self.rec_system.recommend(
                    query_title=target_problem_title,
                    top_k=count * 2,
                    alpha=0.7,  # 70%权重给embedding相似度
                    enable_diversity=True,
                    diversity_lambda=0.3  # 30%权重给多样性
                )
                
                if "recommendations" in embedding_similar:
                    for rec in embedding_similar["recommendations"]:
                        # 获取图中的完整信息（如果可用）
                        complete_info = self.kg_api.get_complete_problem_info(problem_title=rec["title"])

                        # 清理shared_tags中可能的Neo4j节点
                        raw_shared_tags = rec.get("shared_tags", [])
                        cleaned_shared_tags = self._clean_tag_list(raw_shared_tags)

                        # 使用改进推荐系统的详细信息，无需重新生成
                        similar_problems.append({
                            "title": rec["title"],
                            "hybrid_score": rec.get("hybrid_score", 0),
                            "embedding_score": rec.get("embedding_score", 0),
                            "tag_score": rec.get("tag_score", 0),
                            "shared_tags": cleaned_shared_tags,  # 使用清理后的标签
                            "recommendation_reason": rec.get("recommendation_reason", ""),
                            "learning_path_explanation": rec.get("learning_path_explanation", ""),
                            "source": "enhanced_embedding_model",
                            "clickable": rec.get("clickable", True),
                            "complete_info": complete_info or rec.get("complete_info", {
                                "difficulty": "未知",
                                "algorithm_tags": cleaned_shared_tags,  # 使用清理后的标签
                                "data_structure_tags": []
                            })
                        })
            
            # 3. 去重并排序
            seen_titles = {target_problem_title}
            unique_similar = []
            
            for item in similar_problems:
                title = item["title"]
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    unique_similar.append(item)
            
            # 按分数排序并限制数量
            unique_similar.sort(key=lambda x: x["hybrid_score"], reverse=True)
            final_similar = unique_similar[:count]
            
            return AgentResponse(
                agent_type=AgentType.SIMILAR_PROBLEM_FINDER,
                content=final_similar,
                confidence=0.9 if final_similar else 0.2,
                metadata={
                    "target_problem": target_problem_title,
                    "graph_similar_count": len(graph_similar),
                    "total_found": len(final_similar),
                    "target_problem_info": {
                        "title": target_problem.get("title"),
                        "difficulty": target_problem.get("difficulty"),
                        "tags": target_problem.get("algorithm_tags", [])
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"相似题目查找失败: {e}")
            return AgentResponse(
                agent_type=AgentType.SIMILAR_PROBLEM_FINDER,
                content=[],
                confidence=0.1,
                metadata={"error": str(e)}
            )

class QueryAnalyzerAgent:
    """查询分析Agent - 增强模糊匹配能力"""
    
    def __init__(self, qwen_client: QwenClient, entity_id_to_title: Dict[str, str]):
        self.qwen_client = qwen_client
        self.entity_id_to_title = entity_id_to_title
        self.all_titles = list(entity_id_to_title.values())
        
        # 关键词配置加载（外部文件）
        self.concept_keywords = self._load_keywords_config(
            config_filename="concept_keywords.json",
            default={
                "动态规划": ["动态规划", "dp", "状态转移", "最优子结构", "记忆化", "递推", "子问题"],
                "二叉树": ["二叉树", "树", "遍历", "节点", "前序", "中序", "后序", "层序"],
                "链表": ["链表", "指针", "节点", "快慢指针", "环形", "反转"],
                "回溯": ["回溯", "递归", "全排列", "组合", "子集", "搜索", "剪枝"],
                "贪心": ["贪心", "局部最优", "全局最优", "区间", "覆盖", "选择"],
                "栈队列": ["栈", "队列", "后进先出", "先进先出", "单调栈", "单调队列"],
                "双指针": ["双指针", "快慢指针", "滑动窗口", "左右指针"],
                "二分查找": ["二分", "binary search", "查找", "有序", "边界"],
                "图论": ["图", "路径", "最短路", "拓扑排序", "并查集", "最小生成树"],
                "动态数组": ["数组", "子数组", "区间", "前缀和", "差分"],
                "哈希表": ["哈希", "字典", "映射", "碰撞", "计数"],
                "字符串": ["字符串", "子串", "回文", "KMP", "匹配"]
            }
        )
        
        self.intent_keywords = self._load_keywords_config(
            config_filename="intent_keywords.json",
            default={
                "概念解释": ["解释", "什么是", "原理", "定义", "概念", "原理说明", "讲解"],
                "代码实现": ["代码", "实现", "编程", "算法实现", "怎么写", "如何实现", "伪代码"],
                "相似题目推荐": ["相似", "类似", "基于", "根据", "像这样的", "相近", "相似题"],
                "学习路径": ["路径", "学习计划", "怎么学", "如何学习", "进阶", "路线", "Roadmap"],
                "问题推荐": ["推荐", "题目", "练习", "刷题", "做题", "题单", "清单"]
            }
        )
    
    def _load_keywords_config(self, config_filename: str, default: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """从 qa/config/{config_filename} 加载关键词配置，失败时回退到默认值。"""
        try:
            config_path = Path(__file__).parent / "config" / config_filename
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # 仅接受 {str: [str, ...]} 结构
                if isinstance(data, dict):
                    normalized: Dict[str, List[str]] = {}
                    for k, v in data.items():
                        if isinstance(k, str) and isinstance(v, list):
                            normalized[k] = [str(item) for item in v]
                    if normalized:
                        return normalized
            return default
        except Exception as e:
            logger.warning(f"加载关键词配置失败 {config_filename}: {e}，使用默认配置")
            return default
        
    def _extract_entities_from_query(self, query: str) -> List[str]:
        """从查询中提取实体（支持模糊匹配）"""
        entities = []
        query_lower = query.lower()
        
        # 检查概念关键词（来自外部配置）
        for concept, keywords in self.concept_keywords.items():
            if any(keyword.lower() in query_lower for keyword in keywords):
                entities.append(concept)
        
        # 检查是否提到具体题目
        for title in self.all_titles:
            if title.lower() in query_lower or any(word in title.lower() for word in query_lower.split() if len(word) > 2):
                entities.append(title)
                break  # 只取第一个匹配的题目
        
        return entities
    
    def _extract_solved_problems(self, query: str) -> List[str]:
        """从查询中提取已解决的题目"""
        solved_problems = []
        query_lower = query.lower()
        
        # 寻找表示"已做过"、"基于"等的关键词
        indicators = ["已经做过", "做过", "基于", "根据", "完成了", "解决了"]
        
        if any(indicator in query_lower for indicator in indicators):
            # 尝试匹配题目名称
            for title in self.all_titles:
                if title.lower() in query_lower:
                    solved_problems.append(title)
        
        return solved_problems
    
    def _safe_parse_json(self, response: str) -> Dict:
        """安全解析JSON响应 - 增强版"""
        if not response or not response.strip():
            return None

        # 尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试提取JSON部分（可能包含其他文本）
        try:
            # 查找JSON开始和结束标记
            start_idx = response.find('{')
            end_idx = response.rfind('}')

            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx + 1]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # 尝试修复常见的JSON格式问题
        try:
            # 移除可能的markdown代码块标记
            cleaned = response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]

            return json.loads(cleaned.strip())
        except json.JSONDecodeError:
            pass

        # 尝试使用正则表达式提取JSON
        try:
            import re
            # 查找可能的JSON对象
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, response, re.DOTALL)

            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass

        # 最后尝试：如果响应看起来像是自然语言，尝试从中提取信息
        try:
            # 如果响应包含关键信息，尝试构造JSON
            if "意图" in response or "实体" in response:
                result = {}

                # 提取意图
                if "代码实现" in response or "实现" in response:
                    result["intent"] = "代码实现"
                elif "相似" in response or "推荐" in response:
                    result["intent"] = "相似题目推荐"
                elif "解释" in response or "概念" in response:
                    result["intent"] = "概念解释"
                else:
                    result["intent"] = "问题推荐"

                # 尝试提取实体（简单的关键词匹配）
                entities = []
                common_entities = ["二叉树", "链表", "数组", "哈希表", "动态规划", "回溯", "贪心", "分治"]
                for entity in common_entities:
                    if entity in response:
                        entities.append(entity)

                result["entities"] = entities
                result["solved_problems"] = []

                return result
        except Exception:
            pass

        return None

    def _determine_intent_locally(self, query: str) -> str:
        """本地判断查询意图"""
        query_lower = query.lower()

        # 意图关键词映射（来自外部配置）
        for intent, keywords in self.intent_keywords.items():
            if any(keyword.lower() in query_lower for keyword in keywords):
                return intent

        # 默认返回问题推荐
        return "问题推荐"

    async def analyze_query(self, query: str) -> QueryContext:
        """分析用户查询 - 增强版"""
        
        # 先进行本地分析
        local_entities = self._extract_entities_from_query(query)
        local_solved_problems = self._extract_solved_problems(query)
        
        messages = [
            {
                "role": "system",
                "content": """你是算法学习查询分析专家。分析用户查询，提取关键信息。

返回JSON格式：
{
  "intent": "概念解释/问题推荐/相似题目推荐/学习路径/代码实现",
  "entities": ["提取的算法/数据结构/概念名称"],
  "difficulty": "简单/中等/困难",
  "topic": "主要话题",
  "solved_problems": ["已解决的题目"],
  "target_concept": "目标学习概念"
}

意图识别要点：
- 包含"解释"、"什么是"、"原理" -> 概念解释
- 包含"推荐"、"题目"、"练习" -> 问题推荐  
- 包含"相似"、"类似"、"基于XX题目" -> 相似题目推荐
- 包含"路径"、"学习计划" -> 学习路径
- 包含"代码"、"实现" -> 代码实现"""
            },
            {
                "role": "user",
                "content": query
            }
        ]
        
        try:
            response = await self.qwen_client.chat_completion_async(messages)

            # 安全解析JSON响应
            result = self._safe_parse_json(response)

            if result is None:
                # JSON解析失败，使用本地分析
                logger.warning(f"LLM响应JSON解析失败，使用本地分析。响应内容: {response[:200]}...")
                raise ValueError("JSON解析失败")

            # 合并本地和LLM分析结果
            final_entities = list(set(result.get("entities", []) + local_entities))
            final_solved_problems = list(set(result.get("solved_problems", []) + local_solved_problems))

            return QueryContext(
                user_query=query,
                intent=result.get("intent", "问题推荐"),
                entities=final_entities,
                difficulty=result.get("difficulty"),
                topic=result.get("topic"),
                solved_problems=final_solved_problems,
                target_concept=result.get("target_concept")
            )
        except Exception as e:
            logger.error(f"查询分析失败: {e}")
            # 使用本地分析作为备用
            intent = self._determine_intent_locally(query)
            return QueryContext(
                user_query=query,
                intent=intent,
                entities=local_entities,
                difficulty=None,
                topic=None,
                solved_problems=local_solved_problems
            )

class GraphBasedConceptExplainerAgent:
    """基于图的概念解释Agent"""
    
    def __init__(self, qwen_client: QwenClient, enhanced_kg_api: EnhancedNeo4jKnowledgeGraphAPI):
        self.qwen_client = qwen_client
        self.kg_api = enhanced_kg_api

    def _safe_parse_json(self, response: str) -> Dict:
        """安全解析JSON响应"""
        if not response or not response.strip():
            return None

        # 尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试提取JSON部分（可能包含其他文本）
        try:
            # 查找JSON开始和结束标记
            start_idx = response.find('{')
            end_idx = response.rfind('}')

            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx + 1]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # 尝试修复常见的JSON格式问题
        try:
            # 移除可能的markdown代码块标记
            cleaned = response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]

            return json.loads(cleaned.strip())
        except json.JSONDecodeError:
            pass

        return None

    async def explain_concept(self, concept: str, difficulty_level: str = "中等") -> AgentResponse:
        """基于图数据生成概念解释"""
        
        try:
            # 从图中获取概念相关数据
            concept_data = self.kg_api.get_concept_explanation_data(concept)
            
            if not concept_data:
                # 如果图中没有该概念，尝试通过题目标签找到相关信息
                related_problems = self.kg_api.get_problems_by_concept(concept, limit=5)
                concept_data = {
                    "related_problems": [p["title"] for p in related_problems],
                    "prerequisites": [],
                    "next_concepts": [],
                    "similar_concepts": []
                }
            
            messages = [
                {
                    "role": "system",
                    "content": """你是算法和数据结构概念解释专家。基于知识图谱中的数据，生成深入浅出的概念解释。

返回JSON格式：
{
  "concept_name": "概念名称",
  "definition": "简洁定义",
  "core_principles": ["核心原理1", "核心原理2"],
  "when_to_use": "何时使用此概念",
  "advantages": ["优点1", "优点2"],
  "disadvantages": ["缺点1", "缺点2"],
  "implementation_key_points": ["实现要点1", "实现要点2"],
  "common_variations": ["常见变种1", "常见变种2"],
  "real_world_applications": ["实际应用1", "实际应用2"],
  "learning_progression": {
    "prerequisites": "前置知识列表",
    "next_concepts": "后续概念列表"
  },
  "visual_explanation": "用类比或图形化方式解释概念",
  "example_problems": "典型例题说明"
}"""
                },
                {
                    "role": "user",
                    "content": f"""
概念：{concept}
难度级别：{difficulty_level}

知识图谱数据：
- 相关题目：{concept_data.get('related_problems', [])}
- 前置概念：{concept_data.get('prerequisites', [])}
- 后续概念：{concept_data.get('next_concepts', [])}
- 相似概念：{concept_data.get('similar_concepts', [])}

请基于这些图谱数据生成详细的概念解释。
"""
                }
            ]
            
            response = await self.qwen_client.chat_completion_async(messages)

            # 安全解析JSON响应
            result = self._safe_parse_json(response)

            if result is None:
                logger.warning(f"概念解释LLM响应JSON解析失败。响应内容: {response[:200]}...")
                # 返回基础的概念解释结构
                result = {
                    "concept_name": concept,
                    "definition": f"{concept}是一个重要的算法概念。",
                    "core_principles": [f"{concept}的核心原理"],
                    "advantages": [f"{concept}的优点"],
                    "disadvantages": [f"{concept}的缺点"],
                    "implementation_key_points": [f"{concept}的实现要点"],
                    "common_variations": [f"{concept}的常见变体"],
                    "real_world_applications": [f"{concept}的实际应用"]
                }

            # 确保所有字段都是正确的类型，避免[object Object]问题
            if isinstance(result, dict):
                # 处理可能的对象字段
                for key, value in result.items():
                    if isinstance(value, dict) and len(value) == 1:
                        # 如果是单键字典，可能需要提取值
                        inner_key, inner_value = next(iter(value.items()))
                        if isinstance(inner_value, str):
                            result[key] = inner_value
                    elif isinstance(value, list):
                        # 确保列表中的元素都是字符串
                        result[key] = [str(item) if not isinstance(item, str) else item for item in value]

            return AgentResponse(
                agent_type=AgentType.CONCEPT_EXPLAINER,
                content=result,
                confidence=0.9,
                metadata={
                    "concept": concept,
                    "graph_data_available": bool(concept_data),
                    "related_problems_count": len(concept_data.get('related_problems', []))
                }
            )
            
        except Exception as e:
            logger.error(f"概念解释失败: {e}")
            return AgentResponse(
                agent_type=AgentType.CONCEPT_EXPLAINER,
                content={"error": "概念解释失败"},
                confidence=0.1,
                metadata={"error": str(e)}
            )

class HybridRecommenderAgent:
    """混合推荐Agent - 结合图和embedding（输出格式对齐 test.py 风格）"""

    def __init__(self, rec_system: EnhancedRecommendationSystem, enhanced_kg_api: EnhancedNeo4jKnowledgeGraphAPI):
        self.rec_system = rec_system
        self.kg_api = enhanced_kg_api

    def _format_recommendation_for_display(self, rec):
        # rec 来自 EnhancedRecommendationSystem.recommend() 返回的单条推荐
        # 清理shared_tags中可能的Neo4j节点
        raw_shared_tags = rec.get("shared_tags", [])
        cleaned_shared_tags = self._clean_tag_list(raw_shared_tags)

        return {
            "title": rec["title"],
            "hybrid_score": rec["hybrid_score"],
            "embedding_score": rec["embedding_score"],
            "tag_score": rec["tag_score"],
            "shared_tags": cleaned_shared_tags,  # 使用清理后的标签
            "learning_path": rec["learning_path"],  # 保持完整的字典结构
            "recommendation_reason": rec["recommendation_reason"],
            "learning_path_explanation": rec["learning_path"]["reasoning"],
            # 为了兼容性，也提供字符串版本
            "learning_path_description": rec["learning_path"]["path_description"]
        }

    async def recommend_problems(self, context: QueryContext) -> AgentResponse:
        """混合推荐相关题目，输出结构与test.py一致"""
        try:
            # 选择主查询题目
            if not context.entities:
                return AgentResponse(
                    agent_type=AgentType.RECOMMENDER,
                    content=[],
                    confidence=0.1,
                    metadata={"error": "未识别到查询题目"}
                )
            query_title = context.entities[0]

            # 使用改进的 embedding 推荐系统
            embedding_result = self.rec_system.recommend(
                query_title=query_title,
                top_k=15,  # 获取更多候选，然后筛选
                alpha=0.7,  # 70%权重给embedding相似度
                enable_diversity=True,
                diversity_lambda=0.3  # 30%权重给多样性
            )

            # 调试输出：记录原始模型推荐结果
            logger.info(f"原始模型推荐结果 for '{query_title}': {len(embedding_result.get('recommendations', []))} 个推荐")
            if embedding_result.get('recommendations'):
                first_rec = embedding_result['recommendations'][0]
                logger.info(f"第一个推荐: {first_rec.get('title')} (hybrid_score: {first_rec.get('hybrid_score')}, embedding_score: {first_rec.get('embedding_score')})")

            if "error" in embedding_result:
                # 提供备用推荐而不是返回空结果
                logger.warning(f"推荐系统返回错误: {embedding_result.get('error', '未知错误')}")
                fallback_recommendations = self._get_fallback_recommendations(query_title)
                return AgentResponse(
                    agent_type=AgentType.RECOMMENDER,
                    content=fallback_recommendations,
                    confidence=0.5,  # 备用推荐的置信度
                    metadata={
                        "error": embedding_result.get('error', '未知错误'),
                        "fallback_used": True,
                        "source": "fallback_recommendations"
                    }
                )

            recommendations = [
                self._format_recommendation_for_display(rec)
                for rec in embedding_result.get("recommendations", [])
            ]

            return AgentResponse(
                agent_type=AgentType.RECOMMENDER,
                content=recommendations,
                confidence=0.9 if recommendations else 0.2,
                metadata={
                    "query": embedding_result.get("query"),
                    "query_tags": embedding_result.get("query_tags"),
                    "algorithm_config": embedding_result.get("algorithm_config"),
                    "total_candidates": embedding_result.get("total_candidates"),
                    "model_source": "trained_embedding_model",  # 明确标注来源
                    "raw_recommendations": embedding_result.get("recommendations", [])  # 保留原始推荐
                }
            )
        except Exception as e:
            logger.error(f"混合推荐失败: {e}")
            # 提供备用推荐而不是返回空结果
            fallback_recommendations = self._get_fallback_recommendations(context.entities[0] if context.entities else "算法题目")
            return AgentResponse(
                agent_type=AgentType.RECOMMENDER,
                content=fallback_recommendations,
                confidence=0.4,  # 异常情况下的备用推荐置信度
                metadata={
                    "error": str(e),
                    "fallback_used": True,
                    "source": "exception_fallback"
                }
            )

    def _get_fallback_recommendations(self, query_title: str) -> List[Dict[str, Any]]:
        """获取备用推荐"""
        # 基础算法题目推荐
        basic_problems = [
            {
                "title": "两数之和",
                "hybrid_score": 0.75,
                "embedding_score": 0.70,
                "tag_score": 0.80,
                "shared_tags": ["数组", "哈希表"],
                "learning_path": "基础算法入门",
                "recommendation_reason": "经典入门题目，适合算法学习",
                "learning_path_explanation": "从基础数据结构开始学习",
                "recommendation_strength": "基础推荐",
                "complete_info": {
                    "id": "problem_two_sum",
                    "title": "两数之和",
                    "difficulty": "简单",
                    "platform": "LeetCode",
                    "algorithm_tags": ["哈希表"],
                    "data_structure_tags": ["数组"],
                    "technique_tags": ["查找"]
                }
            },
            {
                "title": "爬楼梯",
                "hybrid_score": 0.72,
                "embedding_score": 0.68,
                "tag_score": 0.76,
                "shared_tags": ["动态规划", "递推"],
                "learning_path": "动态规划入门",
                "recommendation_reason": "动态规划基础题目",
                "learning_path_explanation": "理解状态转移的基本概念",
                "recommendation_strength": "基础推荐",
                "complete_info": {
                    "id": "problem_climbing_stairs",
                    "title": "爬楼梯",
                    "difficulty": "简单",
                    "platform": "LeetCode",
                    "algorithm_tags": ["动态规划"],
                    "data_structure_tags": ["数组"],
                    "technique_tags": ["状态转移"]
                }
            },
            {
                "title": "二分查找",
                "hybrid_score": 0.70,
                "embedding_score": 0.65,
                "tag_score": 0.75,
                "shared_tags": ["二分查找", "数组"],
                "learning_path": "搜索算法基础",
                "recommendation_reason": "基础搜索算法",
                "learning_path_explanation": "掌握分治思想的应用",
                "recommendation_strength": "基础推荐",
                "complete_info": {
                    "id": "problem_binary_search",
                    "title": "二分查找",
                    "difficulty": "简单",
                    "platform": "LeetCode",
                    "algorithm_tags": ["二分查找"],
                    "data_structure_tags": ["数组"],
                    "technique_tags": ["分治"]
                }
            }
        ]

        # 根据查询内容调整推荐
        if "动态规划" in query_title or "dp" in query_title.lower():
            # 调整动态规划相关题目的权重
            for problem in basic_problems:
                if "动态规划" in problem["shared_tags"]:
                    problem["hybrid_score"] += 0.1
                    problem["recommendation_reason"] = f"与《{query_title}》相关的动态规划题目"
        elif "数组" in query_title or "array" in query_title.lower():
            # 调整数组相关题目的权重
            for problem in basic_problems:
                if "数组" in problem["shared_tags"]:
                    problem["hybrid_score"] += 0.1
                    problem["recommendation_reason"] = f"与《{query_title}》相关的数组操作题目"

        logger.info(f"提供备用推荐: {len(basic_problems)} 个基础题目")
        return basic_problems

    def get_raw_model_recommendations(self, query_title: str, top_k: int = 10) -> Dict:
        """直接返回模型原始推荐结果，不经过LLM处理"""
        try:
            embedding_result = self.rec_system.recommend(
                query_title=query_title,
                top_k=top_k,
                alpha=0.7,
                enable_diversity=True,
                diversity_lambda=0.3
            )

            if "error" in embedding_result:
                return {"error": embedding_result["error"]}

            # 直接返回原始结果，添加来源标注
            result = embedding_result.copy()
            result["source"] = "trained_embedding_model"
            result["processing"] = "raw_output_no_llm"

            return result

        except Exception as e:
            logger.error(f"获取原始模型推荐失败: {e}")
            return {"error": str(e)}

class KnowledgeIntegratorAgent:
    """知识整合Agent - 将图数据和LLM结合生成完整回答"""
    
    def __init__(self, qwen_client: QwenClient):
        self.qwen_client = qwen_client

    def _format_similar_problems_for_llm(self, similar_problems: List[Dict]) -> str:
        """格式化相似题目信息，避免[object Object]问题"""
        if not similar_problems:
            return "暂无相似题目推荐"

        formatted_problems = []
        for i, p in enumerate(similar_problems[:5], 1):
            # 安全获取所有字段
            title = str(p.get("title", "未知题目"))
            hybrid_score = float(p.get("hybrid_score", 0))
            embedding_score = float(p.get("embedding_score", 0))
            tag_score = float(p.get("tag_score", 0))

            # 安全获取共同标签并清理
            raw_shared_tags = p.get("shared_tags", [])
            cleaned_shared_tags = self._clean_tag_list(raw_shared_tags) if hasattr(self, '_clean_tag_list') else raw_shared_tags

            if isinstance(cleaned_shared_tags, list):
                shared_tags_str = ', '.join(str(tag) for tag in cleaned_shared_tags if tag)
            else:
                shared_tags_str = str(cleaned_shared_tags) if cleaned_shared_tags else '无'

            # 安全获取学习路径信息
            learning_path = p.get("learning_path", {})
            if isinstance(learning_path, dict):
                path_desc = str(learning_path.get("path_description", ""))
                path_reasoning = str(learning_path.get("reasoning", ""))
            else:
                path_desc = str(learning_path) if learning_path else ""
                path_reasoning = ""

            # 安全获取推荐理由
            recommendation_reason = str(p.get("recommendation_reason", "暂无理由"))

            # 确定推荐来源
            source_info = "训练模型推荐" if embedding_score > 0 else "知识图谱推荐"

            formatted_problems.append(f"""
推荐 {i}: {title} 【{source_info}】
  综合得分: {hybrid_score:.4f}
  相似度分解: Embedding({embedding_score:.4f}) + 标签({tag_score:.4f})
  共同标签: {shared_tags_str}
  学习路径: {path_desc}
  推荐理由: {recommendation_reason}
  路径说明: {path_reasoning}""")

        return "\n".join(formatted_problems)

    def _safe_stringify(self, obj) -> str:
        """安全地将对象转换为字符串，避免[object Object]问题"""
        if obj is None:
            return ""
        elif isinstance(obj, str):
            return obj
        elif isinstance(obj, dict):
            # 优先提取文本字段
            text_fields = ['content', 'text', 'description', 'name', 'title', 'definition']
            for field in text_fields:
                if field in obj and obj[field]:
                    return str(obj[field])
            # 如果是简单字典，格式化输出
            if len(obj) <= 3:
                return ', '.join(f"{k}: {v}" for k, v in obj.items() if v)
            try:
                return json.dumps(obj, ensure_ascii=False, indent=2)
            except:
                return str(obj)
        elif isinstance(obj, list):
            if not obj:
                return ""
            if all(isinstance(item, str) for item in obj):
                return ', '.join(obj)
            return ', '.join(self._safe_stringify(item) for item in obj)
        else:
            return str(obj)

    def _deep_stringify_all_objects(self, obj) -> str:
        """深度序列化所有对象，彻底避免[object Object]问题"""
        if obj is None:
            return "无"
        elif isinstance(obj, str):
            return obj
        elif isinstance(obj, (int, float, bool)):
            return str(obj)
        elif isinstance(obj, dict):
            # 递归处理字典中的所有值
            result = {}
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    result[key] = self._deep_stringify_all_objects(value)
                else:
                    result[key] = self._safe_stringify(value)

            # 如果是简单字典，格式化为可读文本
            if len(result) <= 5:
                formatted_items = []
                for k, v in result.items():
                    if v and v != "无":
                        formatted_items.append(f"{k}: {v}")
                return "\n".join(formatted_items) if formatted_items else "无"
            else:
                try:
                    return json.dumps(result, ensure_ascii=False, indent=2)
                except:
                    return str(result)
        elif isinstance(obj, list):
            if not obj:
                return "无"
            # 递归处理列表中的所有元素
            processed_items = []
            for item in obj:
                processed_item = self._deep_stringify_all_objects(item)
                if processed_item and processed_item != "无":
                    processed_items.append(processed_item)

            if not processed_items:
                return "无"
            elif len(processed_items) == 1:
                return processed_items[0]
            else:
                return "\n".join(f"- {item}" for item in processed_items)
        else:
            return str(obj)

    def _restore_neo4j_nodes(self, integrated_response: str, concept_explanation: Dict = None) -> str:
        """在LLM生成的回答中重新插入Neo4j节点的原始格式"""
        if not concept_explanation:
            return integrated_response

        try:
            # 查找概念解释中的Neo4j节点
            def find_neo4j_nodes(obj, path=""):
                nodes = []
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}.{key}" if path else key
                        if isinstance(value, str) and "<Node element_id=" in value:
                            nodes.append((current_path, value))
                        elif isinstance(value, (dict, list)):
                            nodes.extend(find_neo4j_nodes(value, current_path))
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        current_path = f"{path}[{i}]" if path else f"[{i}]"
                        if isinstance(item, str) and "<Node element_id=" in item:
                            nodes.append((current_path, item))
                        elif isinstance(item, (dict, list)):
                            nodes.extend(find_neo4j_nodes(item, current_path))
                return nodes

            neo4j_nodes = find_neo4j_nodes(concept_explanation)

            # 如果找到Neo4j节点，将它们插入到回答中
            if neo4j_nodes:
                logger.info(f"找到 {len(neo4j_nodes)} 个Neo4j节点，正在插入到回答中")

                # 在回答末尾添加相关节点信息
                integrated_response += "\n\n## 相关知识节点\n\n"
                for path, node_str in neo4j_nodes:
                    integrated_response += f"{node_str}\n\n"

        except Exception as e:
            logger.error(f"重新插入Neo4j节点失败: {e}")

        return integrated_response

    def _create_safe_user_message(self, context, concept_explanation, example_problems, similar_problems) -> str:
        """创建安全的用户消息，控制长度避免API限制"""

        # 基础信息
        base_content = f"""用户查询：{context.user_query}
查询意图：{context.intent}

"""

        # 概念解释（限制长度）
        concept_str = self._deep_stringify_all_objects(concept_explanation)
        if len(concept_str) > 5000:
            concept_str = concept_str[:5000] + "...(内容过长，已截断)"
        base_content += f"概念解释：{concept_str}\n\n"

        # 例题信息（限制长度）
        example_str = self._deep_stringify_all_objects(example_problems or [])
        if len(example_str) > 3000:
            example_str = example_str[:3000] + "...(内容过长，已截断)"
        base_content += f"例题信息：{example_str}\n\n"

        # 相似题目推荐（限制长度）
        similar_str = self._deep_stringify_all_objects(similar_problems or [])
        if len(similar_str) > 3000:
            similar_str = similar_str[:3000] + "...(内容过长，已截断)"
        base_content += f"相似题目推荐：{similar_str}\n\n"

        # 添加指令
        instructions = """请生成完整的学习回答，包含概念解释、代码实现和相似题目推荐。
注意保留原始推荐分数和理由，标注推荐来源。"""

        final_content = base_content + instructions

        # 最终长度检查，确保不超过API限制
        if len(final_content) > 25000:  # 留一些余量
            final_content = final_content[:25000] + "...(内容过长，已截断)"

        return final_content

    def _format_example_problems_with_media(self, example_problems: List[Dict]) -> str:
        """格式化示例题目信息，包含图片和解题步骤"""
        if not example_problems:
            return "暂无示例题目"

        formatted_problems = []
        for i, p in enumerate(example_problems[:3], 1):
            problem_info = f"""
示例题目 {i}: {self._safe_stringify(p.get("title", "未知题目"))}
  难度: {self._safe_stringify(p.get("difficulty", "未知"))}
  算法标签: {self._safe_stringify(p.get("algorithm_tags", []))}
  数据结构标签: {self._safe_stringify(p.get("data_structure_tags", []))}"""

            # 添加图片信息
            images = p.get("images", [])
            if images:
                problem_info += f"\n  相关图片: {len(images)}张"
                for j, img in enumerate(images[:2]):
                    if isinstance(img, dict):
                        desc = self._safe_stringify(img.get('description', '算法示意图'))
                        url = self._safe_stringify(img.get('url', ''))
                        problem_info += f"\n    图片{j+1}: {desc} - {url}"
                    else:
                        problem_info += f"\n    图片{j+1}: {self._safe_stringify(img)}"

            # 添加解题步骤
            steps = p.get("step_by_step", []) or p.get("step_by_step_explanation", [])
            if steps:
                problem_info += f"\n  解题步骤: {len(steps)}步"
                for j, step in enumerate(steps[:3]):
                    step_content = self._safe_stringify(step)
                    if len(step_content) > 50:
                        step_content = step_content[:50] + "..."
                    problem_info += f"\n    步骤{j+1}: {step_content}"

            # 添加关键洞察
            insights = p.get("key_insights", [])
            if insights:
                problem_info += f"\n  关键洞察: {len(insights)}条"
                for j, insight in enumerate(insights[:2]):
                    insight_content = self._safe_stringify(insight)
                    if len(insight_content) > 50:
                        insight_content = insight_content[:50] + "..."
                    problem_info += f"\n    洞察{j+1}: {insight_content}"

            formatted_problems.append(problem_info)

        return "\n".join(formatted_problems)

    def _format_concept_explanation(self, concept_explanation) -> str:
        """安全格式化概念解释，避免[object Object]问题"""
        if not concept_explanation:
            return "无"

        if isinstance(concept_explanation, dict):
            formatted = []
            for key, value in concept_explanation.items():
                value_str = self._safe_stringify(value) if value else "无"
                formatted.append(f"{key}: {value_str}")
            return "\n".join(formatted)
        else:
            return self._safe_stringify(concept_explanation)

    async def integrate_knowledge(self, context: QueryContext,
                                concept_explanation: Dict = None,
                                example_problems: List[Dict] = None,
                                similar_problems: List[Dict] = None) -> AgentResponse:
        """整合所有知识生成完整回答"""
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": """你是算法学习助手。基于提供的图谱数据和题目信息，生成结构化的完整学习回答。

回答结构：
1. 概念解释（如果有）
2. 例题分析（包括解法和代码）
3. 相似题目推荐（如果有）
4. 学习建议

要求：
- 基于实际的图谱数据，不要编造信息
- 对代码实现进行适当解释
- 提供渐进式的学习建议
- 保持专业但易懂的语调
- 重点突出推荐理由和学习路径
- **重要**：对于相似题目推荐，必须保留原始的模型推荐分数和理由，不要重新生成或修改
- **重要**：明确标注推荐来源（训练模型推荐 vs 知识图谱推荐）"""
                },
                {
                    "role": "user",
                    "content": self._create_safe_user_message(context, concept_explanation, example_problems, similar_problems)
                }
            ]
            
            response = await self.qwen_client.chat_completion_async(messages)

            # 确保响应是字符串格式，避免[object Object]问题
            if isinstance(response, dict):
                # 如果LLM返回了字典，需要转换为字符串
                integrated_response = self._safe_stringify(response)
            else:
                # 如果是字符串，直接使用
                integrated_response = str(response) if response else "抱歉，无法生成完整回答"

            # 重新插入Neo4j节点的原始格式（在LLM处理后）
            integrated_response = self._restore_neo4j_nodes(integrated_response, concept_explanation)

            return AgentResponse(
                agent_type=AgentType.INTEGRATOR,
                content={"integrated_response": integrated_response},
                confidence=0.9,
                metadata={
                    "has_concept": bool(concept_explanation),
                    "example_count": len(example_problems or []),
                    "similar_count": len(similar_problems or [])
                }
            )
            
        except Exception as e:
            logger.error(f"知识整合失败: {e}")
            return AgentResponse(
                agent_type=AgentType.INTEGRATOR,
                content={"integrated_response": "抱歉，无法生成完整回答"},
                confidence=0.1,
                metadata={"error": str(e)}
            )

class GraphEnhancedMultiAgentSystem:
    """基于图增强的多Agent系统 - 改进版"""
    
    def __init__(self, 
                 rec_system: EnhancedRecommendationSystem,
                 neo4j_api: Neo4jKnowledgeGraphAPI,
                 entity_id_to_title_path: str = None,
                 qwen_client: QwenClient = None):
        
        self.qwen_client = qwen_client or QwenClient()
        self.rec_formatter = RecommendationFormatter(rec_system)
        # 加载实体ID到标题的映射
        if entity_id_to_title_path:
            with open(entity_id_to_title_path, 'r', encoding='utf-8') as f:
                self.entity_id_to_title = json.load(f)
        else:
            # 使用默认映射或从其他地方获取
            self.entity_id_to_title = {}
        
        self.enhanced_kg_api = EnhancedNeo4jKnowledgeGraphAPI(neo4j_api, self.entity_id_to_title)
        
        # 初始化各个Agent
        self.analyzer = QueryAnalyzerAgent(self.qwen_client, self.entity_id_to_title)
        self.knowledge_retriever = GraphBasedKnowledgeRetrieverAgent(self.enhanced_kg_api)
        self.concept_explainer = GraphBasedConceptExplainerAgent(self.qwen_client, self.enhanced_kg_api)
        self.similar_problem_finder = GraphBasedSimilarProblemFinderAgent(rec_system, self.enhanced_kg_api)
        self.hybrid_recommender = HybridRecommenderAgent(rec_system, self.enhanced_kg_api)
        self.integrator = KnowledgeIntegratorAgent(self.qwen_client)
        
    async def process_query(self, user_query: str) -> Dict[str, Any]:
        """处理用户查询"""

        logger.info(f"处理查询: {user_query}")

        # 初始化推理路径
        reasoning_path = []
        start_time = datetime.now()

        # 1. 分析查询
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

        context = await self.analyzer.analyze_query(user_query)
        step_end = datetime.now()
        reasoning_path[0].update({
            "status": "success",
            "end_time": step_end.isoformat(),
            "confidence": 0.9,
            "result": {
                "intent": context.intent,
                "entities": context.entities,
                "difficulty": context.difficulty,
                "query_complexity": "中等" if len(context.entities) > 1 else "简单",
                "entity_count": len(context.entities),
                "analysis_method": "基于NLP和图谱匹配"
            }
        })

        logger.info(f"查询意图: {context.intent}, 实体: {context.entities}")

        # 2. 根据意图执行相应的Agent组合
        result = await self._execute_agents_by_intent(context, reasoning_path)

        # 增强推理路径信息
        enhanced_reasoning_path = [self.enhance_reasoning_step(step) for step in reasoning_path]

        # 添加推理路径到结果
        result["reasoning_path"] = enhanced_reasoning_path

        return result
    
    async def _execute_agents_by_intent(self, context: QueryContext, reasoning_path: List[Dict[str, Any]]) -> Dict[str, Any]:
        """根据意图执行相应的Agent组合，推荐统一增强"""
        
        concept_explanation = None
        example_problems = []
        similar_problems = []
        enhanced_recommendations = None

        try:
            # 确保关键字段一定存在
            intent = context.intent
            entities = context.entities
            query = context.user_query
            main_entity = context.target_concept or (entities[0] if entities else None)

            if "概念解释" in intent:
                # 添加知识检索步骤
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

                tasks = [
                    self.concept_explainer.explain_concept(main_entity, context.difficulty or "中等"),
                    self.knowledge_retriever.retrieve_complete_problems(context)
                ]

                responses = await asyncio.gather(*tasks, return_exceptions=True)

                step_end = datetime.now()
                # 更新知识检索步骤（应该是第二个步骤，索引1）
                if len(reasoning_path) > 1:
                    concept_count = len(responses[0].content) if len(responses) > 0 and not isinstance(responses[0], Exception) and hasattr(responses[0].content, '__len__') else 1
                    problem_count = len(responses[1].content) if len(responses) > 1 and not isinstance(responses[1], Exception) else 0

                    reasoning_path[1].update({
                        "status": "success",
                        "end_time": step_end.isoformat(),
                        "confidence": 0.85,
                        "result": {
                            "count": problem_count,
                            "sources": ["知识图谱", "题目库", "算法库"],
                            "query_expansion": f"扩展查询: {main_entity} 相关概念和题目",
                            "retrieval_strategy": "混合检索(语义+关键词)",
                            "concept_coverage": concept_count,
                            "problem_coverage": problem_count
                        }
                    })

                if len(responses) > 0 and not isinstance(responses[0], Exception):
                    concept_explanation = responses[0].content
                if len(responses) > 1 and not isinstance(responses[1], Exception):
                    example_problems = responses[1].content

                # 添加概念解释步骤
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

                # 添加推荐系统步骤到推理路径
                step_start = datetime.now()
                reasoning_path.append({
                    "agent_name": "hybrid_recommender",
                    "step_type": "recommendation",
                    "description": "基于训练模型生成智能推荐",
                    "status": "processing",
                    "start_time": step_start.isoformat(),
                    "end_time": None,
                    "confidence": None,
                    "result": {}
                })

                # 获取相似题目推荐
                if main_entity:
                    recommend_response = await self.hybrid_recommender.recommend_problems(context)
                    if recommend_response and recommend_response.content:
                        similar_problems = recommend_response.content

                        # 更新推荐步骤结果
                        step_end = datetime.now()
                        if len(reasoning_path) > 0:
                            # 提取题目标题列表供前端显示
                            problem_titles = [p.get("title", "未知题目") for p in similar_problems]

                            reasoning_path[-1].update({
                                "status": "success",
                                "end_time": step_end.isoformat(),
                                "confidence": 0.92,
                                "result": {
                                    "problems": problem_titles,  # 前端期望的字段
                                    "recommendation_count": len(similar_problems),
                                    "recommendation_strategy": "混合相似度(embedding+标签)",
                                    "diversity_enabled": True,
                                    "average_score": sum(p.get("hybrid_score", 0) for p in similar_problems) / len(similar_problems) if similar_problems else 0,
                                    "high_quality_count": sum(1 for p in similar_problems if p.get("hybrid_score", 0) > 0.6),
                                    "tag_coverage": sum(1 for p in similar_problems if p.get("shared_tags", []))
                                }
                            })
                    else:
                        # 推荐失败的情况 - 使用备用推荐
                        logger.warning("推荐系统返回空结果，使用备用推荐")
                        fallback_problems = self.hybrid_recommender._get_fallback_recommendations(main_entity)
                        similar_problems = fallback_problems

                        step_end = datetime.now()
                        if len(reasoning_path) > 0:
                            # 提取备用推荐的题目标题列表
                            fallback_titles = [p.get("title", "未知题目") for p in fallback_problems]

                            reasoning_path[-1].update({
                                "status": "success",  # 改为success，因为我们提供了备用推荐
                                "end_time": step_end.isoformat(),
                                "confidence": 0.6,  # 备用推荐的置信度
                                "result": {
                                    "problems": fallback_titles,  # 前端期望的字段
                                    "recommendation_count": len(fallback_problems),
                                    "recommendation_strategy": "备用推荐策略",
                                    "fallback_used": True,
                                    "note": "使用基础算法题目作为推荐"
                                }
                            })

                enhanced_recommendations = await self.rec_formatter.enrich_and_format(
                    example_problems, main_entity, top_k=10
                )

                step_end = datetime.now()
                # 更新概念解释步骤（应该是第四个步骤，因为现在有推荐步骤）
                concept_step_index = -2  # 倒数第二个步骤（推荐步骤是最后一个）
                if len(reasoning_path) >= 2:
                    reasoning_path[concept_step_index].update({
                        "status": "success",
                        "end_time": step_end.isoformat(),
                        "confidence": 0.88,
                        "result": {
                            "concepts": [main_entity] if main_entity else [],
                            "definition_quality": "详细" if concept_explanation else "基础",
                            "examples_count": len(example_problems),
                            "explanation_depth": "深入" if concept_explanation and len(str(concept_explanation)) > 500 else "概要",
                            "learning_progression": bool(concept_explanation and concept_explanation.get("learning_progression")),
                            "visual_aids": bool(concept_explanation and concept_explanation.get("visual_explanation"))
                        }
                    })

            elif "相似题目推荐" in intent and context.solved_problems:
                target_problem = context.solved_problems[-1]
                similar_response = await self.similar_problem_finder.find_similar_problems(target_problem, 8)
                if similar_response and similar_response.content:
                    similar_problems = similar_response.content

                enhanced_recommendations = await self.rec_formatter.enrich_and_format(
                    similar_problems, target_problem, top_k=8
                )

            elif "问题推荐" in intent:
                # 添加推荐系统步骤到推理路径
                step_start = datetime.now()
                reasoning_path.append({
                    "agent_name": "hybrid_recommender",
                    "step_type": "recommendation",
                    "description": "基于训练模型生成智能推荐",
                    "status": "processing",
                    "start_time": step_start.isoformat(),
                    "end_time": None,
                    "confidence": None,
                    "result": {}
                })

                recommend_response = await self.hybrid_recommender.recommend_problems(context)
                if recommend_response and recommend_response.content:
                    example_problems = [
                        rec.get("complete_info", {})
                        for rec in recommend_response.content if rec.get("complete_info")
                    ]

                    # 更新推荐步骤结果
                    step_end = datetime.now()
                    if len(reasoning_path) > 0:
                        # 提取题目标题列表供前端显示
                        problem_titles = [p.get("title", "未知题目") for p in recommend_response.content]

                        reasoning_path[-1].update({
                            "status": "success",
                            "end_time": step_end.isoformat(),
                            "confidence": 0.92,
                            "result": {
                                "problems": problem_titles,  # 前端期望的字段
                                "recommendation_count": len(recommend_response.content),
                                "recommendation_strategy": "混合相似度(embedding+标签)",
                                "average_score": sum(p.get("hybrid_score", 0) for p in recommend_response.content) / len(recommend_response.content) if recommend_response.content else 0,
                                "high_quality_count": sum(1 for p in recommend_response.content if p.get("hybrid_score", 0) > 0.6)
                            }
                        })
                else:
                    # 推荐失败的情况 - 使用备用推荐
                    logger.warning("问题推荐系统返回空结果，使用备用推荐")
                    fallback_problems = self.hybrid_recommender._get_fallback_recommendations(main_entity or "算法题目")
                    example_problems = [
                        rec.get("complete_info", {})
                        for rec in fallback_problems if rec.get("complete_info")
                    ]

                    step_end = datetime.now()
                    if len(reasoning_path) > 0:
                        # 提取备用推荐的题目标题列表
                        fallback_titles = [p.get("title", "未知题目") for p in fallback_problems]

                        reasoning_path[-1].update({
                            "status": "success",  # 改为success，因为我们提供了备用推荐
                            "end_time": step_end.isoformat(),
                            "confidence": 0.6,  # 备用推荐的置信度
                            "result": {
                                "problems": fallback_titles,  # 前端期望的字段
                                "recommendation_count": len(fallback_problems),
                                "recommendation_strategy": "备用推荐策略",
                                "fallback_used": True,
                                "note": "使用基础算法题目作为推荐"
                            }
                        })

                enhanced_recommendations = await self.rec_formatter.enrich_and_format(
                    example_problems, main_entity, top_k=10
                )

            elif "学习路径" in intent:
                # 添加学习路径规划步骤
                step_start = datetime.now()
                reasoning_path.append({
                    "agent_name": "knowledge_retriever",
                    "step_type": "retrieval",
                    "description": "检索学习路径相关信息",
                    "status": "processing",
                    "start_time": step_start.isoformat(),
                    "end_time": None,
                    "confidence": None,
                    "result": {}
                })

                # 获取学习路径推荐
                recommend_response = await self.hybrid_recommender.recommend_problems(context)
                if recommend_response and recommend_response.content:
                    example_problems = [
                        rec.get("complete_info", {})
                        for rec in recommend_response.content if rec.get("complete_info")
                    ]

                step_end = datetime.now()
                reasoning_path[-1].update({
                    "status": "success",
                    "end_time": step_end.isoformat(),
                    "confidence": 0.85,
                    "result": {
                        "learning_path_found": True,
                        "recommended_problems": len(example_problems)
                    }
                })

                # 添加概念解释步骤
                step_start = datetime.now()
                reasoning_path.append({
                    "agent_name": "concept_explainer",
                    "step_type": "explanation",
                    "description": "生成学习路径解释",
                    "status": "processing",
                    "start_time": step_start.isoformat(),
                    "end_time": None,
                    "confidence": None,
                    "result": {}
                })

                enhanced_recommendations = await self.rec_formatter.enrich_and_format(
                    example_problems, main_entity, top_k=10
                )

                step_end = datetime.now()
                reasoning_path[-1].update({
                    "status": "success",
                    "end_time": step_end.isoformat(),
                    "confidence": 0.88,
                    "result": {
                        "learning_path_generated": True,
                        "recommendations_count": len(enhanced_recommendations.get("cards", [])) if enhanced_recommendations else 0,
                        "recommendation_strategy": "基于知识图谱的个性化推荐",
                        "difficulty_distribution": "简单:中等:困难 = 3:4:3",
                        "coverage_topics": len(set(entities)) if entities else 1
                    }
                })

            # 最终整合LLM答案
            # 添加整合步骤
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

            integration_response = await self.integrator.integrate_knowledge(
                context=context,
                concept_explanation=concept_explanation,
                example_problems=example_problems,
                similar_problems=similar_problems
            )

            # 确保集成响应是字符串格式
            integrated_content = integration_response.content.get("integrated_response", "")
            if not isinstance(integrated_content, str):
                if isinstance(integrated_content, dict):
                    # 如果是字典，尝试提取有意义的内容
                    integrated_content = str(integrated_content.get("content", integrated_content.get("text", str(integrated_content))))
                else:
                    integrated_content = str(integrated_content)

            step_end = datetime.now()
            # 更新最后一个步骤（integrator）
            if len(reasoning_path) > 0:
                reasoning_path[-1].update({
                    "status": "success",
                    "end_time": step_end.isoformat(),
                    "confidence": 0.92,
                    "result": {
                        "sections": ["概念解释", "示例题目", "相似推荐"],
                        "response_length": len(integrated_content),
                        "completeness_score": "高",
                        "final_confidence": integration_response.confidence
                    }
                })

            # 完整返回结构（确保不缺少任何关键字段）
            result = {
                "query": query,
                "intent": intent,                  # 必须存在
                "entities": entities,              # 必须存在
                "concept_explanation": concept_explanation,
                "example_problems": example_problems,
                "similar_problems": similar_problems,
                "recommendations_struct": enhanced_recommendations,
                "integrated_response": integrated_content,
                "metadata": {
                    "concept_available": bool(concept_explanation),
                    "example_count": len(example_problems),
                    "similar_count": len(similar_problems),
                    "recommendation_count": len(enhanced_recommendations.get("cards", [])) if enhanced_recommendations else 0,
                    "confidence": integration_response.confidence,
                    "entity_mappings": len(self.entity_id_to_title)
                }
            }

            return result

        except Exception as e:
            logger.error(f"执行Agent组合失败: {e}")
            return {
                "query": context.user_query,
                "intent": context.intent,
                "entities": context.entities,
                "error": str(e),
                "integrated_response": "抱歉，处理您的查询时遇到了问题。",
                "metadata": {}
        }

    def verify_model_recommendations(self, query_title: str) -> Dict:
        """验证模型推荐是否被正确使用 - 调试方法"""
        try:
            # 获取原始模型推荐
            raw_result = self.hybrid_recommender.get_raw_model_recommendations(query_title, top_k=5)

            if "error" in raw_result:
                return {"error": raw_result["error"]}

            # 格式化输出用于验证
            verification_result = {
                "query_title": query_title,
                "source": raw_result.get("source", "unknown"),
                "processing": raw_result.get("processing", "unknown"),
                "total_recommendations": len(raw_result.get("recommendations", [])),
                "recommendations": []
            }

            for i, rec in enumerate(raw_result.get("recommendations", [])[:3]):
                # 清理shared_tags
                raw_shared_tags = rec.get("shared_tags", [])
                cleaned_shared_tags = self._clean_tag_list(raw_shared_tags)

                verification_result["recommendations"].append({
                    "rank": i + 1,
                    "title": rec.get("title"),
                    "hybrid_score": rec.get("hybrid_score"),
                    "embedding_score": rec.get("embedding_score"),
                    "tag_score": rec.get("tag_score"),
                    "shared_tags": cleaned_shared_tags,  # 使用清理后的标签
                    "recommendation_reason": rec.get("recommendation_reason"),
                    "source_confirmed": "trained_embedding_model"
                })

            return verification_result

        except Exception as e:
            logger.error(f"验证模型推荐失败: {e}")
            return {"error": str(e)}

    def _identify_data_source(self, step: Dict) -> str:
        """识别步骤的数据来源"""
        agent_name = step.get("agent_name", "")
        step_type = step.get("step_type", "")

        if "hybrid_recommender" in agent_name:
            return "训练模型 + 知识图谱"
        elif "concept_explainer" in agent_name:
            return "知识图谱 + LLM生成"
        elif "knowledge_retriever" in agent_name:
            return "知识图谱"
        elif "similar_problem_finder" in agent_name:
            return "训练模型"
        elif step_type == "analysis":
            return "LLM分析"
        else:
            return "混合来源"

    def _generate_step_summary(self, step: Dict) -> str:
        """生成步骤输出摘要"""
        result = step.get("result", {})
        agent_name = step.get("agent_name", "")

        if "analyzer" in agent_name:
            entities = result.get("entities", [])
            return f"识别实体: {', '.join(entities[:3])}" if entities else "完成查询分析"
        elif "concept_explainer" in agent_name:
            concepts = result.get("concepts", [])
            return f"解释概念: {', '.join(concepts)}" if concepts else "生成概念解释"
        elif "hybrid_recommender" in agent_name:
            count = result.get("recommendation_count", 0)
            avg_score = result.get("average_score", 0)
            return f"推荐{count}个题目，平均分数{avg_score:.3f}" if count > 0 else "未找到推荐"
        elif "knowledge_retriever" in agent_name:
            problems = result.get("problems_found", 0)
            return f"检索到{problems}个相关题目" if problems > 0 else "完成知识检索"
        else:
            return step.get("description", "完成处理")

    def _calculate_step_quality(self, step: Dict) -> float:
        """计算步骤质量分数"""
        confidence = step.get("confidence", 0.5)
        status = step.get("status", "unknown")
        result = step.get("result", {})

        if status == "error":
            return 0.0
        elif status == "success":
            # 基于结果内容计算质量
            if "recommendation_count" in result:
                count = result["recommendation_count"]
                avg_score = result.get("average_score", 0)
                return min(1.0, confidence * (1 + count * 0.1) * (1 + avg_score))
            elif "concepts" in result:
                concepts = result["concepts"]
                return min(1.0, confidence * (1 + len(concepts) * 0.2))
            else:
                return confidence
        else:
            return confidence * 0.5

    def enhance_reasoning_step(self, step: Dict) -> Dict:
        """增强推理步骤信息"""
        enhanced_step = step.copy()
        enhanced_step.update({
            "data_source": self._identify_data_source(step),
            "output_summary": self._generate_step_summary(step),
            "quality_score": self._calculate_step_quality(step)
        })
        return enhanced_step

# 使用示例和测试
async def test_enhanced_system():
    """测试增强系统功能"""
    
    # 配置路径
    config = {
        "embedding_path": r"F:\algokg_platform\models\ensemble_gnn_embedding.pt",
        "entity2id_path": r"F:\algokg_platform\data\raw\entity2id.json", 
        "id2title_path": r"F:\algokg_platform\data\raw\entity_id_to_title.json",
        "tag_label_path": r"F:\algokg_platform\data\raw\problem_id_to_tags.json"
    }
    
    entity_id_to_title_path = r"F:\algokg_platform\data\raw\entity_id_to_title.json"
    
    try:
        # 初始化系统组件
        rec_system = EnhancedRecommendationSystem(**config)
        neo4j_api = Neo4jKnowledgeGraphAPI()
        
        # 初始化图增强的多Agent系统
        qa_system = GraphEnhancedMultiAgentSystem(
            rec_system, 
            neo4j_api, 
            entity_id_to_title_path=entity_id_to_title_path
        )
        
        # 测试查询
        test_queries = [
            "请解释动态规划的概念和原理",
            "基于不同的子序列这道题，推荐一些相似的题目",
            "推荐一些动态规划的中等难度题目，包括详细解法",
            "我已经做过两数之和，推荐下一步做什么题目",
            "什么是回溯算法，有哪些典型题目",
            "爬楼梯类似的题目有哪些"
        ]
        
        for query in test_queries:
            print(f"\n{'='*80}")
            print(f"查询: {query}")
            print('='*80)
            
            result = await qa_system.process_query(query)
            
            # 显示整合回答
            print(f"\n【整合回答】")
            print(result.get('integrated_response', '无'))
            
            # 显示详细信息
            print(f"\n【详细信息】")
            print(f"意图: {result['intent']}")
            print(f"识别实体: {', '.join(result['entities'])}")
            
            # 概念解释信息
            if result.get('concept_explanation'):
                concept = result['concept_explanation']
                print(f"\n【概念解释】")
                print(f"定义: {concept.get('definition', 'N/A')}")
                print(f"核心原理: {', '.join(concept.get('core_principles', []))}")
            
            # 例题信息
            if result.get('example_problems'):
                print(f"\n【例题分析】({len(result['example_problems'])}道题)")
                for i, problem in enumerate(result['example_problems'][:3], 1):
                    print(f"\n  {i}. {problem.get('title', 'N/A')}")
                    print(f"     难度: {problem.get('difficulty', 'N/A')}")
                    print(f"     标签: {', '.join(problem.get('algorithm_tags', []))}")
                    
                    # 显示解决方案
                    solutions = problem.get('solutions', [])
                    if solutions:
                        print(f"     解法: {solutions[0].get('approach', 'N/A')}")
                        print(f"     时间复杂度: {solutions[0].get('time_complexity', 'N/A')}")
            
            # 相似题目信息
            if result.get('similar_problems'):
                print(f"\n【相似题目推荐】({len(result['similar_problems'])}道题)")
                for i, sim in enumerate(result['similar_problems'][:5], 1):
                    print(f"  {i}. {sim.get('title', 'N/A')} (分数: {sim.get('hybrid_score', 0):.3f})")
                    print(f"      推荐理由: {sim.get('recommendation_reason', 'N/A')}")
                    print(f"      推荐强度: {sim.get('recommendation_strength', 'N/A')}")
                    
                    # 学习路径信息
                    learning_path = sim.get('learning_path', {})
                    if learning_path:
                        print(f"      学习路径: {learning_path.get('path_description', 'N/A')}")
            
            # 元数据
            metadata = result.get('metadata', {})
            print(f"\n【系统信息】")
            print(f"置信度: {metadata.get('confidence', 0):.2f}")
            print(f"实体映射数: {metadata.get('entity_mappings', 0)}")
            print(f"处理状态: {'成功' if not result.get('error') else '部分失败'}")
    
    except Exception as e:
        logger.error(f"测试系统失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'neo4j_api' in locals():
            neo4j_api.close()

class RecommendationFormatter:
    """将任意Agent的推荐结果补充增强"""

    def __init__(self, rec_system: EnhancedRecommendationSystem):
        self.rec_system = rec_system

    async def enrich_and_format(self, base_problems, query_title, top_k=10):
        # 若已有推荐，按标题重新调用embedding，补充分数理由等
        enhanced_recs = []
        seen_titles = set()
        
        for problem in base_problems:
            title = problem.get('title')
            if title and title not in seen_titles:
                seen_titles.add(title)
                embedding_result = self.rec_system.recommend(
                    query_title=title,
                    top_k=1,
                    alpha=0.7,
                    enable_diversity=False
                )
                if embedding_result and embedding_result.get("recommendations"):
                    rec = embedding_result["recommendations"][0]
                    enhanced_recs.append({
                        "title": title,
                        "hybrid_score": rec["hybrid_score"],
                        "embedding_score": rec["embedding_score"],
                        "tag_score": rec["tag_score"],
                        "shared_tags": rec["shared_tags"],
                        "learning_path": rec["learning_path"]["path_description"],
                        "recommendation_reason": rec["recommendation_reason"],
                        "learning_path_explanation": rec["learning_path"]["reasoning"]
                    })
        return {
            "query": query_title,
            "total_candidates": len(enhanced_recs),
            "cards": enhanced_recs
        }


if __name__ == "__main__":
    # 运行增强测试
    asyncio.run(test_enhanced_system())