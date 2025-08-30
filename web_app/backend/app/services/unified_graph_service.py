"""
统一图谱服务 - 融合知识图谱和Neo4j图谱功能
"""

import logging
from typing import Dict, List, Optional, Any, Union
from app.models.response import GraphData, GraphNode, GraphEdge
from backend.neo4j_loader.neo4j_api import Neo4jKnowledgeGraphAPI
from app.core.deps import get_current_neo4j_api

logger = logging.getLogger(__name__)

class UnifiedGraphService:
    """统一图谱服务 - 整合多种图谱数据源"""
    
    def __init__(self, neo4j_api: Optional[Neo4jKnowledgeGraphAPI] = None):
        self.neo4j_api = neo4j_api or get_current_neo4j_api()
        
    def query_unified_graph(self, 
                           entity_name: str,
                           entity_type: Optional[str] = None,
                           depth: int = 2,
                           limit: int = 50,
                           data_sources: List[str] = None) -> GraphData:
        """
        统一图谱查询 - 支持多数据源融合
        
        Args:
            entity_name: 实体名称
            entity_type: 实体类型
            depth: 查询深度
            limit: 结果限制
            data_sources: 数据源列表 ['neo4j', 'embedding', 'static']
        """
        if data_sources is None:
            data_sources = ['neo4j']  # 默认使用Neo4j
            
        all_nodes = []
        all_edges = []
        center_node = None
        
        # 1. Neo4j数据源
        if 'neo4j' in data_sources:
            neo4j_data = self._query_neo4j_graph(entity_name, entity_type, depth, limit)
            if neo4j_data:
                all_nodes.extend(neo4j_data.nodes)
                all_edges.extend(neo4j_data.edges)
                center_node = neo4j_data.center_node
                
        # 2. Embedding推荐数据源
        if 'embedding' in data_sources:
            embedding_data = self._query_embedding_graph(entity_name, limit)
            if embedding_data:
                all_nodes.extend(embedding_data.nodes)
                all_edges.extend(embedding_data.edges)
                
        # 3. 静态知识图谱数据源
        if 'static' in data_sources:
            static_data = self._query_static_graph(entity_name, entity_type, depth, limit)
            if static_data:
                all_nodes.extend(static_data.nodes)
                all_edges.extend(static_data.edges)
                
        # 去重和合并
        merged_data = self._merge_graph_data(all_nodes, all_edges, center_node or entity_name)
        
        # 增强节点信息
        enhanced_data = self._enhance_graph_data(merged_data, entity_name)
        
        logger.info(f"统一图谱查询完成: {entity_name}, 节点数: {len(enhanced_data.nodes)}, 边数: {len(enhanced_data.edges)}")
        return enhanced_data
        
    def _query_neo4j_graph(self, entity_name: str, entity_type: Optional[str], depth: int, limit: int) -> Optional[GraphData]:
        """查询Neo4j图谱数据"""
        try:
            from app.api.graph import Neo4jGraphVisualizer
            
            if not self.neo4j_api:
                logger.warning("Neo4j API不可用")
                return None
                
            visualizer = Neo4jGraphVisualizer(self.neo4j_api)
            return visualizer.query_graph_data(entity_name, entity_type, depth, limit)
            
        except Exception as e:
            logger.error(f"Neo4j图谱查询失败: {e}")
            return None
            
    def _query_embedding_graph(self, entity_name: str, limit: int) -> Optional[GraphData]:
        """基于embedding推荐构建图谱"""
        try:
            from app.core.deps import get_enhanced_recommendation_system
            
            rec_system = get_enhanced_recommendation_system()
            if not rec_system:
                return None
                
            # 获取推荐结果
            rec_result = rec_system.recommend(
                query_title=entity_name,
                top_k=min(limit, 10),
                alpha=0.7,
                enable_diversity=True
            )
            
            if "error" in rec_result:
                return None
                
            # 转换为图谱数据
            nodes = []
            edges = []
            
            # 中心节点
            center_id = f"problem_{entity_name}"
            nodes.append(GraphNode(
                id=center_id,
                label=entity_name,
                type="Problem",
                properties={"is_center": True, "source": "embedding"}
            ))
            
            # 推荐节点
            for i, rec in enumerate(rec_result.get("recommendations", [])):
                node_id = f"problem_{rec['title']}"
                nodes.append(GraphNode(
                    id=node_id,
                    label=rec["title"],
                    type="Problem",
                    properties={
                        "hybrid_score": rec["hybrid_score"],
                        "shared_tags": rec["shared_tags"],
                        "source": "embedding"
                    }
                ))
                
                # 添加相似关系边
                edges.append(GraphEdge(
                    source=center_id,
                    target=node_id,
                    relationship="SIMILAR_TO",
                    properties={
                        "score": rec["hybrid_score"],
                        "reason": rec["recommendation_reason"],
                        "source": "embedding"
                    }
                ))
                
            return GraphData(nodes=nodes, edges=edges, center_node=center_id, layout_type="force")
            
        except Exception as e:
            logger.error(f"Embedding图谱查询失败: {e}")
            return None
            
    def _query_static_graph(self, entity_name: str, entity_type: Optional[str], depth: int, limit: int) -> Optional[GraphData]:
        """查询静态知识图谱数据"""
        # 这里可以添加静态知识图谱的查询逻辑
        # 比如从配置文件、数据库或其他数据源加载预定义的图谱结构
        return None
        
    def _merge_graph_data(self, all_nodes: List[GraphNode], all_edges: List[GraphEdge], center_node: str) -> GraphData:
        """合并多个数据源的图谱数据"""
        # 去重节点
        unique_nodes = {}
        for node in all_nodes:
            if node.id not in unique_nodes:
                unique_nodes[node.id] = node
            else:
                # 合并节点属性
                existing_node = unique_nodes[node.id]
                if existing_node.properties is None:
                    existing_node.properties = {}
                if node.properties:
                    existing_node.properties.update(node.properties)
                    
        # 去重边
        unique_edges = {}
        for edge in all_edges:
            edge_key = f"{edge.source}-{edge.relationship}-{edge.target}"
            if edge_key not in unique_edges:
                unique_edges[edge_key] = edge
            else:
                # 合并边属性
                existing_edge = unique_edges[edge_key]
                if existing_edge.properties is None:
                    existing_edge.properties = {}
                if edge.properties:
                    existing_edge.properties.update(edge.properties)
                    
        return GraphData(
            nodes=list(unique_nodes.values()),
            edges=list(unique_edges.values()),
            center_node=center_node,
            layout_type="force"
        )
        
    def _enhance_graph_data(self, graph_data: GraphData, center_entity: str) -> GraphData:
        """增强图谱数据 - 添加额外信息和优化"""
        # 标记中心节点
        for node in graph_data.nodes:
            if node.properties is None:
                node.properties = {}
                
            # 标记是否为中心节点
            if node.id == graph_data.center_node or node.label == center_entity:
                node.properties["is_center"] = True
                node.properties["color"] = "#ff6b6b"  # 中心节点红色
            else:
                node.properties["is_center"] = False
                node.properties["color"] = self._get_node_color(node.type)
                
            # 添加可点击属性
            node.clickable = True
            
        # 增强边信息
        for edge in graph_data.edges:
            if edge.properties is None:
                edge.properties = {}
                
            # 根据关系类型设置边的样式
            edge.properties["color"] = self._get_edge_color(edge.relationship)
            edge.properties["width"] = self._get_edge_width(edge.relationship)
            
        return graph_data
        
    def _get_node_color(self, node_type: str) -> str:
        """根据节点类型获取颜色"""
        color_map = {
            "Problem": "#4ecdc4",      # 题目：青色
            "Algorithm": "#45b7d1",    # 算法：蓝色
            "DataStructure": "#96ceb4", # 数据结构：绿色
            "Technique": "#feca57",    # 技巧：黄色
            "Difficulty": "#ff9ff3",   # 难度：粉色
            "Platform": "#54a0ff",     # 平台：深蓝色
            "Operation": "#5f27cd",    # 操作：紫色
            "Concept": "#a55eea",      # 概念：紫色
        }
        return color_map.get(node_type, "#ddd")  # 默认灰色
        
    def _get_edge_color(self, relationship: str) -> str:
        """根据关系类型获取边颜色"""
        color_map = {
            "USES": "#45b7d1",         # 使用：蓝色
            "IMPLEMENTS": "#96ceb4",   # 实现：绿色
            "SIMILAR_TO": "#feca57",   # 相似：黄色
            "BELONGS_TO": "#ff9ff3",   # 属于：粉色
            "REQUIRES": "#54a0ff",     # 需要：深蓝色
            "RELATED_TO": "#a55eea",   # 相关：紫色
        }
        return color_map.get(relationship, "#999")  # 默认灰色
        
    def _get_edge_width(self, relationship: str) -> int:
        """根据关系类型获取边宽度"""
        width_map = {
            "USES": 2,
            "IMPLEMENTS": 3,
            "SIMILAR_TO": 2,
            "BELONGS_TO": 1,
            "REQUIRES": 2,
            "RELATED_TO": 1,
        }
        return width_map.get(relationship, 1)
        
    def get_node_details(self, node_id: str, node_type: str) -> Dict[str, Any]:
        """获取节点详细信息"""
        try:
            logger.info(f"获取节点详情: node_id={node_id}, node_type={node_type}")

            # 处理不同的节点ID格式
            if node_type == "Problem":
                # 提取题目名称，支持多种ID格式
                if node_id.startswith("neo4j_"):
                    # 来自QA服务的图谱：neo4j_题目名称
                    title = node_id.replace("neo4j_", "")
                elif node_id.startswith("problem_"):
                    # 来自独立图谱：problem_xxx
                    title = node_id.replace("problem_", "").replace("_", " ")
                elif node_id.startswith("node_problem_"):
                    # 来自独立图谱的格式：node_problem_AP_xxx
                    # 这种情况下，我们无法直接从节点ID获取题目名称
                    # 但我们可以提示用户，并尝试从前端传递的其他信息中获取
                    logger.warning(f"独立图谱节点ID格式: {node_id}")
                    return {
                        "basic_info": {
                            "title": "节点详情不可用",
                            "type": "Problem",
                            "description": "此节点来自独立图谱，无法直接获取详细信息。建议使用包含实体名称的问题来获取增强图谱数据。",
                            "category": "系统提示"
                        }
                    }
                else:
                    # 直接使用节点ID作为题目名称
                    # 这种情况通常是前端传递了节点的label（题目名称）
                    title = node_id

                logger.info(f"提取的题目名称: {title}")
                return self._get_problem_details(title)

            elif node_type == "Algorithm":
                if node_id.startswith("neo4j_"):
                    name = node_id.replace("neo4j_", "")
                elif node_id.startswith("algorithm_"):
                    name = node_id.replace("algorithm_", "").replace("_", " ")
                else:
                    name = node_id

                logger.info(f"提取的算法名称: {name}")
                return self._get_algorithm_details(name)

            elif node_type == "DataStructure":
                if node_id.startswith("neo4j_"):
                    name = node_id.replace("neo4j_", "")
                elif node_id.startswith("datastructure_"):
                    name = node_id.replace("datastructure_", "").replace("_", " ")
                else:
                    name = node_id

                logger.info(f"提取的数据结构名称: {name}")
                return self._get_datastructure_details(name)
            else:
                logger.warning(f"未支持的节点类型: {node_type}")
                return {"error": f"未支持的节点类型: {node_type}"}

        except Exception as e:
            logger.error(f"获取节点详情失败: {e}")
            return {"error": str(e)}

    def _get_problem_details_by_node_id(self, node_id: str) -> Dict[str, Any]:
        """通过节点ID获取题目详细信息 - 处理node_problem_格式"""
        try:
            if not self.neo4j_api:
                return {}

            logger.info(f"通过节点ID查询题目: {node_id}")

            # 处理node_problem_格式的节点ID
            if node_id.startswith("node_problem_"):
                # 提取element_id部分
                element_id = node_id.replace("node_problem_", "")
                logger.info(f"提取的element_id: {element_id}")

                # 通过element_id查询Neo4j节点
                try:
                    with self.neo4j_api.driver.session() as session:
                        # 尝试多种查询方式
                        queries = [
                            # Neo4j 5.x+ 使用 elementId()
                            """
                            MATCH (p:Problem)
                            WHERE elementId(p) = $element_id
                            RETURN p.title as title
                            """,
                            # Neo4j 4.x 使用 id()
                            """
                            MATCH (p:Problem)
                            WHERE id(p) = toInteger($element_id)
                            RETURN p.title as title
                            """,
                            # 如果element_id是字符串格式，尝试直接匹配
                            """
                            MATCH (p:Problem)
                            WHERE toString(id(p)) = $element_id
                            RETURN p.title as title
                            """
                        ]

                        result = None
                        for i, query in enumerate(queries):
                            try:
                                logger.info(f"尝试查询方式 {i+1}: {element_id}")
                                result = session.run(query, element_id=element_id).single()
                                if result and result['title']:
                                    break
                            except Exception as query_error:
                                logger.warning(f"查询方式 {i+1} 失败: {query_error}")
                                continue

                        if result and result['title']:
                            title = result['title']
                            logger.info(f"通过element_id找到题目: {title}")
                            return self._get_problem_details(title)
                        else:
                            logger.warning(f"所有查询方式都未找到element_id对应的题目: {element_id}")
                            # 提供更友好的错误信息和建议
                            return {
                                "error": f"无法通过节点ID '{node_id}' 找到对应的题目",
                                "suggestion": "请尝试直接使用题目名称进行查询，或使用QA服务生成的图谱",
                                "basic_info": {
                                    "title": "节点信息不可用",
                                    "type": "Problem",
                                    "description": f"节点ID '{node_id}' 可能来自独立图谱，建议使用题目名称查询"
                                }
                            }

                except Exception as e:
                    logger.error(f"通过element_id查询失败: {e}")
                    return {"error": f"查询节点ID '{node_id}' 失败: {str(e)}"}

            return {"error": f"不支持的节点ID格式: {node_id}"}

        except Exception as e:
            logger.error(f"通过节点ID获取题目详情失败: {e}")
            return {"error": str(e)}

    def _get_problem_details(self, title: str) -> Dict[str, Any]:
        """获取题目详细信息 - 返回格式化的丰富数据"""
        try:
            if not self.neo4j_api:
                return {}

            # 获取完整题目信息
            problem_info = self.neo4j_api.get_problem_by_title(title)
            if not problem_info:
                return {"error": f"题目 '{title}' 未找到"}

            # 获取相似题目
            similar_problems = self.neo4j_api.get_similar_problems(title, limit=5)

            # 格式化返回数据，与独立图谱API保持一致
            result = {
                "basic_info": {
                    "title": problem_info.get("title", title),
                    "type": "Problem",
                    "description": problem_info.get("description", ""),
                    "difficulty": problem_info.get("difficulty", ""),
                    "platform": problem_info.get("platform", ""),
                    "category": problem_info.get("category", ""),
                    "url": problem_info.get("url", "")
                },
                "algorithms": [
                    {
                        "name": alg.get("name", ""),
                        "description": alg.get("description", ""),
                        "category": alg.get("category", "")
                    }
                    for alg in problem_info.get("algorithms", [])
                ],
                "data_structures": [
                    {
                        "name": ds.get("name", ""),
                        "description": ds.get("description", ""),
                        "category": ds.get("category", "")
                    }
                    for ds in problem_info.get("data_structures", [])
                ],
                "techniques": [
                    {
                        "name": tech.get("name", ""),
                        "description": tech.get("description", "")
                    }
                    for tech in problem_info.get("techniques", [])
                ],
                "related_problems": [
                    {
                        "title": sp.get("title", ""),
                        "difficulty": sp.get("difficulty", ""),
                        "similarity_score": sp.get("similarity_score", 0)
                    }
                    for sp in similar_problems
                ],
                "complexity": {
                    "time": problem_info.get("time_complexity", "未知"),
                    "space": problem_info.get("space_complexity", "未知")
                },
                "solutions": problem_info.get("solutions", []),
                "insights": problem_info.get("insights", []),
                "step_by_step": problem_info.get("step_by_step", [])
            }

            return result

        except Exception as e:
            logger.error(f"获取题目详情失败: {e}")
            return {"error": str(e)}
            
    def _get_algorithm_details(self, name: str) -> Dict[str, Any]:
        """获取算法详细信息 - 返回格式化的丰富数据"""
        try:
            if not self.neo4j_api:
                return {}

            # 获取算法信息
            algorithm_info = self.neo4j_api.get_algorithm_by_name(name)
            if not algorithm_info:
                return {"error": f"算法 '{name}' 未找到"}

            # 安全地获取算法信息
            alg_node = algorithm_info.get("algorithm", {})
            problems_data = algorithm_info.get("problems", [])

            # 将Neo4j节点转换为字典
            if hasattr(alg_node, 'get'):
                # Neo4j节点对象，转换为字典
                algorithm_data = dict(alg_node)
            elif isinstance(alg_node, dict):
                # 已经是字典
                algorithm_data = alg_node
            else:
                # 其他情况，创建空字典
                algorithm_data = {}

            # 格式化返回数据
            result = {
                "basic_info": {
                    "title": algorithm_data.get("name", name),
                    "type": "Algorithm",
                    "description": algorithm_data.get("description", ""),
                    "category": algorithm_data.get("category", ""),
                    "complexity": algorithm_data.get("complexity", "")
                },
                "related_problems": [
                    {
                        "title": problem.get("title", "") if hasattr(problem, 'get') else str(problem),
                        "difficulty": problem.get("difficulty", "") if hasattr(problem, 'get') else "",
                        "platform": problem.get("platform", "") if hasattr(problem, 'get') else ""
                    }
                    for problem in problems_data if problem
                ],
                "complexity": {
                    "time": algorithm_data.get("time_complexity", "未知"),
                    "space": algorithm_data.get("space_complexity", "未知")
                },
                "applications": algorithm_data.get("applications", []),
                "advantages": algorithm_data.get("advantages", []),
                "disadvantages": algorithm_data.get("disadvantages", [])
            }

            return result

        except Exception as e:
            logger.error(f"获取算法详情失败: {e}")
            return {"error": str(e)}
            
    def _get_datastructure_details(self, name: str) -> Dict[str, Any]:
        """获取数据结构详细信息 - 返回格式化的丰富数据"""
        try:
            if not self.neo4j_api:
                return {}

            # 获取数据结构信息
            ds_info = self.neo4j_api.get_data_structure_by_name(name)
            if not ds_info:
                return {"error": f"数据结构 '{name}' 未找到"}

            logger.info(f"数据结构信息类型: {type(ds_info)}, 内容: {ds_info}")

            # 安全地获取数据结构信息
            ds_node = ds_info.get("data_structure", {})
            problems_data = ds_info.get("problems", [])

            logger.info(f"数据结构节点类型: {type(ds_node)}, 内容: {ds_node}")

            # 将Neo4j节点转换为字典
            if hasattr(ds_node, 'get'):
                # Neo4j节点对象，转换为字典
                ds_data = dict(ds_node)
                logger.info(f"转换后的数据结构数据: {ds_data}")
            elif isinstance(ds_node, dict):
                # 已经是字典
                ds_data = ds_node
                logger.info(f"数据结构数据已是字典: {ds_data}")
            else:
                # 其他情况，创建空字典
                logger.warning(f"数据结构节点类型异常: {type(ds_node)}, 值: {ds_node}")
                ds_data = {}

            # 格式化返回数据
            result = {
                "basic_info": {
                    "title": ds_data.get("name", name),
                    "type": "DataStructure",
                    "description": ds_data.get("description", ""),
                    "category": ds_data.get("category", ""),
                    "properties": ds_data.get("properties", "")
                },
                "related_problems": [
                    {
                        "title": problem.get("title", "") if hasattr(problem, 'get') else str(problem),
                        "difficulty": problem.get("difficulty", "") if hasattr(problem, 'get') else "",
                        "platform": problem.get("platform", "") if hasattr(problem, 'get') else ""
                    }
                    for problem in problems_data if problem
                ],
                "operations": [
                    {
                        "name": op.get("name", ""),
                        "complexity": op.get("complexity", ""),
                        "description": op.get("description", "")
                    }
                    for op in ds_data.get("operations", [])
                ],
                "complexity": {
                    "access": ds_data.get("access_complexity", "未知"),
                    "search": ds_data.get("search_complexity", "未知"),
                    "insertion": ds_data.get("insertion_complexity", "未知"),
                    "deletion": ds_data.get("deletion_complexity", "未知")
                },
                "advantages": ds_data.get("advantages", []),
                "disadvantages": ds_data.get("disadvantages", []),
                "use_cases": ds_data.get("use_cases", [])
            }

            return result

        except Exception as e:
            logger.error(f"获取数据结构详情失败: {e}")
            return {"error": str(e)}
