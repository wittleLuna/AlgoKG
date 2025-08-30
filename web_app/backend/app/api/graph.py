from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
import logging
import json

from app.models import GraphQueryRequest, GraphData, GraphNode, GraphEdge
from app.core.deps import get_current_neo4j_api
from backend.neo4j_loader.neo4j_api import Neo4jKnowledgeGraphAPI
from app.services.unified_graph_service import UnifiedGraphService

logger = logging.getLogger(__name__)
router = APIRouter()

class Neo4jGraphVisualizer:
    """Neo4j图谱可视化器"""

    def __init__(self, neo4j_api: Neo4jKnowledgeGraphAPI):
        self.neo4j_api = neo4j_api

    def query_graph_data(self, center_entity: str, entity_type: str = None, depth: int = 2, limit: int = 50) -> GraphData:
        """查询图谱数据用于可视化"""

        # 构建Cypher查询
        if entity_type == "Problem":
            cypher = self._build_problem_graph_query(center_entity, depth, limit)
        elif entity_type == "Algorithm":
            cypher = self._build_algorithm_graph_query(center_entity, depth, limit)
        elif entity_type == "DataStructure":
            cypher = self._build_data_structure_graph_query(center_entity, depth, limit)
        else:
            cypher = self._build_general_graph_query(center_entity, depth, limit)

        # 执行查询
        try:
            # 根据实体类型设置正确的参数名
            if entity_type == "Problem":
                params = {"problem_title": center_entity}
            elif entity_type == "Algorithm":
                params = {"algorithm_name": center_entity}
            elif entity_type == "DataStructure":
                params = {"ds_name": center_entity}
            else:
                params = {"entity_name": center_entity}

            results = self.neo4j_api.run_query(cypher, params)
            return self._convert_to_graph_data(results, center_entity)
        except Exception as e:
            logger.error(f"Neo4j图谱查询失败: {e}")
            return GraphData(nodes=[], edges=[], center_node="", layout_type="force")

    def _build_problem_graph_query(self, problem_title: str, depth: int, limit: int) -> str:
        """构建题目相关的图谱查询"""
        return """
        MATCH (p:Problem {title: $problem_title})
        OPTIONAL MATCH (p)-[r1:USES_ALGORITHM]->(a:Algorithm)
        OPTIONAL MATCH (p)-[r2:USES_DATA_STRUCTURE]->(ds:DataStructure)
        OPTIONAL MATCH (p)-[r3:USES_TECHNIQUE]->(t:Technique)
        OPTIONAL MATCH (p)-[r4:SIMILAR_TO]->(sp:Problem)
        OPTIONAL MATCH (p)-[r5:HAS_DIFFICULTY]->(d:Difficulty)
        OPTIONAL MATCH (p)-[r6:BELONGS_TO_PLATFORM]->(pl:Platform)

        WITH p,
             collect(DISTINCT {node: a, rel: r1, type: 'Algorithm'}) as algorithms,
             collect(DISTINCT {node: ds, rel: r2, type: 'DataStructure'}) as data_structures,
             collect(DISTINCT {node: t, rel: r3, type: 'Technique'}) as techniques,
             collect(DISTINCT {node: sp, rel: r4, type: 'Problem'}) as similar_problems,
             collect(DISTINCT {node: d, rel: r5, type: 'Difficulty'}) as difficulties,
             collect(DISTINCT {node: pl, rel: r6, type: 'Platform'}) as platforms

        RETURN p as center_node,
               algorithms[..10] as algorithms,
               data_structures[..10] as data_structures,
               techniques[..10] as techniques,
               similar_problems[..15] as similar_problems,
               difficulties as difficulties,
               platforms as platforms
        """

    def _build_algorithm_graph_query(self, algorithm_name: str, depth: int, limit: int) -> str:
        """构建算法相关的图谱查询"""
        return """
        MATCH (a:Algorithm {name: $algorithm_name})
        OPTIONAL MATCH (p:Problem)-[r1:USES_ALGORITHM]->(a)
        OPTIONAL MATCH (a)-[r2:RELATED_TO]->(ra:Algorithm)
        OPTIONAL MATCH (a)-[r3:REQUIRES_DATA_STRUCTURE]->(ds:DataStructure)
        OPTIONAL MATCH (a)-[r4:USES_TECHNIQUE]->(t:Technique)

        WITH a,
             collect(DISTINCT {node: p, rel: r1, type: 'Problem'}) as problems,
             collect(DISTINCT {node: ra, rel: r2, type: 'Algorithm'}) as related_algorithms,
             collect(DISTINCT {node: ds, rel: r3, type: 'DataStructure'}) as data_structures,
             collect(DISTINCT {node: t, rel: r4, type: 'Technique'}) as techniques

        RETURN a as center_node,
               problems[..25] as problems,
               related_algorithms[..10] as related_algorithms,
               data_structures[..10] as data_structures,
               techniques[..10] as techniques
        """

    def _build_data_structure_graph_query(self, ds_name: str, depth: int, limit: int) -> str:
        """构建数据结构相关的图谱查询"""
        return """
        MATCH (ds:DataStructure {name: $ds_name})
        OPTIONAL MATCH (p:Problem)-[r1:USES_DATA_STRUCTURE]->(ds)
        OPTIONAL MATCH (a:Algorithm)-[r2:REQUIRES_DATA_STRUCTURE]->(ds)
        OPTIONAL MATCH (ds)-[r3:RELATED_TO]->(rds:DataStructure)
        OPTIONAL MATCH (ds)-[r4:SUPPORTS_OPERATION]->(op:Operation)

        WITH ds,
             collect(DISTINCT {node: p, rel: r1, type: 'Problem'}) as problems,
             collect(DISTINCT {node: a, rel: r2, type: 'Algorithm'}) as algorithms,
             collect(DISTINCT {node: rds, rel: r3, type: 'DataStructure'}) as related_ds,
             collect(DISTINCT {node: op, rel: r4, type: 'Operation'}) as operations

        RETURN ds as center_node,
               problems[..25] as problems,
               algorithms[..10] as algorithms,
               related_ds[..10] as related_ds,
               operations[..10] as operations
        """

    def _build_general_graph_query(self, entity_name: str, depth: int, limit: int) -> str:
        """构建通用图谱查询"""
        return """
        MATCH (n)
        WHERE n.name = $entity_name OR n.title = $entity_name
        OPTIONAL MATCH (n)-[r]-(connected)

        WITH n, collect(DISTINCT {node: connected, rel: r, type: labels(connected)[0]}) as connections

        RETURN n as center_node,
               connections[..50] as connections
        """

    def _convert_to_graph_data(self, results: List[Dict], center_entity: str) -> GraphData:
        """将Neo4j查询结果转换为图谱数据"""
        nodes = []
        edges = []
        center_node_id = None

        if not results:
            return GraphData(nodes=[], edges=[], center_node="", layout_type="force")

        result = results[0]  # 取第一个结果

        # 处理中心节点
        center_node = result.get('center_node')
        if center_node:
            center_node_id = self._create_node_id(center_node)
            nodes.append(self._convert_node(center_node, is_center=True))

        # 处理连接的节点
        for key, connections in result.items():
            if key == 'center_node' or not connections:
                continue

            for connection in connections:
                if isinstance(connection, dict) and 'node' in connection:
                    connected_node = connection['node']
                    relationship = connection.get('rel', {})
                    node_type = connection.get('type', 'Unknown')

                    if connected_node:
                        # 添加连接的节点
                        connected_node_id = self._create_node_id(connected_node)
                        nodes.append(self._convert_node(connected_node, node_type=node_type))

                        # 添加边
                        if center_node_id and relationship:
                            edge = self._convert_edge(center_node_id, connected_node_id, relationship)
                            if edge:
                                edges.append(edge)

        # 去重节点
        unique_nodes = {}
        for node in nodes:
            unique_nodes[node.id] = node

        return GraphData(
            nodes=list(unique_nodes.values()),
            edges=edges,
            center_node=center_node_id or "",
            layout_type="force"
        )

    def _create_node_id(self, node) -> str:
        """创建节点ID"""
        if hasattr(node, 'element_id'):
            return f"node_{node.element_id}"
        elif isinstance(node, dict):
            # 尝试从字典中获取标识符
            for key in ['id', 'element_id', 'title', 'name']:
                if key in node:
                    return f"node_{node[key]}"
        return f"node_{hash(str(node))}"

    def _convert_node(self, node, is_center: bool = False, node_type: str = None) -> GraphNode:
        """转换Neo4j节点为GraphNode"""
        node_id = self._create_node_id(node)

        # 获取节点标签
        if hasattr(node, 'labels'):
            labels = list(node.labels)
            primary_type = labels[0] if labels else (node_type or "Unknown")
        else:
            primary_type = node_type or "Unknown"

        # 获取节点属性
        if hasattr(node, 'get'):
            # Neo4j节点对象
            properties = dict(node)
            label = node.get('title') or node.get('name') or node.get('label') or str(node_id)
        elif isinstance(node, dict):
            # 字典格式
            properties = node.copy()
            label = node.get('title') or node.get('name') or node.get('label') or str(node_id)
        else:
            properties = {}
            label = str(node)

        # 添加可视化属性
        properties.update({
            "is_center": is_center,
            "node_type": primary_type,
            "size": 30 if is_center else 20,
            "color": self._get_node_color(primary_type, is_center)
        })

        return GraphNode(
            id=node_id,
            label=label,
            type=primary_type,
            properties=properties
        )

    def _convert_edge(self, source_id: str, target_id: str, relationship) -> Optional[GraphEdge]:
        """转换Neo4j关系为GraphEdge"""
        if not relationship:
            return None

        # 获取关系类型
        if hasattr(relationship, 'type'):
            rel_type = relationship.type
        elif isinstance(relationship, dict) and 'type' in relationship:
            rel_type = relationship['type']
        else:
            rel_type = "RELATED_TO"

        # 获取关系属性
        if hasattr(relationship, 'get'):
            properties = dict(relationship)
        elif isinstance(relationship, dict):
            properties = relationship.copy()
        else:
            properties = {}

        return GraphEdge(
            source=source_id,
            target=target_id,
            relationship=rel_type,
            properties=properties
        )

    def _get_node_color(self, node_type: str, is_center: bool = False) -> str:
        """根据节点类型获取颜色"""
        if is_center:
            return "#ff6b6b"  # 中心节点红色

        color_map = {
            "Problem": "#4ecdc4",      # 题目：青色
            "Algorithm": "#45b7d1",    # 算法：蓝色
            "DataStructure": "#96ceb4", # 数据结构：绿色
            "Technique": "#feca57",    # 技巧：黄色
            "Difficulty": "#ff9ff3",   # 难度：粉色
            "Platform": "#54a0ff",     # 平台：深蓝色
            "Operation": "#5f27cd",    # 操作：紫色
        }

        return color_map.get(node_type, "#ddd")  # 默认灰色

# ================== 统一图谱API ==================

@router.post("/unified/query", response_model=GraphData)
async def query_unified_graph(
    request: GraphQueryRequest,
    data_sources: List[str] = Query(default=["neo4j"], description="数据源列表"),
    neo4j_api: Neo4jKnowledgeGraphAPI = Depends(get_current_neo4j_api)
):
    """
    统一图谱查询 - 融合多种数据源

    - **entity_name**: 实体名称
    - **entity_type**: 实体类型（可选）
    - **depth**: 查询深度
    - **limit**: 结果限制
    - **data_sources**: 数据源列表 ['neo4j', 'embedding', 'static']
    """
    try:
        unified_service = UnifiedGraphService(neo4j_api)

        graph_data = unified_service.query_unified_graph(
            entity_name=request.entity_name,
            entity_type=request.entity_type,
            depth=request.depth,
            limit=request.limit,
            data_sources=data_sources
        )

        logger.info(f"统一图谱查询成功: {request.entity_name}, 数据源: {data_sources}, 节点数: {len(graph_data.nodes)}")
        return graph_data

    except Exception as e:
        logger.error(f"统一图谱查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unified/node/{node_id}/details")
async def get_unified_node_details(
    node_id: str,
    node_type: str = Query(..., description="节点类型"),
    neo4j_api: Neo4jKnowledgeGraphAPI = Depends(get_current_neo4j_api)
):
    """
    获取统一图谱节点详细信息

    - **node_id**: 节点ID
    - **node_type**: 节点类型
    """
    try:
        unified_service = UnifiedGraphService(neo4j_api)
        details = unified_service.get_node_details(node_id, node_type)

        logger.info(f"获取节点详情成功: {node_id}")
        return details

    except Exception as e:
        logger.error(f"获取节点详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=GraphData)
async def query_graph(
    request: GraphQueryRequest,
    neo4j_api: Neo4jKnowledgeGraphAPI = Depends(get_current_neo4j_api)
):
    """
    查询知识图谱数据 - 基于Neo4j实时数据

    - **entity_name**: 实体名称
    - **entity_type**: 实体类型（可选）
    - **depth**: 查询深度
    - **limit**: 结果限制
    """
    try:
        visualizer = Neo4jGraphVisualizer(neo4j_api)

        # 设置查询参数
        params = {
            "entity_name": request.entity_name,
            "problem_title": request.entity_name,
            "algorithm_name": request.entity_name,
            "ds_name": request.entity_name
        }

        # 执行查询并返回图谱数据
        graph_data = visualizer.query_graph_data(
            center_entity=request.entity_name,
            entity_type=request.entity_type,
            depth=request.depth,
            limit=request.limit
        )

        logger.info(f"Neo4j图谱查询成功: {request.entity_name}, 节点数: {len(graph_data.nodes)}, 边数: {len(graph_data.edges)}")
        return graph_data

    except Exception as e:
        logger.error(f"Neo4j图谱查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/neo4j/problem/{problem_title}", response_model=GraphData)
async def get_neo4j_problem_graph(
    problem_title: str,
    depth: int = Query(default=2, ge=1, le=5),
    limit: int = Query(default=30, ge=1, le=100),
    neo4j_api: Neo4jKnowledgeGraphAPI = Depends(get_current_neo4j_api)
):
    """
    获取特定题目的Neo4j知识图谱

    - **problem_title**: 题目标题
    - **depth**: 查询深度
    - **limit**: 结果限制
    """
    try:
        visualizer = Neo4jGraphVisualizer(neo4j_api)
        graph_data = visualizer.query_graph_data(
            center_entity=problem_title,
            entity_type="Problem",
            depth=depth,
            limit=limit
        )

        logger.info(f"Neo4j题目图谱查询成功: {problem_title}")
        return graph_data

    except Exception as e:
        logger.error(f"获取Neo4j题目图谱失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/neo4j/algorithm/{algorithm_name}", response_model=GraphData)
async def get_neo4j_algorithm_graph(
    algorithm_name: str,
    depth: int = Query(default=2, ge=1, le=5),
    limit: int = Query(default=30, ge=1, le=100),
    neo4j_api: Neo4jKnowledgeGraphAPI = Depends(get_current_neo4j_api)
):
    """
    获取特定算法的Neo4j知识图谱

    - **algorithm_name**: 算法名称
    - **depth**: 查询深度
    - **limit**: 结果限制
    """
    try:
        visualizer = Neo4jGraphVisualizer(neo4j_api)
        graph_data = visualizer.query_graph_data(
            center_entity=algorithm_name,
            entity_type="Algorithm",
            depth=depth,
            limit=limit
        )

        logger.info(f"Neo4j算法图谱查询成功: {algorithm_name}")
        return graph_data

    except Exception as e:
        logger.error(f"获取Neo4j算法图谱失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/neo4j/data-structure/{ds_name}", response_model=GraphData)
async def get_neo4j_data_structure_graph(
    ds_name: str,
    depth: int = Query(default=2, ge=1, le=5),
    limit: int = Query(default=30, ge=1, le=100),
    neo4j_api: Neo4jKnowledgeGraphAPI = Depends(get_current_neo4j_api)
):
    """
    获取特定数据结构的Neo4j知识图谱

    - **ds_name**: 数据结构名称
    - **depth**: 查询深度
    - **limit**: 结果限制
    """
    try:
        visualizer = Neo4jGraphVisualizer(neo4j_api)
        graph_data = visualizer.query_graph_data(
            center_entity=ds_name,
            entity_type="DataStructure",
            depth=depth,
            limit=limit
        )

        logger.info(f"Neo4j数据结构图谱查询成功: {ds_name}")
        return graph_data

    except Exception as e:
        logger.error(f"获取Neo4j数据结构图谱失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/neo4j/explore", response_model=GraphData)
async def explore_neo4j_graph(
    query: str = Query(..., description="搜索查询"),
    node_types: str = Query(default="Problem,Algorithm,DataStructure", description="节点类型，逗号分隔"),
    limit: int = Query(default=50, ge=1, le=200),
    neo4j_api: Neo4jKnowledgeGraphAPI = Depends(get_current_neo4j_api)
):
    """
    探索Neo4j知识图谱 - 支持模糊搜索

    - **query**: 搜索关键词
    - **node_types**: 要搜索的节点类型
    - **limit**: 结果限制
    """
    try:
        # 构建模糊搜索查询
        types = [t.strip() for t in node_types.split(",")]
        type_conditions = " OR ".join([f"n:{t}" for t in types])

        cypher = f"""
        MATCH (n)
        WHERE ({type_conditions})
        AND (toLower(n.name) CONTAINS toLower($query)
             OR toLower(n.title) CONTAINS toLower($query)
             OR toLower(n.description) CONTAINS toLower($query))

        OPTIONAL MATCH (n)-[r]-(connected)
        WHERE ({type_conditions.replace('n:', 'connected:')})

        WITH n, collect(DISTINCT {{node: connected, rel: r, type: labels(connected)[0]}}) as connections
        LIMIT {limit}

        RETURN n as center_node, connections
        """

        results = neo4j_api.run_query(cypher, {"query": query})

        # 转换为图谱数据
        visualizer = Neo4jGraphVisualizer(neo4j_api)
        nodes = []
        edges = []

        for result in results:
            center_node = result.get('center_node')
            if center_node:
                center_id = visualizer._create_node_id(center_node)
                nodes.append(visualizer._convert_node(center_node))

                connections = result.get('connections', [])
                for conn in connections[:10]:  # 限制每个中心节点的连接数
                    if isinstance(conn, dict) and 'node' in conn:
                        connected_node = conn['node']
                        if connected_node:
                            connected_id = visualizer._create_node_id(connected_node)
                            nodes.append(visualizer._convert_node(connected_node, node_type=conn.get('type')))

                            edge = visualizer._convert_edge(center_id, connected_id, conn.get('rel'))
                            if edge:
                                edges.append(edge)

        # 去重节点
        unique_nodes = {}
        for node in nodes:
            unique_nodes[node.id] = node

        graph_data = GraphData(
            nodes=list(unique_nodes.values()),
            edges=edges,
            center_node="",
            layout_type="force"
        )

        logger.info(f"Neo4j探索查询成功: {query}, 节点数: {len(graph_data.nodes)}")
        return graph_data

    except Exception as e:
        logger.error(f"Neo4j探索查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 添加题目详情API
@router.get("/problem/{problem_title}")
async def get_problem_detail(problem_title: str):
    """获取题目详细信息"""
    try:
        from app.services.enhanced_problem_service import EnhancedProblemService

        service = EnhancedProblemService()
        problem_detail = service.get_problem_detail(problem_title)

        if not problem_detail:
            raise HTTPException(status_code=404, detail="题目未找到")

        return problem_detail

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取题目详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations/fallback")
async def get_fallback_recommendations(query: str = Query(..., description="查询内容")):
    """获取备用推荐"""
    try:
        from app.services.enhanced_problem_service import EnhancedProblemService

        service = EnhancedProblemService()
        recommendations = service.get_fallback_recommendations(query)

        return {"recommendations": recommendations}

    except Exception as e:
        logger.error(f"获取备用推荐失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/problems/search-by-tags")
async def search_problems_by_tags(tags: List[str]):
    """根据标签搜索题目"""
    try:
        from app.services.enhanced_problem_service import EnhancedProblemService

        service = EnhancedProblemService()
        results = service.search_problems_by_tags(tags)

        return {"problems": results}

    except Exception as e:
        logger.error(f"根据标签搜索题目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/problem/{problem_title}/graph", response_model=GraphData)
async def get_problem_graph(
    problem_title: str,
    depth: int = Query(default=2, ge=1, le=5),
    limit: int = Query(default=20, ge=1, le=100),
    neo4j_api: Neo4jKnowledgeGraphAPI = Depends(get_current_neo4j_api)
):
    """
    获取特定题目的知识图谱
    
    - **problem_title**: 题目标题
    - **depth**: 查询深度
    - **limit**: 结果限制
    """
    try:
        # 获取题目详细信息
        problem_info = neo4j_api.get_problem_by_title(problem_title)
        if not problem_info:
            raise HTTPException(status_code=404, detail=f"题目 '{problem_title}' 不存在")
        
        nodes = []
        edges = []
        
        # 添加中心题目节点
        center_node_id = f"problem_{problem_title}"
        nodes.append(GraphNode(
            id=center_node_id,
            label=problem_title,
            type="Problem",
            properties={
                "difficulty": problem_info.get("difficulty", ""),
                "platform": problem_info.get("platform", ""),
                "category": problem_info.get("category", ""),
                "description": problem_info.get("description", ""),
                "url": problem_info.get("url", ""),
                "images": problem_info.get("images", []),
                "step_by_step": problem_info.get("step_by_step", []),
                "algorithms": [alg.get("name", "") for alg in problem_info.get("algorithms", [])],
                "data_structures": [ds.get("name", "") for ds in problem_info.get("data_structures", [])],
                "techniques": [tech.get("name", "") for tech in problem_info.get("techniques", [])],
                "insights": [ins.get("content", "") for ins in problem_info.get("insights", [])],
                "is_center": True
            }
        ))
        
        # 添加算法节点
        for i, algorithm in enumerate(problem_info.get("algorithms", [])[:5]):
            if algorithm:
                alg_id = f"algorithm_{i}"
                nodes.append(GraphNode(
                    id=alg_id,
                    label=algorithm.get("name", ""),
                    type="Algorithm",
                    properties=algorithm
                ))
                edges.append(GraphEdge(
                    source=center_node_id,
                    target=alg_id,
                    relationship="USES_ALGORITHM"
                ))
        
        # 添加数据结构节点
        for i, ds in enumerate(problem_info.get("data_structures", [])[:5]):
            if ds:
                ds_id = f"data_structure_{i}"
                nodes.append(GraphNode(
                    id=ds_id,
                    label=ds.get("name", ""),
                    type="DataStructure",
                    properties=ds
                ))
                edges.append(GraphEdge(
                    source=center_node_id,
                    target=ds_id,
                    relationship="REQUIRES_DATA_STRUCTURE"
                ))
        
        # 添加技巧节点
        for i, technique in enumerate(problem_info.get("techniques", [])[:5]):
            if technique:
                tech_id = f"technique_{i}"
                nodes.append(GraphNode(
                    id=tech_id,
                    label=technique.get("name", ""),
                    type="Technique",
                    properties=technique
                ))
                edges.append(GraphEdge(
                    source=center_node_id,
                    target=tech_id,
                    relationship="APPLIES_TECHNIQUE"
                ))

        # 添加洞察节点
        for i, insight in enumerate(problem_info.get("insights", [])[:3]):
            if insight:
                insight_id = f"insight_{i}"
                nodes.append(GraphNode(
                    id=insight_id,
                    label=f"洞察{i+1}",
                    type="Insight",
                    properties={
                        "content": insight.get("content", ""),
                        "importance": insight.get("importance", "medium"),
                        "category": insight.get("category", "")
                    }
                ))
                edges.append(GraphEdge(
                    source=center_node_id,
                    target=insight_id,
                    relationship="PROVIDES_INSIGHT"
                ))

        # 添加图片节点
        for i, image in enumerate(problem_info.get("images", [])[:3]):
            if image and image.get("url"):
                image_id = f"image_{i}"
                nodes.append(GraphNode(
                    id=image_id,
                    label=f"图片{i+1}",
                    type="Image",
                    properties={
                        "url": image.get("url", ""),
                        "description": image.get("description", ""),
                        "type": image.get("type", "diagram")
                    }
                ))
                edges.append(GraphEdge(
                    source=center_node_id,
                    target=image_id,
                    relationship="HAS_IMAGE"
                ))

        # 添加解题步骤节点
        for i, step in enumerate(problem_info.get("step_by_step", [])[:5]):
            if step and step.get("title"):
                step_id = f"step_{i}"
                nodes.append(GraphNode(
                    id=step_id,
                    label=f"步骤{step.get('order', i+1)}",
                    type="Step",
                    properties={
                        "title": step.get("title", ""),
                        "description": step.get("description", ""),
                        "code": step.get("code", ""),
                        "explanation": step.get("explanation", ""),
                        "order": step.get("order", i+1)
                    }
                ))
                edges.append(GraphEdge(
                    source=center_node_id,
                    target=step_id,
                    relationship="HAS_STEP",
                    properties={"order": step.get("order", i+1)}
                ))

        # 获取相似题目
        similar_problems = neo4j_api.get_similar_problems(problem_title, 5)
        for i, similar in enumerate(similar_problems):
            similar_id = f"similar_{i}"
            nodes.append(GraphNode(
                id=similar_id,
                label=similar.get("title", ""),
                type="Problem",
                properties={
                    "difficulty": similar.get("difficulty", ""),
                    "category": similar.get("category", ""),
                    "similarity_score": similar.get("similarity_score", 0)
                }
            ))
            edges.append(GraphEdge(
                source=center_node_id,
                target=similar_id,
                relationship="SIMILAR_TO",
                properties={"confidence": similar.get("similarity_score", 0)}
            ))
        
        return GraphData(
            nodes=nodes,
            edges=edges,
            center_node=center_node_id,
            layout_type="force"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取题目图谱失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/concept/{concept_name}/graph", response_model=GraphData)
async def get_concept_graph(
    concept_name: str,
    depth: int = Query(default=2, ge=1, le=5),
    limit: int = Query(default=20, ge=1, le=100),
    neo4j_api: Neo4jKnowledgeGraphAPI = Depends(get_current_neo4j_api)
):
    """
    获取特定概念的知识图谱
    
    - **concept_name**: 概念名称
    - **depth**: 查询深度
    - **limit**: 结果限制
    """
    try:
        nodes = []
        edges = []
        
        # 尝试不同的概念类型查询
        concept_info = None
        concept_type = "Concept"
        center_node_id = f"concept_{concept_name}"
        
        # 先尝试作为算法查询
        alg_info = neo4j_api.get_algorithm_by_name(concept_name)
        if alg_info:
            concept_info = alg_info["algorithm"]
            concept_type = "Algorithm"
            center_node_id = f"algorithm_{concept_name}"
            
            # 添加相关题目
            for i, problem in enumerate(alg_info.get("problems", [])[:limit]):
                if problem:
                    problem_id = f"problem_{i}"
                    nodes.append(GraphNode(
                        id=problem_id,
                        label=problem.get("title", ""),
                        type="Problem",
                        properties={
                            "difficulty": problem.get("difficulty", ""),
                            "platform": problem.get("platform", "")
                        }
                    ))
                    edges.append(GraphEdge(
                        source=center_node_id,
                        target=problem_id,
                        relationship="USES_ALGORITHM"
                    ))
        
        # 尝试作为数据结构查询
        if not concept_info:
            ds_info = neo4j_api.get_data_structure_by_name(concept_name)
            if ds_info:
                concept_info = ds_info["data_structure"]
                concept_type = "DataStructure"
                center_node_id = f"data_structure_{concept_name}"
                
                # 添加相关题目
                for i, problem in enumerate(ds_info.get("problems", [])[:limit]):
                    if problem:
                        problem_id = f"problem_{i}"
                        nodes.append(GraphNode(
                            id=problem_id,
                            label=problem.get("title", ""),
                            type="Problem",
                            properties={
                                "difficulty": problem.get("difficulty", ""),
                                "platform": problem.get("platform", "")
                            }
                        ))
                        edges.append(GraphEdge(
                            source=center_node_id,
                            target=problem_id,
                            relationship="REQUIRES_DATA_STRUCTURE"
                        ))
        
        # 尝试作为技巧查询
        if not concept_info:
            tech_info = neo4j_api.get_technique_by_name(concept_name)
            if tech_info:
                concept_info = tech_info["technique"]
                concept_type = "Technique"
                center_node_id = f"technique_{concept_name}"
                
                # 添加相关题目
                for i, problem in enumerate(tech_info.get("problems", [])[:limit]):
                    if problem:
                        problem_id = f"problem_{i}"
                        nodes.append(GraphNode(
                            id=problem_id,
                            label=problem.get("title", ""),
                            type="Problem",
                            properties={
                                "difficulty": problem.get("difficulty", ""),
                                "platform": problem.get("platform", "")
                            }
                        ))
                        edges.append(GraphEdge(
                            source=center_node_id,
                            target=problem_id,
                            relationship="APPLIES_TECHNIQUE"
                        ))
        
        # 添加中心概念节点
        if concept_info:
            nodes.insert(0, GraphNode(
                id=center_node_id,
                label=concept_name,
                type=concept_type,
                properties={**concept_info, "is_center": True}
            ))
        else:
            # 如果没找到具体信息，创建一个通用概念节点
            nodes.insert(0, GraphNode(
                id=center_node_id,
                label=concept_name,
                type="Concept",
                properties={"is_center": True}
            ))
        
        return GraphData(
            nodes=nodes,
            edges=edges,
            center_node=center_node_id,
            layout_type="force"
        )
        
    except Exception as e:
        logger.error(f"获取概念图谱失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_graph_statistics(
    neo4j_api: Neo4jKnowledgeGraphAPI = Depends(get_current_neo4j_api)
):
    """
    获取知识图谱统计信息
    """
    try:
        stats = neo4j_api.get_statistics()
        return {
            "total_nodes": sum([
                stats.get("total_problems", 0),
                stats.get("total_algorithms", 0),
                stats.get("total_data_structures", 0)
            ]),
            "total_problems": stats.get("total_problems", 0),
            "total_algorithms": stats.get("total_algorithms", 0),
            "total_data_structures": stats.get("total_data_structures", 0),
            "difficulty_distribution": stats.get("difficulty_distribution", []),
            "top_categories": stats.get("top_categories", [])
        }
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 辅助函数
async def _query_problem_graph(request: GraphQueryRequest, neo4j_api: Neo4jKnowledgeGraphAPI) -> GraphData:
    """查询题目相关图谱"""
    # 实现题目图谱查询逻辑
    return await get_problem_graph(request.entity_name, request.depth, request.limit, neo4j_api)

async def _query_algorithm_graph(request: GraphQueryRequest, neo4j_api: Neo4jKnowledgeGraphAPI) -> GraphData:
    """查询算法相关图谱"""
    # 实现算法图谱查询逻辑
    return await get_concept_graph(request.entity_name, request.depth, request.limit, neo4j_api)

async def _query_data_structure_graph(request: GraphQueryRequest, neo4j_api: Neo4jKnowledgeGraphAPI) -> GraphData:
    """查询数据结构相关图谱"""
    # 实现数据结构图谱查询逻辑
    return await get_concept_graph(request.entity_name, request.depth, request.limit, neo4j_api)

async def _query_general_graph(request: GraphQueryRequest, neo4j_api: Neo4jKnowledgeGraphAPI) -> GraphData:
    """通用图谱查询"""
    # 实现通用图谱查询逻辑
    return await get_concept_graph(request.entity_name, request.depth, request.limit, neo4j_api)

# ================== 节点详情API ==================

@router.get("/problem/{problem_title}/detail")
async def get_problem_detail(
    problem_title: str,
    neo4j_api: Neo4jKnowledgeGraphAPI = Depends(get_current_neo4j_api)
):
    """
    获取题目详细信息

    - **problem_title**: 题目标题
    """
    try:
        # 获取完整题目信息
        problem_info = neo4j_api.get_problem_by_title(problem_title)

        if not problem_info:
            raise HTTPException(status_code=404, detail=f"题目 '{problem_title}' 未找到")

        # 获取相似题目
        similar_problems = neo4j_api.get_similar_problems(problem_title, limit=5)

        # 构建返回数据
        result = {
            "basic_info": {
                "title": problem_info.get("title", problem_title),
                "type": "Problem",
                "description": problem_info.get("description", ""),
                "difficulty": problem_info.get("difficulty", ""),
                "platform": problem_info.get("platform", ""),
                "category": problem_info.get("category", "")
            },
            "algorithms": [
                {"name": alg.get("name", ""), "description": alg.get("description", "")}
                for alg in problem_info.get("algorithms", [])
            ],
            "data_structures": [
                {"name": ds.get("name", ""), "description": ds.get("description", "")}
                for ds in problem_info.get("data_structures", [])
            ],
            "techniques": [
                {"name": tech.get("name", ""), "description": tech.get("description", "")}
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
            }
        }

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取题目详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/algorithm/{algorithm_name}/detail")
async def get_algorithm_detail(
    algorithm_name: str,
    neo4j_api: Neo4jKnowledgeGraphAPI = Depends(get_current_neo4j_api)
):
    """
    获取算法详细信息

    - **algorithm_name**: 算法名称
    """
    try:
        # 获取算法信息
        algorithm_info = neo4j_api.get_algorithm_by_name(algorithm_name)

        if not algorithm_info:
            raise HTTPException(status_code=404, detail=f"算法 '{algorithm_name}' 未找到")

        # 构建返回数据
        result = {
            "basic_info": {
                "title": algorithm_info.get("name", algorithm_name),
                "type": "Algorithm",
                "description": algorithm_info.get("description", ""),
                "category": algorithm_info.get("category", "")
            },
            "related_problems": [
                {
                    "title": problem.get("title", ""),
                    "difficulty": problem.get("difficulty", "")
                }
                for problem in algorithm_info.get("problems", [])
            ]
        }

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取算法详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/datastructure/{ds_name}/detail")
async def get_datastructure_detail(
    ds_name: str,
    neo4j_api: Neo4jKnowledgeGraphAPI = Depends(get_current_neo4j_api)
):
    """
    获取数据结构详细信息

    - **ds_name**: 数据结构名称
    """
    try:
        # 获取数据结构信息
        ds_info = neo4j_api.get_data_structure_by_name(ds_name)

        if not ds_info:
            raise HTTPException(status_code=404, detail=f"数据结构 '{ds_name}' 未找到")

        # 构建返回数据
        result = {
            "basic_info": {
                "title": ds_info.get("name", ds_name),
                "type": "DataStructure",
                "description": ds_info.get("description", ""),
                "category": ds_info.get("category", "")
            },
            "related_problems": [
                {
                    "title": problem.get("title", ""),
                    "difficulty": problem.get("difficulty", "")
                }
                for problem in ds_info.get("problems", [])
            ]
        }

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据结构详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/node/{node_name}/detail")
async def get_node_detail(
    node_name: str,
    node_type: str = Query(default="Unknown", description="节点类型"),
    neo4j_api: Neo4jKnowledgeGraphAPI = Depends(get_current_neo4j_api)
):
    """
    获取通用节点详细信息

    - **node_name**: 节点名称
    - **node_type**: 节点类型（可选，默认为Unknown）
    """
    try:
        # 如果节点类型未知，尝试从Neo4j中查询节点类型
        if node_type == "Unknown" or not node_type:
            node_info = neo4j_api.get_node_by_name(node_name)
            if node_info:
                node_type = node_info.get("type", "Unknown")
                logger.info(f"从Neo4j查询到节点类型: {node_name} -> {node_type}")

        # 根据节点类型调用相应的方法
        if node_type == "Problem":
            return await get_problem_detail(node_name, neo4j_api)
        elif node_type == "Algorithm":
            return await get_algorithm_detail(node_name, neo4j_api)
        elif node_type == "DataStructure":
            return await get_datastructure_detail(node_name, neo4j_api)
        else:
            # 尝试查询通用节点信息
            node_info = neo4j_api.get_node_by_name(node_name)
            if node_info:
                node_data = node_info.get("node", {})
                result = {
                    "basic_info": {
                        "title": node_name,
                        "type": node_type,
                        "description": node_data.get("description", f"{node_type}类型的知识节点"),
                        "category": node_data.get("category", ""),
                        "properties": node_data
                    }
                }
                return result
            else:
                raise HTTPException(status_code=404, detail=f"节点 '{node_name}' 未找到")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取节点详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
