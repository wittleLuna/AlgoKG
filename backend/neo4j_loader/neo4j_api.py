import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from neo4j import GraphDatabase
from collections import defaultdict

logger = logging.getLogger(__name__)

class Neo4jKnowledgeGraphAPI:
    """
    Neo4j知识图谱API - 全本体、支持multi_agent_qa全流程的接口集合
    """

    def __init__(self, uri: str = "bolt://localhost:7687",
                 user: str = "neo4j",
                 password: str = "Abcd1234!"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    

    def close(self):
        if self.driver:
            self.driver.close()
    # 
    # ================== 题目相关 ==================
    def get_problem_by_title(self, title: str) -> Optional[Dict]:
        """根据题目title精确获取题目信息（含标签/技巧/解法/复杂度/代码/洞察/图片/步骤等）"""
        with self.driver.session() as session:
            query = """
            MATCH (p:Problem {title: $title})
            OPTIONAL MATCH (p)-[:USES_ALGORITHM]->(alg:Algorithm)
            OPTIONAL MATCH (p)-[:REQUIRES_DATA_STRUCTURE]->(ds:DataStructure)
            OPTIONAL MATCH (p)-[:APPLIES_TECHNIQUE]->(tech:Technique)
            OPTIONAL MATCH (p)-[:HAS_SOLUTION]->(sol:Solution)
            OPTIONAL MATCH (sol)-[:IMPLEMENTED_IN]->(lang:Language)
            OPTIONAL MATCH (p)-[:HAS_TIME_COMPLEXITY]->(tc:Complexity)
            OPTIONAL MATCH (p)-[:HAS_SPACE_COMPLEXITY]->(sc:Complexity)
            OPTIONAL MATCH (p)-[:PROVIDES_INSIGHT]->(ins:Insight)
            OPTIONAL MATCH (p)-[:BELONGS_TO_CATEGORY]->(cat:Category)
            OPTIONAL MATCH (p)-[:HAS_DIFFICULTY]->(dif:Difficulty)
            OPTIONAL MATCH (p)-[:HAS_IMAGE]->(img:Image)
            OPTIONAL MATCH (p)-[:HAS_STEP]->(step:Step)
            RETURN p,
                collect(DISTINCT alg) as algorithms,
                collect(DISTINCT ds) as data_structures,
                collect(DISTINCT tech) as techniques,
                collect(DISTINCT sol) as solutions,
                collect(DISTINCT lang) as languages,
                collect(DISTINCT tc) as time_complexities,
                collect(DISTINCT sc) as space_complexities,
                collect(DISTINCT ins) as insights,
                collect(DISTINCT cat) as categories,
                collect(DISTINCT dif) as difficulties,
                collect(DISTINCT img) as images,
                collect(DISTINCT step) as steps
            LIMIT 1
            """
            try:
                result = session.run(query, title=title).single()
                if not result: return None
                p = result['p']

                # 处理图片数据
                images = []
                for img in result['images']:
                    if img:
                        images.append({
                            'url': img.get('url', ''),
                            'description': img.get('description', ''),
                            'type': img.get('type', 'diagram')
                        })

                # 处理步骤数据
                steps = []
                for step in result['steps']:  
                    if step:
                        steps.append({
                            'order': step.get('order', 0),
                            'title': step.get('title', ''),
                            'description': step.get('description', ''),
                            'code': step.get('code', ''),
                            'explanation': step.get('explanation', '')
                        })

                # 按顺序排序步骤
                steps.sort(key=lambda x: x['order'])

                # 清理Neo4j节点对象，只保留关键属性
                def extract_node_info(node):
                    """从Neo4j节点中提取关键信息"""
                    if hasattr(node, 'get'):
                        return {
                            'name': node.get('name', ''),
                            'title': node.get('title', ''),
                            'description': node.get('description', ''),
                            'category': node.get('category', ''),
                            'type': node.get('type', '')
                        }
                    elif isinstance(node, dict):
                        return {
                            'name': node.get('name', ''),
                            'title': node.get('title', ''),
                            'description': node.get('description', ''),
                            'category': node.get('category', ''),
                            'type': node.get('type', '')
                        }
                    else:
                        return {'name': str(node), 'title': str(node)}

                return {
                    'title': p.get('title'),
                    'description': p.get('description'),
                    'difficulty': p.get('difficulty'),
                    'url': p.get('url'),
                    'platform': p.get('platform'),
                    'category': p.get('category'),
                    'algorithms': [extract_node_info(a) for a in result['algorithms'] if a],
                    'data_structures': [extract_node_info(d) for d in result['data_structures'] if d],
                    'techniques': [extract_node_info(t) for t in result['techniques'] if t],
                    'solutions': [extract_node_info(s) for s in result['solutions'] if s],
                    'languages': [extract_node_info(l) for l in result['languages'] if l],
                    'time_complexities': [extract_node_info(tc) for tc in result['time_complexities'] if tc],
                    'space_complexities': [extract_node_info(sc) for sc in result['space_complexities'] if sc],
                    'insights': [extract_node_info(ins) for ins in result['insights'] if ins],
                    'categories': [extract_node_info(cat) for cat in result['categories'] if cat],
                    'difficulties': [extract_node_info(dif) for dif in result['difficulties'] if dif],
                    'images': images,
                    'step_by_step': steps
                }
            except Exception as e:
                logger.error(f"get_problem_by_title error: {e}")
                return None

    def search_problems(self, keyword: str, limit=15) -> List[Dict]:
        """按关键词（模糊）搜索题目"""
        with self.driver.session() as session:
            query = """
            MATCH (p:Problem)
            WHERE toLower(p.title) CONTAINS toLower($keyword)
               OR toLower(p.description) CONTAINS toLower($keyword)
               OR toLower(p.category) CONTAINS toLower($keyword)
            RETURN p
            ORDER BY p.title
            LIMIT $limit
            """
            try:
                # 清理Neo4j节点对象，只返回关键属性
                results = []
                for record in session.run(query, keyword=keyword, limit=limit):
                    p = record['p']
                    if hasattr(p, 'get'):
                        results.append({
                            'title': p.get('title', ''),
                            'description': p.get('description', ''),
                            'difficulty': p.get('difficulty', ''),
                            'url': p.get('url', ''),
                            'platform': p.get('platform', ''),
                            'category': p.get('category', ''),
                            'id': p.get('id', '')
                        })
                    elif isinstance(p, dict):
                        results.append(p)
                    else:
                        results.append({'title': str(p)})
                return results
            except Exception as e:
                logger.error(f"search_problems error: {e}")
                return []

    # ================== 概念/算法/结构/技巧 ==================
    def get_algorithm_by_name(self, name: str) -> Optional[Dict]:
        """获取算法实体及相关题目"""
        with self.driver.session() as session:
            query = """
            MATCH (a:Algorithm)
            WHERE toLower(a.name) CONTAINS toLower($name)
            OPTIONAL MATCH (a)<-[:USES_ALGORITHM]-(p:Problem)
            RETURN a, collect(p) as problems
            LIMIT 1
            """
            try:
                record = session.run(query, name=name).single()
                if not record: return None
                return {
                    "algorithm": record['a'],
                    "problems": [p for p in record['problems'] if p]
                }
            except Exception as e:
                logger.error(f"get_algorithm_by_name error: {e}")
                return None

    def get_data_structure_by_name(self, name: str) -> Optional[Dict]:
        """获取数据结构实体及相关题目"""
        with self.driver.session() as session:
            query = """
            MATCH (ds:DataStructure)
            WHERE toLower(ds.name) CONTAINS toLower($name)
            OPTIONAL MATCH (ds)<-[:REQUIRES_DATA_STRUCTURE]-(p:Problem)
            RETURN ds, collect(p) as problems
            LIMIT 1
            """
            try:
                record = session.run(query, name=name).single()
                if not record: return None
                return {
                    "data_structure": record['ds'],
                    "problems": [p for p in record['problems'] if p]
                }
            except Exception as e:
                logger.error(f"get_data_structure_by_name error: {e}")
                return None

    def get_technique_by_name(self, name: str) -> Optional[Dict]:
        """获取技巧实体及相关题目"""
        with self.driver.session() as session:
            query = """
            MATCH (t:Technique)
            WHERE toLower(t.name) CONTAINS toLower($name)
            OPTIONAL MATCH (t)<-[:APPLIES_TECHNIQUE]-(p:Problem)
            RETURN t, collect(p) as problems
            LIMIT 1
            """
            try:
                record = session.run(query, name=name).single()
                if not record: return None
                return {
                    "technique": record['t'],
                    "problems": [p for p in record['problems'] if p]
                }
            except Exception as e:
                logger.error(f"get_technique_by_name error: {e}")
                return None

    def get_node_by_name(self, name: str) -> Optional[Dict]:
        """通用节点查询 - 根据名称查找任意类型的节点"""
        with self.driver.session() as session:
            query = """
            MATCH (n)
            WHERE (n:Problem AND (toLower(n.title) = toLower($name) OR toLower(n.title) CONTAINS toLower($name)))
               OR (n:Algorithm AND (toLower(n.name) = toLower($name) OR toLower(n.name) CONTAINS toLower($name)))
               OR (n:DataStructure AND (toLower(n.name) = toLower($name) OR toLower(n.name) CONTAINS toLower($name)))
               OR (n:Technique AND (toLower(n.name) = toLower($name) OR toLower(n.name) CONTAINS toLower($name)))
            RETURN n, labels(n) as node_labels
            ORDER BY
                CASE
                    WHEN toLower(n.title) = toLower($name) OR toLower(n.name) = toLower($name) THEN 1
                    ELSE 2
                END
            LIMIT 1
            """
            try:
                record = session.run(query, name=name).single()
                if not record: return None

                node = record['n']
                labels = record['node_labels']

                # 确定节点类型
                node_type = None
                if 'Problem' in labels:
                    node_type = 'Problem'
                elif 'Algorithm' in labels:
                    node_type = 'Algorithm'
                elif 'DataStructure' in labels:
                    node_type = 'DataStructure'
                elif 'Technique' in labels:
                    node_type = 'Technique'
                else:
                    node_type = labels[0] if labels else 'Unknown'

                return {
                    "node": dict(node),
                    "type": node_type,
                    "labels": labels,
                    "name": node.get('name') or node.get('title', ''),
                    "title": node.get('title') or node.get('name', '')
                }
            except Exception as e:
                logger.error(f"get_node_by_name error: {e}")
                return None

    # ================== 路径/统计/关系 ==================
    def get_learning_path(self, concept: str, limit=10) -> List[Dict]:
        """获取某概念的学习路径（从易到难的题目链路）"""
        with self.driver.session() as session:
            query = """
            MATCH path=(p1:Problem)-[:PREREQUISITE_OF*1..3]->(p2:Problem)
            WHERE toLower(p1.category) CONTAINS toLower($concept) OR toLower(p1.title) CONTAINS toLower($concept)
            RETURN p1.title as start_title, p1.difficulty as start_difficulty,
                   p2.title as end_title, p2.difficulty as end_difficulty, length(path) as steps
            ORDER BY steps
            LIMIT $limit
            """
            try:
                return [dict(record) for record in session.run(query, concept=concept, limit=limit)]
            except Exception as e:
                logger.error(f"get_learning_path error: {e}")
                return []

    def get_similar_problems(self, problem_title: str, limit=10) -> List[Dict]:
        """获取与某题相似的题目（可用于推荐/多跳检索）"""
        with self.driver.session() as session:
            query = """
            MATCH (p1:Problem {title: $problem_title})-[r:SIMILAR_TO]-(p2:Problem)
            RETURN p2.title as title, p2.difficulty as difficulty, p2.category as category, r.confidence as similarity_score
            ORDER BY similarity_score DESC
            LIMIT $limit
            """
            try:
                return [dict(record) for record in session.run(query, problem_title=problem_title, limit=limit)]
            except Exception as e:
                logger.error(f"get_similar_problems error: {e}")
                return []

    def get_statistics(self) -> Dict:
        """获取图谱统计信息"""
        with self.driver.session() as session:
            queries = {
                'total_problems': "MATCH (p:Problem) RETURN count(p) as count",
                'total_algorithms': "MATCH (a:Algorithm) RETURN count(a) as count",
                'total_data_structures': "MATCH (ds:DataStructure) RETURN count(ds) as count",
                'difficulty_distribution': "MATCH (p:Problem) RETURN p.difficulty as difficulty, count(p) as count",
                'top_categories': "MATCH (p:Problem) RETURN p.category as category, count(p) as count ORDER BY count DESC LIMIT 10"
            }
            stats = {}
            for key, query in queries.items():
                try:
                    result = session.run(query)
                    if key.startswith("total_"):
                        stats[key] = result.single()['count']
                    else:
                        stats[key] = [dict(record) for record in result]
                except Exception as e:
                    logger.error(f"统计查询失败 {key}: {e}")
                    stats[key] = 0 if key.startswith('total_') else []
            return stats

    # ========== 高阶扩展接口：按实体全量查询、批量导入 ==========
    def get_entities_by_type(self, entity_type: str, limit=100) -> List[Dict]:
        """获取指定类型的所有实体（支持 Problem, Algorithm, DataStructure, Technique, ...）"""
        with self.driver.session() as session:
            query = f"MATCH (n:{entity_type}) RETURN n LIMIT $limit"
            try:
                # 清理Neo4j节点对象，只返回关键属性
                results = []
                for record in session.run(query, limit=limit):
                    n = record['n']
                    if hasattr(n, 'get'):
                        results.append({
                            'name': n.get('name', ''),
                            'title': n.get('title', ''),
                            'description': n.get('description', ''),
                            'category': n.get('category', ''),
                            'type': entity_type,
                            'id': n.get('id', ''),
                            'difficulty': n.get('difficulty', ''),
                            'url': n.get('url', ''),
                            'platform': n.get('platform', '')
                        })
                    elif isinstance(n, dict):
                        results.append(n)
                    else:
                        results.append({'name': str(n), 'type': entity_type})
                return results
            except Exception as e:
                logger.error(f"get_entities_by_type error: {e}")
                return []

    def batch_import_entities(self, entities: List[Dict], entity_type: str):
        """批量导入实体（实体需有唯一id/属性）"""
        with self.driver.session() as session:
            cypher = f"""
            UNWIND $entities AS entity
            MERGE (n:{entity_type} {{id: entity.id}})
            SET n += entity
            """
            try:
                session.run(cypher, entities=entities)
                logger.info(f"批量导入{len(entities)}个{entity_type}实体成功")
            except Exception as e:
                logger.error(f"批量导入实体失败: {e}")

    def batch_import_relationships(self, relationships: List[Dict], rel_type: str):
        """批量导入关系，关系需有 source/target 字段"""
        with self.driver.session() as session:
            cypher = f"""
            UNWIND $relationships AS rel
            MATCH (a {{id: rel.source}})
            MATCH (b {{id: rel.target}})
            MERGE (a)-[r:{rel_type}]->(b)
            SET r += rel
            """
            try:
                session.run(cypher, relationships=relationships)
                logger.info(f"批量导入{len(relationships)}条{rel_type}关系成功")
            except Exception as e:
                logger.error(f"批量导入关系失败: {e}")

    # ========== 其它扩展接口可继续补充 ==========

# 用法示例：
# api = Neo4jKnowledgeGraphAPI()
# api.get_problem_by_title("复原IP地址")
# api.get_algorithm_by_name("BFS")
# api.get_similar_problems("复原IP地址")

    def run_query(self, cypher: str, params: Optional[dict] = None) -> list:
        """通用cypher查询接口，multi_agent_qa智能体兼容"""
        with self.driver.session() as session:
            try:
                result = session.run(cypher, **(params or {}))
                return [record.data() for record in result]
            except Exception as e:
                logger.error(f"run_query error: {e}")
                return []
