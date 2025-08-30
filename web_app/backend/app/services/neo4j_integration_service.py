"""
Neo4j知识图谱集成服务
将笔记中提取的实体集成到Neo4j知识图谱中
"""
import sys
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# 添加backend路径以导入neo4j_loader模块
backend_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'backend')
sys.path.append(backend_path)

try:
    from backend.neo4j_loader.extractor2_modified import Entity, Relationship, ExtendedNeo4jKnowledgeGraph
    NEO4J_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Neo4j集成模块不可用: {e}")
    NEO4J_AVAILABLE = False
    Entity = None
    Relationship = None
    ExtendedNeo4jKnowledgeGraph = None

from app.core.config import get_settings

logger = logging.getLogger(__name__)

class NoteEntityIntegrationService:
    """笔记实体集成服务"""
    
    def __init__(self):
        self.neo4j_available = NEO4J_AVAILABLE
        self.graph_db = None
        
        if self.neo4j_available:
            try:
                settings = get_settings()
                # 从配置中获取Neo4j连接信息
                neo4j_uri = getattr(settings, 'NEO4J_URI', 'bolt://localhost:7687')
                neo4j_user = getattr(settings, 'NEO4J_USER', 'neo4j')
                neo4j_password = getattr(settings, 'NEO4J_PASSWORD', 'password')
                
                self.graph_db = ExtendedNeo4jKnowledgeGraph(neo4j_uri, neo4j_user, neo4j_password)
                logger.info("Neo4j知识图谱连接成功")
            except Exception as e:
                logger.error(f"Neo4j连接失败: {e}")
                self.neo4j_available = False
        else:
            logger.warning("Neo4j集成不可用，将使用模拟模式")
    
    async def integrate_note_entities(self, note_id: str, entities: List[Dict], relations: List[Dict]) -> Dict[str, Any]:
        """将笔记实体集成到知识图谱中"""
        try:
            if not self.neo4j_available or not self.graph_db:
                return await self._simulate_integration(note_id, entities, relations)
            
            # 转换为Neo4j实体格式
            neo4j_entities = self._convert_to_neo4j_entities(entities, note_id)
            neo4j_relations = self._convert_to_neo4j_relations(relations, note_id)
            
            # 检查现有实体并决定合并策略
            integration_results = await self._analyze_entity_integration(neo4j_entities)
            
            # 存储新实体和增强现有实体
            await self._store_entities_with_strategy(neo4j_entities, integration_results)
            
            # 存储关系
            if neo4j_relations:
                self.graph_db.store_relationships(neo4j_relations)
            
            # 返回集成结果
            return {
                'success': True,
                'note_id': note_id,
                'integrated_entities': len(neo4j_entities),
                'integrated_relations': len(neo4j_relations),
                'integration_details': integration_results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"实体集成失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'note_id': note_id,
                'timestamp': datetime.now().isoformat()
            }
    
    def _convert_to_neo4j_entities(self, entities: List[Dict], note_id: str) -> List[Entity]:
        """转换为Neo4j实体格式"""
        neo4j_entities = []
        
        for entity in entities:
            # 映射实体类型到Neo4j标签
            entity_type = self._map_entity_type(entity.get('type', 'Unknown'))
            
            neo4j_entity = Entity(
                id=entity.get('id', f"note_{note_id}_{hash(entity.get('name', ''))%10000}"),
                name=entity.get('name', ''),
                type=entity_type,
                properties={
                    'description': entity.get('description', ''),
                    'confidence': entity.get('confidence', 1.0),
                    'source_type': 'note',
                    'source_note_id': note_id,
                    'extracted_at': datetime.now().isoformat()
                },
                source_file=f"note_{note_id}"
            )
            neo4j_entities.append(neo4j_entity)
        
        return neo4j_entities
    
    def _convert_to_neo4j_relations(self, relations: List[Dict], note_id: str) -> List[Relationship]:
        """转换为Neo4j关系格式"""
        neo4j_relations = []
        
        for relation in relations:
            neo4j_relation = Relationship(
                source=relation.get('source', ''),
                target=relation.get('target', ''),
                type=self._map_relation_type(relation.get('type', 'RELATED_TO')),
                properties={
                    'confidence': relation.get('confidence', 1.0),
                    'source_note_id': note_id,
                    'created_at': datetime.now().isoformat()
                },
                confidence=relation.get('confidence', 1.0),
                source_file=f"note_{note_id}"
            )
            neo4j_relations.append(neo4j_relation)
        
        return neo4j_relations
    
    def _map_entity_type(self, entity_type: str) -> str:
        """映射实体类型到Neo4j标签"""
        type_mapping = {
            'algorithm_paradigm': 'AlgorithmParadigm',
            'data_structure': 'DataStructure',
            'technique': 'Technique',
            'problem_type': 'ProblemType',
            'complexity': 'Complexity',
            'concept': 'Concept'
        }
        return type_mapping.get(entity_type, 'Entity')
    
    def _map_relation_type(self, relation_type: str) -> str:
        """映射关系类型"""
        type_mapping = {
            'uses': 'USES',
            'is_a': 'IS_A',
            'part_of': 'PART_OF',
            'related_to': 'RELATED_TO',
            'implements': 'IMPLEMENTS',
            'solves': 'SOLVES'
        }
        return type_mapping.get(relation_type, 'RELATED_TO')
    
    async def _analyze_entity_integration(self, entities: List[Entity]) -> Dict[str, Any]:
        """分析实体集成策略"""
        integration_results = {
            'new_entities': [],
            'enhanced_entities': [],
            'existing_entities': [],
            'merge_decisions': []
        }
        
        for entity in entities:
            # 检查实体是否已存在
            existing_entity = await self._find_existing_entity(entity)
            
            if existing_entity:
                # 决定是否合并
                should_merge, merge_strategy = await self._should_merge_entities(entity, existing_entity)
                
                if should_merge:
                    integration_results['enhanced_entities'].append({
                        'entity': entity,
                        'existing': existing_entity,
                        'strategy': merge_strategy
                    })
                else:
                    integration_results['existing_entities'].append(entity)
            else:
                integration_results['new_entities'].append(entity)
        
        return integration_results
    
    async def _find_existing_entity(self, entity: Entity) -> Optional[Dict]:
        """查找现有实体"""
        if not self.graph_db:
            return None
        
        try:
            with self.graph_db.driver.session() as session:
                # 按名称和类型查找
                result = session.run(
                    f"MATCH (n:{entity.type}) WHERE n.name = $name RETURN n",
                    name=entity.name
                )
                record = result.single()
                return dict(record['n']) if record else None
        except Exception as e:
            logger.error(f"查找现有实体失败: {e}")
            return None
    
    async def _should_merge_entities(self, new_entity: Entity, existing_entity: Dict) -> Tuple[bool, str]:
        """判断是否应该合并实体"""
        # 简单的合并策略：如果名称相同且类型相同，则增强现有实体
        if (new_entity.name.lower() == existing_entity.get('name', '').lower() and 
            new_entity.type == existing_entity.get('type', '')):
            return True, 'enhance_properties'
        
        return False, 'no_merge'
    
    async def _store_entities_with_strategy(self, entities: List[Entity], integration_results: Dict):
        """根据策略存储实体"""
        # 存储新实体
        if integration_results['new_entities']:
            self.graph_db.store_entities(integration_results['new_entities'])
            logger.info(f"存储了 {len(integration_results['new_entities'])} 个新实体")
        
        # 增强现有实体
        for enhanced in integration_results['enhanced_entities']:
            await self._enhance_existing_entity(enhanced['entity'], enhanced['existing'])
    
    async def _enhance_existing_entity(self, new_entity: Entity, existing_entity: Dict):
        """增强现有实体"""
        try:
            with self.graph_db.driver.session() as session:
                # 更新实体属性
                session.run(
                    f"""
                    MATCH (n:{new_entity.type}) WHERE n.name = $name
                    SET n.last_enhanced = $timestamp,
                        n.enhancement_count = COALESCE(n.enhancement_count, 0) + 1,
                        n.source_notes = COALESCE(n.source_notes, []) + [$source_note]
                    """,
                    name=new_entity.name,
                    timestamp=datetime.now().isoformat(),
                    source_note=new_entity.source_file
                )
                logger.info(f"增强了实体: {new_entity.name}")
        except Exception as e:
            logger.error(f"增强实体失败: {e}")
    
    async def _simulate_integration(self, note_id: str, entities: List[Dict], relations: List[Dict]) -> Dict[str, Any]:
        """模拟集成（当Neo4j不可用时）"""
        logger.info(f"模拟集成笔记 {note_id} 的 {len(entities)} 个实体和 {len(relations)} 个关系")
        
        return {
            'success': True,
            'note_id': note_id,
            'integrated_entities': len(entities),
            'integrated_relations': len(relations),
            'integration_details': {
                'new_entities': entities,
                'enhanced_entities': [],
                'existing_entities': [],
                'merge_decisions': []
            },
            'timestamp': datetime.now().isoformat(),
            'mode': 'simulation'
        }

# 全局服务实例
_integration_service = None

def get_neo4j_integration_service() -> NoteEntityIntegrationService:
    """获取Neo4j集成服务实例"""
    global _integration_service
    if _integration_service is None:
        _integration_service = NoteEntityIntegrationService()
    return _integration_service
