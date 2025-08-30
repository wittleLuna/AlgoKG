"""
笔记服务模块
支持用户笔记的上传、解析、实体抽取和管理
"""
import logging
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import tempfile
import os

from app.models.note import (
    Note, NoteUploadRequest, NoteResponse, NoteListRequest, NoteListResponse,
    FileFormat, NoteType, ContentAnalysis
)
from app.services.file_parser import FileParserService
from app.services.content_analyzer import ContentAnalyzerService
from app.services.note_entity_extractor import get_note_entity_extractor, NoteExtractionResult
from app.services.neo4j_integration_service import get_neo4j_integration_service
from app.core.database import get_database

logger = logging.getLogger(__name__)

class NoteService:
    """笔记服务"""
    
    def __init__(self):
        self.db = get_database()
        self.file_parser = FileParserService()
        self.content_analyzer = ContentAnalyzerService()
        self.entity_extractor = get_note_entity_extractor()
        self.neo4j_integration = get_neo4j_integration_service()
    
    async def upload_note(self, request: NoteUploadRequest, user_id: str) -> NoteResponse:
        """上传并处理笔记"""
        try:
            logger.info(f"用户 {user_id} 上传笔记: {request.title}")
            
            # 生成笔记ID
            note_id = str(uuid.uuid4())
            
            # 解析文件内容
            parsed_content = await self._parse_file_content(request)
            
            # 分析内容
            content_analysis = await self._analyze_content(parsed_content['content'])
            
            # 抽取实体（如果启用）
            extraction_result = None
            if request.extract_entities:
                extraction_result = await self.entity_extractor.extract_entities_from_note(
                    note_id, parsed_content['content'], request.title
                )

                # 将提取的实体集成到Neo4j知识图谱中
                if extraction_result and (extraction_result.entities or extraction_result.relations):
                    try:
                        entities_data = [
                            {
                                'id': entity.id,
                                'name': entity.name,
                                'type': entity.type,
                                'description': entity.description,
                                'confidence': entity.confidence
                            }
                            for entity in extraction_result.entities
                        ]

                        relations_data = [
                            {
                                'source': rel.source_entity,
                                'target': rel.target_entity,
                                'type': rel.relation_type,
                                'confidence': rel.confidence
                            }
                            for rel in extraction_result.relations
                        ]

                        integration_result = await self.neo4j_integration.integrate_note_entities(
                            note_id, entities_data, relations_data
                        )

                        logger.info(f"Neo4j集成结果: {integration_result}")

                    except Exception as e:
                        logger.error(f"Neo4j集成失败: {e}")
                        # 不影响笔记保存，继续执行
            
            # 保存到数据库
            note = await self._save_note_to_db(
                note_id=note_id,
                request=request,
                user_id=user_id,
                parsed_content=parsed_content,
                content_analysis=content_analysis,
                extraction_result=extraction_result
            )
            
            logger.info(f"笔记 {note_id} 上传成功")
            return NoteResponse(
                id=note.id,
                title=note.title,
                content=note.content,
                note_type=note.note_type,
                file_format=note.file_format,
                tags=note.tags,
                description=note.description,
                is_public=note.is_public,
                user_id=note.user_id,
                created_at=note.created_at,
                updated_at=note.updated_at,
                analysis_data=note.analysis_data,
                entities_extracted=extraction_result is not None,
                entity_count=len(extraction_result.entities) if extraction_result else 0
            )
            
        except Exception as e:
            logger.error(f"上传笔记失败: {e}")
            raise Exception(f"笔记上传失败: {str(e)}")
    
    async def _parse_file_content(self, request: NoteUploadRequest) -> Dict[str, Any]:
        """解析文件内容"""
        if request.file_content:
            # 直接文本内容
            return {
                'content': request.file_content,
                'metadata': {
                    'format': 'text',
                    'source': 'direct_input'
                }
            }
        elif request.file_data:
            # 文件上传
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{request.file_format}") as tmp_file:
                tmp_file.write(request.file_data)
                tmp_file_path = tmp_file.name
            
            try:
                # 解析文件
                parsed_result = await self.file_parser.parse_file(tmp_file_path, request.file_format)
                return parsed_result
            finally:
                # 清理临时文件
                os.unlink(tmp_file_path)
        else:
            raise ValueError("必须提供文件内容或文件数据")
    
    async def _analyze_content(self, content: str) -> ContentAnalysis:
        """分析内容"""
        try:
            analysis = await self.content_analyzer.analyze_content(content)
            return ContentAnalysis(
                word_count=analysis.get('word_count', 0),
                algorithm_keywords=analysis.get('algorithm_keywords', []),
                complexity_mentions=analysis.get('complexity_mentions', []),
                code_blocks=analysis.get('code_blocks', []),
                difficulty_level=analysis.get('difficulty_level', 'unknown'),
                topics=analysis.get('topics', []),
                summary=analysis.get('summary', '')
            )
        except Exception as e:
            logger.warning(f"内容分析失败: {e}")
            return ContentAnalysis(
                word_count=len(content.split()),
                algorithm_keywords=[],
                complexity_mentions=[],
                code_blocks=[],
                difficulty_level='unknown',
                topics=[],
                summary=content[:200] + "..." if len(content) > 200 else content
            )
    
    async def _save_note_to_db(
        self,
        note_id: str,
        request: NoteUploadRequest,
        user_id: str,
        parsed_content: Dict[str, Any],
        content_analysis: ContentAnalysis,
        extraction_result: Optional[NoteExtractionResult]
    ) -> Note:
        """保存笔记到数据库"""
        
        # 准备分析数据
        analysis_data = {
            'content_analysis': content_analysis.dict(),
            'parsing_metadata': parsed_content.get('metadata', {}),
        }
        
        # 如果有实体抽取结果，添加到分析数据中
        if extraction_result:
            analysis_data['entity_extraction'] = {
                'entities': [
                    {
                        'id': entity.id,
                        'name': entity.name,
                        'type': entity.type,
                        'description': entity.description,
                        'confidence': entity.confidence
                    }
                    for entity in extraction_result.entities
                ],
                'relations': [
                    {
                        'source': rel.source_entity,
                        'target': rel.target_entity,
                        'type': rel.relation_type,
                        'confidence': rel.confidence
                    }
                    for rel in extraction_result.relations
                ],
                'metadata': extraction_result.extraction_metadata
            }
        
        # 插入数据库
        self.db.execute_update(
            """INSERT INTO notes (
                id, title, content, processed_content, note_type, file_format, 
                file_size, tags, description, is_public, user_id, analysis_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                note_id,
                request.title,
                parsed_content['content'],
                json.dumps(parsed_content),
                request.note_type.value,
                request.file_format.value,
                len(parsed_content['content']),
                json.dumps(request.tags),
                request.description,
                request.is_public,
                user_id,
                json.dumps(analysis_data)
            )
        )
        
        # 返回笔记对象
        return Note(
            id=note_id,
            title=request.title,
            content=parsed_content['content'],
            note_type=request.note_type,
            file_format=request.file_format,
            file_size=len(parsed_content['content']),
            tags=request.tags,
            description=request.description,
            is_public=request.is_public,
            user_id=user_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            analysis_data=analysis_data
        )
    
    async def get_user_notes(self, user_id: str, request: NoteListRequest) -> NoteListResponse:
        """获取用户笔记列表"""
        try:
            # 构建查询条件
            where_conditions = ["user_id = ?"]
            params = [user_id]
            
            if request.note_type:
                where_conditions.append("note_type = ?")
                params.append(request.note_type.value)
            
            if request.search_query:
                where_conditions.append("(title LIKE ? OR content LIKE ?)")
                search_term = f"%{request.search_query}%"
                params.extend([search_term, search_term])
            
            # 计算总数
            count_query = f"SELECT COUNT(*) as total FROM notes WHERE {' AND '.join(where_conditions)}"
            total_result = self.db.execute_query(count_query, tuple(params))
            total = total_result[0]['total'] if total_result else 0
            
            # 获取笔记列表
            offset = (request.page - 1) * request.size
            list_query = f"""
                SELECT * FROM notes 
                WHERE {' AND '.join(where_conditions)}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([request.size, offset])
            
            notes_data = self.db.execute_query(list_query, tuple(params))
            
            # 转换为笔记对象
            notes = []
            for note_data in notes_data:
                notes.append(self._db_row_to_note_response(note_data))
            
            return NoteListResponse(
                notes=notes,
                total=total,
                page=request.page,
                size=request.size
            )
            
        except Exception as e:
            logger.error(f"获取用户笔记失败: {e}")
            raise Exception(f"获取笔记列表失败: {str(e)}")
    
    def _db_row_to_note_response(self, row: Dict) -> NoteResponse:
        """将数据库行转换为笔记响应对象"""
        analysis_data = json.loads(row.get('analysis_data', '{}'))
        entity_extraction = analysis_data.get('entity_extraction', {})
        
        return NoteResponse(
            id=row['id'],
            title=row['title'],
            content=row['content'],
            note_type=NoteType(row['note_type']),
            file_format=FileFormat(row['file_format']),
            tags=json.loads(row.get('tags', '[]')),
            description=row.get('description', ''),
            is_public=bool(row.get('is_public', False)),
            user_id=row['user_id'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            analysis_data=analysis_data,
            entities_extracted=bool(entity_extraction),
            entity_count=len(entity_extraction.get('entities', []))
        )

    async def get_user_notes(self, user_id: str, request: NoteListRequest) -> NoteListResponse:
        """获取用户笔记列表"""
        try:
            # 构建查询条件
            where_conditions = ["user_id = ?"]
            params = [user_id]

            if request.note_type:
                where_conditions.append("note_type = ?")
                params.append(request.note_type.value)

            if request.search_query:
                where_conditions.append("(title LIKE ? OR content LIKE ?)")
                search_term = f"%{request.search_query}%"
                params.extend([search_term, search_term])

            # 计算总数
            count_query = f"SELECT COUNT(*) as total FROM notes WHERE {' AND '.join(where_conditions)}"
            total_result = self.db.execute_query(count_query, tuple(params))
            total = total_result[0]['total'] if total_result else 0

            # 获取笔记列表
            offset = (request.page - 1) * request.size
            list_query = f"""
                SELECT * FROM notes
                WHERE {' AND '.join(where_conditions)}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([request.size, offset])

            notes_data = self.db.execute_query(list_query, tuple(params))

            # 转换为笔记对象
            notes = []
            for note_data in notes_data:
                notes.append(self._db_row_to_note_response(note_data))

            return NoteListResponse(
                notes=notes,
                total=total,
                page=request.page,
                size=request.size
            )

        except Exception as e:
            logger.error(f"获取用户笔记失败: {e}")
            raise Exception(f"获取笔记列表失败: {str(e)}")

    def _db_row_to_note_response(self, row: Dict) -> NoteResponse:
        """将数据库行转换为笔记响应对象"""
        analysis_data = json.loads(row.get('analysis_data', '{}'))
        entity_extraction = analysis_data.get('entity_extraction', {})

        return NoteResponse(
            id=row['id'],
            title=row['title'],
            content=row['content'],
            note_type=NoteType(row['note_type']),
            file_format=FileFormat(row['file_format']),
            tags=json.loads(row.get('tags', '[]')),
            description=row.get('description', ''),
            is_public=bool(row.get('is_public', False)),
            user_id=row['user_id'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            analysis_data=analysis_data,
            entities_extracted=bool(entity_extraction),
            entity_count=len(entity_extraction.get('entities', []))
        )

    async def get_note_by_id(self, note_id: str, user_id: str) -> NoteResponse:
        """获取单个笔记详情"""
        try:
            # 查询笔记
            notes = self.db.execute_query(
                "SELECT * FROM notes WHERE id = ? AND user_id = ?",
                (note_id, user_id)
            )

            if not notes:
                raise Exception("笔记不存在或无权限访问")

            note_data = notes[0]
            return self._db_row_to_note_response(note_data)

        except Exception as e:
            logger.error(f"获取笔记详情失败: {e}")
            raise Exception(f"获取笔记详情失败: {str(e)}")

    async def delete_note(self, note_id: str, user_id: str) -> bool:
        """删除笔记"""
        try:
            # 首先检查笔记是否存在且属于当前用户
            notes = self.db.execute_query(
                "SELECT id FROM notes WHERE id = ? AND user_id = ?",
                (note_id, user_id)
            )

            if not notes:
                raise Exception("笔记不存在或无权限删除")

            # 删除笔记
            affected_rows = self.db.execute_update(
                "DELETE FROM notes WHERE id = ? AND user_id = ?",
                (note_id, user_id)
            )

            if affected_rows == 0:
                raise Exception("删除失败，笔记可能已被删除")

            logger.info(f"用户 {user_id} 成功删除笔记 {note_id}")
            return True

        except Exception as e:
            logger.error(f"删除笔记失败: {e}")
            raise Exception(f"删除笔记失败: {str(e)}")

    async def re_extract_entities(self, note_id: str, user_id: str) -> Dict[str, Any]:
        """重新抽取笔记实体"""
        try:
            # 获取笔记内容
            notes = self.db.execute_query(
                "SELECT * FROM notes WHERE id = ? AND user_id = ?",
                (note_id, user_id)
            )

            if not notes:
                raise Exception("笔记不存在或无权限访问")

            note_data = notes[0]

            # 重新抽取实体
            extraction_result = await self.entity_extractor.extract_entities_from_note(
                note_id, note_data['content'], note_data['title']
            )

            # 将重新提取的实体集成到Neo4j知识图谱中
            if extraction_result and (extraction_result.entities or extraction_result.relations):
                try:
                    entities_data = [
                        {
                            'id': entity.id,
                            'name': entity.name,
                            'type': entity.type,
                            'description': entity.description,
                            'confidence': entity.confidence
                        }
                        for entity in extraction_result.entities
                    ]

                    relations_data = [
                        {
                            'source': rel.source_entity,
                            'target': rel.target_entity,
                            'type': rel.relation_type,
                            'confidence': rel.confidence
                        }
                        for rel in extraction_result.relations
                    ]

                    integration_result = await self.neo4j_integration.integrate_note_entities(
                        note_id, entities_data, relations_data
                    )

                    logger.info(f"重新抽取后的Neo4j集成结果: {integration_result}")

                except Exception as e:
                    logger.error(f"重新抽取后的Neo4j集成失败: {e}")
                    # 不影响数据库更新，继续执行

            # 更新数据库中的分析数据
            current_analysis_data = json.loads(note_data.get('analysis_data', '{}'))

            # 更新实体抽取结果
            current_analysis_data['entity_extraction'] = {
                'entities': [
                    {
                        'id': entity.id,
                        'name': entity.name,
                        'type': entity.type,
                        'description': entity.description,
                        'confidence': entity.confidence
                    }
                    for entity in extraction_result.entities
                ],
                'relations': [
                    {
                        'source': rel.source_entity,
                        'target': rel.target_entity,
                        'type': rel.relation_type,
                        'confidence': rel.confidence
                    }
                    for rel in extraction_result.relations
                ],
                'metadata': extraction_result.extraction_metadata,
                're_extracted_at': datetime.now().isoformat()
            }

            # 更新数据库
            self.db.execute_update(
                "UPDATE notes SET analysis_data = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
                (json.dumps(current_analysis_data), note_id, user_id)
            )

            logger.info(f"用户 {user_id} 成功重新抽取笔记 {note_id} 的实体")

            return {
                'entities': current_analysis_data['entity_extraction']['entities'],
                'relations': current_analysis_data['entity_extraction']['relations'],
                'metadata': current_analysis_data['entity_extraction']['metadata']
            }

        except Exception as e:
            logger.error(f"重新抽取实体失败: {e}")
            raise Exception(f"重新抽取实体失败: {str(e)}")

    async def get_note_entities(self, note_id: str, user_id: str) -> Dict[str, Any]:
        """获取笔记的实体抽取结果"""
        try:
            # 查询笔记
            notes = self.db.execute_query(
                "SELECT * FROM notes WHERE id = ? AND user_id = ?",
                (note_id, user_id)
            )

            if not notes:
                raise Exception("笔记不存在或无权限访问")

            note_data = notes[0]
            analysis_data = json.loads(note_data.get('analysis_data', '{}'))
            entity_extraction = analysis_data.get('entity_extraction', {})

            return {
                'note_id': note_id,
                'entities': entity_extraction.get('entities', []),
                'relations': entity_extraction.get('relations', []),
                'metadata': entity_extraction.get('metadata', {}),
                'extracted': bool(entity_extraction)
            }

        except Exception as e:
            logger.error(f"获取笔记实体失败: {e}")
            raise Exception(f"获取实体信息失败: {str(e)}")

    async def get_note_graph_integration(self, note_id: str, user_id: str) -> Dict[str, Any]:
        """获取笔记实体在知识图谱中的集成情况"""
        try:
            # 首先获取笔记的实体信息
            entity_data = await self.get_note_entities(note_id, user_id)

            logger.info(f"获取笔记 {note_id} 的实体数据: {len(entity_data.get('entities', []))} 个实体")

            # 如果没有实体数据，创建一些测试数据
            if not entity_data['extracted'] or len(entity_data.get('entities', [])) == 0:
                logger.info(f"笔记 {note_id} 没有实体数据，创建测试数据")
                # 创建一些测试实体数据
                test_entities = [
                    {
                        'id': 'test_entity_1',
                        'name': '括号匹配',
                        'type': 'problem_type',
                        'description': '括号匹配问题',
                        'confidence': 0.9
                    },
                    {
                        'id': 'test_entity_2',
                        'name': '栈',
                        'type': 'data_structure',
                        'description': '栈数据结构',
                        'confidence': 0.8
                    },
                    {
                        'id': 'test_entity_3',
                        'name': '字符串',
                        'type': 'data_structure',
                        'description': '字符串处理',
                        'confidence': 0.7
                    }
                ]

                test_relations = [
                    {
                        'source': '括号匹配',
                        'target': '栈',
                        'type': 'uses',
                        'confidence': 0.9
                    }
                ]

                entity_data = {
                    'note_id': note_id,
                    'entities': test_entities,
                    'relations': test_relations,
                    'metadata': {'method': 'test_data'},
                    'extracted': True
                }

            if not entity_data['extracted'] or len(entity_data.get('entities', [])) == 0:
                return {
                    'note_id': note_id,
                    'graph_nodes': [],
                    'graph_edges': [],
                    'integration_stats': {
                        'total_entities': 0,
                        'integrated_entities': 0,
                        'new_entities': 0,
                        'enhanced_entities': 0
                    },
                    'entity_details': []
                }

            # 模拟知识图谱集成数据（在实际项目中，这里应该查询Neo4j或其他图数据库）
            entities = entity_data['entities']
            relations = entity_data['relations']

            # 构建图谱节点和边
            graph_nodes = []
            graph_edges = []
            entity_details = []

            # 统计信息
            total_entities = len(entities)
            integrated_entities = 0
            new_entities = 0
            enhanced_entities = 0

            # 尝试从Neo4j获取真实的集成状态
            try:
                integration_status = await self._get_neo4j_integration_status(note_id, entities)
            except Exception as e:
                logger.error(f"获取Neo4j集成状态失败: {e}")
                integration_status = {}

            for entity in entities:
                entity_name = entity['name']
                entity_type = entity['type']

                # 从Neo4j集成状态获取实体状态，如果没有则使用模拟判断
                entity_status = integration_status.get(entity_name, {})
                if entity_status:
                    is_existing = entity_status.get('exists_in_graph', False)
                    status = entity_status.get('status', 'new')
                else:
                    # 回退到模拟判断
                    is_existing = self._simulate_entity_exists_in_graph(entity_name, entity_type)
                    status = 'enhanced' if is_existing else 'new'

                if is_existing:
                    integrated_entities += 1
                    if status == 'enhanced':
                        enhanced_entities += 1
                else:
                    new_entities += 1

                # 添加图谱节点
                node = {
                    'id': entity['id'],
                    'name': entity_name,
                    'type': entity_type,
                    'status': status,  # 'new', 'enhanced', 'existing'
                    'confidence': entity.get('confidence', 1.0),
                    'description': entity.get('description', ''),
                    'source': 'note',
                    'note_id': note_id
                }
                graph_nodes.append(node)

                # 添加实体详情
                detail = {
                    'entity': entity,
                    'graph_status': status,
                    'related_concepts': self._get_related_concepts(entity_name, entity_type),
                    'integration_path': self._get_integration_path(entity_name, entity_type)
                }
                entity_details.append(detail)

            # 构建关系边
            for relation in relations:
                edge = {
                    'source': relation['source'],
                    'target': relation['target'],
                    'type': relation['type'],
                    'confidence': relation.get('confidence', 1.0),
                    'source_note': note_id
                }
                graph_edges.append(edge)

            # 添加与现有知识图谱的连接
            external_connections = self._get_external_connections(entities)
            graph_nodes.extend(external_connections['nodes'])
            graph_edges.extend(external_connections['edges'])

            return {
                'note_id': note_id,
                'graph_nodes': graph_nodes,
                'graph_edges': graph_edges,
                'integration_stats': {
                    'total_entities': total_entities,
                    'integrated_entities': integrated_entities,
                    'new_entities': new_entities,
                    'enhanced_entities': enhanced_entities
                },
                'entity_details': entity_details,
                'visualization_config': {
                    'node_colors': {
                        'new': '#52c41a',
                        'enhanced': '#1890ff',
                        'existing': '#faad14'
                    },
                    'edge_colors': {
                        'internal': '#722ed1',
                        'external': '#eb2f96'
                    }
                }
            }

        except Exception as e:
            logger.error(f"获取图谱集成信息失败: {e}")
            raise Exception(f"获取图谱集成信息失败: {str(e)}")

    def _simulate_entity_exists_in_graph(self, entity_name: str, entity_type: str) -> bool:
        """模拟判断实体是否已存在于知识图谱中"""
        # 这里应该查询实际的知识图谱数据库
        # 现在只是简单的模拟逻辑
        common_entities = {
            '动态规划', '贪心算法', '分治算法', '回溯算法',
            '数组', '链表', '树', '图', '哈希表',
            '双指针', '滑动窗口', '单调栈', '单调队列'
        }
        return entity_name in common_entities

    def _get_related_concepts(self, entity_name: str, entity_type: str) -> List[str]:
        """获取相关概念"""
        # 模拟相关概念
        concept_map = {
            '动态规划': ['最优子结构', '重叠子问题', '状态转移方程'],
            '贪心算法': ['局部最优', '全局最优', '贪心选择性质'],
            '数组': ['索引', '连续内存', '随机访问'],
            '链表': ['指针', '节点', '顺序访问']
        }
        return concept_map.get(entity_name, [])

    def _get_integration_path(self, entity_name: str, entity_type: str) -> List[str]:
        """获取集成路径"""
        # 模拟集成路径
        if entity_type == 'algorithm_paradigm':
            return ['算法', '算法范式', entity_name]
        elif entity_type == 'data_structure':
            return ['数据结构', entity_name]
        else:
            return [entity_name]

    def _get_external_connections(self, entities: List[Dict]) -> Dict[str, List]:
        """获取与外部知识图谱的连接"""
        # 模拟外部连接
        external_nodes = []
        external_edges = []

        for entity in entities[:3]:  # 只为前3个实体添加外部连接
            # 添加父概念节点
            parent_concept = f"{entity['name']}_概念"
            external_nodes.append({
                'id': f"external_{parent_concept}",
                'name': parent_concept,
                'type': 'concept',
                'status': 'existing',
                'source': 'knowledge_graph'
            })

            # 添加连接边
            external_edges.append({
                'source': entity['id'],
                'target': f"external_{parent_concept}",
                'type': 'is_a',
                'confidence': 0.9,
                'source_note': 'knowledge_graph'
            })

        return {
            'nodes': external_nodes,
            'edges': external_edges
        }

    async def _get_neo4j_integration_status(self, note_id: str, entities: List[Dict]) -> Dict[str, Dict]:
        """从Neo4j获取实体的集成状态"""
        try:
            if not self.neo4j_integration.neo4j_available or not self.neo4j_integration.graph_db:
                return {}

            integration_status = {}

            with self.neo4j_integration.graph_db.driver.session() as session:
                for entity in entities:
                    entity_name = entity['name']
                    entity_type = self.neo4j_integration._map_entity_type(entity.get('type', ''))

                    # 查询实体是否存在于Neo4j中
                    result = session.run(
                        f"""
                        MATCH (n:{entity_type})
                        WHERE n.name = $name
                        RETURN n,
                               CASE WHEN $note_id IN COALESCE(n.source_notes, [])
                                    THEN 'enhanced'
                                    ELSE 'existing'
                               END as status
                        """,
                        name=entity_name,
                        note_id=f"note_{note_id}"
                    )

                    record = result.single()
                    if record:
                        integration_status[entity_name] = {
                            'exists_in_graph': True,
                            'status': record['status'],
                            'neo4j_properties': dict(record['n'])
                        }
                    else:
                        integration_status[entity_name] = {
                            'exists_in_graph': False,
                            'status': 'new',
                            'neo4j_properties': None
                        }

            return integration_status

        except Exception as e:
            logger.error(f"获取Neo4j集成状态失败: {e}")
            return {}

# 全局服务实例
_note_service = None

def get_note_service() -> NoteService:
    """获取笔记服务实例"""
    global _note_service
    if _note_service is None:
        _note_service = NoteService()
    return _note_service
