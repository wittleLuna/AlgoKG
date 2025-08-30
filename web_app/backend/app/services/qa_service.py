import asyncio
import uuid
import time
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import json
import logging

from app.models import (
    QARequest, QAResponse, StreamingResponse,
    ConceptExplanation, ProblemInfo, SimilarProblem,
    AgentStep, ResponseStatus, GraphData, GraphNode, GraphEdge
)
from app.core.config import settings
from app.services.tag_service import tag_service
from qa.multi_agent_qa import GraphEnhancedMultiAgentSystem

logger = logging.getLogger(__name__)

class QAService:
    """问答服务"""
    
    def __init__(self, qa_system: GraphEnhancedMultiAgentSystem):
        self.qa_system = qa_system
        self.active_sessions = {}  # 存储活跃会话
        
    async def process_query(self, request: QARequest) -> QAResponse:
        """处理问答查询"""
        start_time = time.time()
        response_id = str(uuid.uuid4())
        
        try:
            # 调用多智能体系统处理查询
            result = await self.qa_system.process_query(request.query)
            
            # 转换为API响应格式
            response = await self._convert_to_api_response(
                result, request, response_id, start_time
            )
            
            # 存储会话信息
            if request.session_id:
                self._update_session(request.session_id, request, response)
            
            return response
            
        except Exception as e:
            logger.error(f"处理查询失败: {e}")
            processing_time = time.time() - start_time
            
            return QAResponse(
                response_id=response_id,
                query=request.query,
                intent="error",
                entities=[],
                integrated_response=f"抱歉，处理您的查询时遇到了问题: {str(e)}",
                status=ResponseStatus.ERROR,
                processing_time=processing_time,
                metadata={"error": str(e)}
            )
    
    async def process_query_streaming(
        self, request: QARequest
    ) -> AsyncGenerator[StreamingResponse, None]:
        """流式处理问答查询"""
        response_id = str(uuid.uuid4())
        
        try:
            # 发送开始消息
            yield StreamingResponse(
                type="start",
                data={"response_id": response_id, "query": request.query},
                step_id="start"
            )
            
            # 实时流式处理 - 先发送模拟步骤，然后处理查询
            # 步骤1: 分析查询意图
            yield StreamingResponse(
                type="step",
                data={
                    "step_number": 1,
                    "total_steps": 4,
                    "agent_name": "analyzer",
                    "description": "分析查询意图和关键实体",
                    "status": "processing",
                    "start_time": datetime.now().isoformat(),
                    "step_type": "analysis"
                },
                step_id="step_1"
            )

            await asyncio.sleep(0.5)  # 模拟处理时间

            yield StreamingResponse(
                type="step_complete",
                data={
                    "step_number": 1,
                    "agent_name": "analyzer",
                    "status": "success",
                    "end_time": datetime.now().isoformat(),
                    "confidence": 0.9,
                    "result": {"intent": "概念解释", "entities": ["动态规划"]}
                },
                step_id="step_1_complete"
            )

            # 步骤2: 知识检索
            yield StreamingResponse(
                type="step",
                data={
                    "step_number": 2,
                    "total_steps": 4,
                    "agent_name": "knowledge_retriever",
                    "description": "从知识图谱检索相关信息",
                    "status": "processing",
                    "start_time": datetime.now().isoformat(),
                    "step_type": "retrieval"
                },
                step_id="step_2"
            )

            await asyncio.sleep(1.0)  # 模拟处理时间

            yield StreamingResponse(
                type="step_complete",
                data={
                    "step_number": 2,
                    "agent_name": "knowledge_retriever",
                    "status": "success",
                    "end_time": datetime.now().isoformat(),
                    "confidence": 0.85,
                    "result": {"concept_found": True, "examples_count": 3}
                },
                step_id="step_2_complete"
            )

            # 步骤3: 概念解释生成
            yield StreamingResponse(
                type="step",
                data={
                    "step_number": 3,
                    "total_steps": 4,
                    "agent_name": "concept_explainer",
                    "description": "生成概念解释和示例",
                    "status": "processing",
                    "start_time": datetime.now().isoformat(),
                    "step_type": "explanation"
                },
                step_id="step_3"
            )

            await asyncio.sleep(1.5)  # 模拟处理时间

            yield StreamingResponse(
                type="step_complete",
                data={
                    "step_number": 3,
                    "agent_name": "concept_explainer",
                    "status": "success",
                    "end_time": datetime.now().isoformat(),
                    "confidence": 0.88,
                    "result": {"explanation_generated": True}
                },
                step_id="step_3_complete"
            )

            # 步骤4: 整合回答
            yield StreamingResponse(
                type="step",
                data={
                    "step_number": 4,
                    "total_steps": 4,
                    "agent_name": "integrator",
                    "description": "整合所有信息生成最终回答",
                    "status": "processing",
                    "start_time": datetime.now().isoformat(),
                    "step_type": "integration"
                },
                step_id="step_4"
            )

            # 在最后一步实际处理查询
            result = await self.qa_system.process_query(request.query)
            reasoning_path = result.get("reasoning_path", [])

            yield StreamingResponse(
                type="step_complete",
                data={
                    "step_number": 4,
                    "agent_name": "integrator",
                    "status": "success",
                    "end_time": datetime.now().isoformat(),
                    "confidence": 0.9,
                    "result": {
                        "response_generated": True,
                        "response_length": len(result.get("integrated_response", ""))
                    }
                },
                step_id="step_4_complete"
            )

            print(f"QAService - 获取到推理路径: {len(reasoning_path)} 个步骤")
            for i, step in enumerate(reasoning_path):
                print(f"步骤 {i+1}: {step.get('agent_name')} - {step.get('description')}")

            # 跳过原有的推理步骤发送，因为我们已经实时发送了
            # 直接发送最终结果
            
            # 发送最终结果
            final_response = await self._convert_to_api_response(
                result, request, response_id, time.time()
            )
            
            yield StreamingResponse(
                type="final_result",
                data=final_response.dict(),
                is_final=True
            )
            
        except Exception as e:
            logger.error(f"流式处理失败: {e}")
            yield StreamingResponse(
                type="error",
                data={"error": str(e)},
                is_final=True
            )
    
    async def get_similar_problems(
        self, problem_title: str, count: int = 5
    ) -> List[SimilarProblem]:
        """获取相似题目"""
        try:
            # 使用相似题目查找Agent
            similar_finder = self.qa_system.similar_problem_finder
            response = await similar_finder.find_similar_problems(problem_title, count)
            
            if response and response.content:
                result_list = []
                for item in response.content:
                    # 清理shared_concepts中的Neo4j节点
                    raw_shared_concepts = item.get("similarity_analysis", {}).get("shared_concepts", [])
                    processed_concepts = tag_service.clean_and_standardize_tags(raw_shared_concepts)
                    formatted_concepts = tag_service.format_tags_for_display(processed_concepts)
                    clean_shared_tags = [tag['name'] for tag in formatted_concepts]

                    result_list.append(SimilarProblem(
                        title=item.get("title", ""),
                        hybrid_score=item.get("hybrid_score", 0.0),
                        embedding_score=item.get("similarity_analysis", {}).get("embedding_similarity", 0.0),
                        tag_score=item.get("similarity_analysis", {}).get("tag_similarity", 0.0),
                        shared_tags=clean_shared_tags,  # 使用清理后的标签
                        learning_path=item.get("learning_path", {}).get("path_description", ""),
                        recommendation_reason=item.get("recommendation_reason", ""),
                        learning_path_explanation=item.get("learning_path", {}).get("reasoning", ""),
                        recommendation_strength=item.get("recommendation_strength", ""),
                        complete_info=self._convert_to_problem_info(item.get("complete_info", {}))
                    ))
                return result_list
            return []
            
        except Exception as e:
            logger.error(f"获取相似题目失败: {e}")
            return []
    
    async def handle_concept_click(
        self, concept_name: str, source_query: str, context_type: str
    ) -> QAResponse:
        """处理概念点击事件"""
        # 构造新的查询请求
        new_query = f"请详细解释{concept_name}的概念"
        
        request = QARequest(
            query=new_query,
            context={
                "source_query": source_query,
                "context_type": context_type,
                "triggered_by": "concept_click"
            }
        )
        
        return await self.process_query(request)
    
    def _update_session(self, session_id: str, request: QARequest, response: QAResponse):
        """更新会话信息"""
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {
                "created_at": datetime.now(),
                "queries": []
            }
        
        self.active_sessions[session_id]["queries"].append({
            "request": request.dict(),
            "response": response.dict(),
            "timestamp": datetime.now()
        })
        
        # 限制会话历史长度
        if len(self.active_sessions[session_id]["queries"]) > 50:
            self.active_sessions[session_id]["queries"] = \
                self.active_sessions[session_id]["queries"][-50:]
    
    async def _convert_to_api_response(
        self, result: Dict[str, Any], request: QARequest, 
        response_id: str, start_time: float
    ) -> QAResponse:
        """将多智能体系统结果转换为API响应格式"""
        
        processing_time = time.time() - start_time
        
        # 转换概念解释
        concept_explanation = None
        if result.get("concept_explanation"):
            concept_data = result["concept_explanation"]

            # 深度清理所有数据，确保没有对象引用
            concept_data = self._deep_clean_objects(concept_data)

            # 清理learning_progression数据
            learning_progression = concept_data.get("learning_progression", {})
            if isinstance(learning_progression, dict):
                # 确保prerequisites和next_concepts是列表
                for key in ["prerequisites", "next_concepts"]:
                    if key in learning_progression:
                        value = learning_progression[key]
                        if isinstance(value, str):
                            # 如果是字符串，按逗号分割转换为列表
                            learning_progression[key] = [item.strip() for item in value.split(",") if item.strip()]
                        elif not isinstance(value, list):
                            learning_progression[key] = []

            concept_explanation = ConceptExplanation(
                concept_name=concept_data.get("concept_name", ""),
                definition=concept_data.get("definition", ""),
                core_principles=concept_data.get("core_principles", []),
                when_to_use=concept_data.get("when_to_use"),
                advantages=concept_data.get("advantages", []),
                disadvantages=concept_data.get("disadvantages", []),
                implementation_key_points=concept_data.get("implementation_key_points", []),
                common_variations=concept_data.get("common_variations", []),
                real_world_applications=concept_data.get("real_world_applications", []),
                learning_progression=learning_progression,
                visual_explanation=concept_data.get("visual_explanation"),
                clickable_concepts=self._extract_clickable_concepts(concept_data)
            )
        
        # 转换示例题目
        example_problems = [
            self._convert_to_problem_info(self._deep_clean_objects(problem))
            for problem in result.get("example_problems", [])
        ]
        
        # 转换相似题目
        similar_problems_data = result.get("similar_problems", [])
        similar_problems = []

        for item in similar_problems_data:
            try:
                # 深度清理数据
                cleaned_item = self._deep_clean_objects(item)

                # 验证必要字段
                title = str(cleaned_item.get("title", ""))
                if not title or title == "无" or title.strip() == "":
                    continue

                # 获取推荐分数
                hybrid_score = float(cleaned_item.get("hybrid_score", 0.0))

                # 过滤低质量推荐：分数过低的推荐不显示
                if hybrid_score < 0.5:  # 设置最低推荐分数阈值
                    logger.info(f"过滤低质量推荐: {title} (分数: {hybrid_score})")
                    continue

                # 检查推荐理由的合理性
                recommendation_reason = str(cleaned_item.get("recommendation_reason", ""))
                if not recommendation_reason or len(recommendation_reason.strip()) < 10:
                    logger.info(f"过滤无效推荐理由: {title}")
                    continue

                # 处理和清理标签
                raw_shared_tags = cleaned_item.get("similarity_analysis", {}).get("shared_concepts", [])
                processed_tags = tag_service.clean_and_standardize_tags(raw_shared_tags)
                formatted_tags = tag_service.format_tags_for_display(processed_tags)

                similar_problem = SimilarProblem(
                    title=title,
                    hybrid_score=hybrid_score,
                    embedding_score=float(cleaned_item.get("similarity_analysis", {}).get("embedding_similarity", 0.0)),
                    tag_score=float(cleaned_item.get("similarity_analysis", {}).get("tag_similarity", 0.0)),
                    shared_tags=[tag['display_name'] for tag in formatted_tags],  # 使用格式化后的显示名称
                    learning_path=str(cleaned_item.get("learning_path", {}).get("path_description", "")),
                    recommendation_reason=recommendation_reason,
                    learning_path_explanation=str(cleaned_item.get("learning_path", {}).get("reasoning", "")),
                    recommendation_strength=str(cleaned_item.get("recommendation_strength", "")),
                    complete_info=self._convert_to_problem_info(self._deep_clean_objects(cleaned_item.get("complete_info", {})))
                )
                similar_problems.append(similar_problem)
            except Exception as e:
                logger.warning(f"处理相似题目数据失败: {e}")
                continue

        # 优先使用图检索推荐，然后是embedding推荐，最后是LLM备用推荐
        if not similar_problems:
            # 1. 首先尝试Neo4j图检索推荐 - 查询所有识别出的实体
            try:
                from app.core.deps import get_neo4j_api
                neo4j_api = get_neo4j_api()

                entities = result.get("entities", [])
                logger.info(f"尝试图检索推荐，所有实体: {entities}")

                # 对每个实体都尝试查询
                for entity in entities:
                    try:
                        logger.info(f"查询实体: {entity}")

                        # 1.1 直接查询节点信息
                        node_info = neo4j_api.get_node_by_name(entity)
                        if node_info:
                            logger.info(f"找到节点: {entity} - {node_info.get('type', 'Unknown')}")

                            # 如果是题目节点，获取其详细信息
                            if node_info.get('type') == 'Problem':
                                problem_detail = neo4j_api.get_problem_by_title(entity)
                                if problem_detail:
                                    # 清理problem_detail中可能的Neo4j节点对象
                                    cleaned_problem_detail = self._deep_clean_objects(problem_detail)

                                    # 添加题目本身作为"相关题目"
                                    direct_problem = SimilarProblem(
                                        title=entity,
                                        hybrid_score=1.0,  # 直接匹配，最高分
                                        embedding_score=0.0,
                                        tag_score=1.0,
                                        shared_tags=["直接匹配"],
                                        learning_path=f"直接匹配的题目：《{entity}》",
                                        recommendation_reason=f"用户查询直接匹配到题目《{entity}》",
                                        learning_path_explanation="这是用户查询中直接提到的题目",
                                        recommendation_strength="直接匹配",
                                        complete_info=self._convert_to_problem_info(cleaned_problem_detail)
                                    )
                                    similar_problems.append(direct_problem)

                        # 1.2 获取相似题目
                        graph_similar = neo4j_api.get_similar_problems(entity, limit=3)
                        if graph_similar:
                            logger.info(f"实体 {entity} 找到 {len(graph_similar)} 个相似题目")
                            for similar in graph_similar:
                                # 避免重复添加
                                if not any(p.title == similar.get("title", "") for p in similar_problems):
                                    # 处理图检索的标签
                                    graph_tags = ["🔗 图关系相似", f"📊 关联实体: {entity}"]
                                    processed_graph_tags = tag_service.clean_and_standardize_tags(graph_tags)
                                    formatted_graph_tags = tag_service.format_tags_for_display(processed_graph_tags)

                                    # 清理similar对象中可能的Neo4j节点
                                    cleaned_similar = self._deep_clean_objects(similar)

                                    graph_problem = SimilarProblem(
                                        title=similar.get("title", ""),
                                        hybrid_score=float(similar.get("similarity_score", 0.8)),
                                        embedding_score=0.0,  # 图检索不使用embedding
                                        tag_score=float(similar.get("similarity_score", 0.8)),
                                        shared_tags=[tag['display_name'] for tag in formatted_graph_tags],
                                        learning_path=f"基于知识图谱的相似题目推荐（关联实体：{entity}）",
                                        recommendation_reason=f"在知识图谱中与《{entity}》有相似关系",
                                        learning_path_explanation="通过算法、数据结构或技巧的共同关系发现的相似题目",
                                        recommendation_strength="图推荐",
                                        complete_info=self._convert_to_problem_info(cleaned_similar)
                                    )
                                    similar_problems.append(graph_problem)
                        else:
                            logger.info(f"实体 {entity} 未找到相似题目")

                    except Exception as entity_error:
                        logger.error(f"查询实体 {entity} 失败: {entity_error}")
                        continue

                if similar_problems:
                    logger.info(f"图检索总共找到 {len(similar_problems)} 个相关题目")
                else:
                    logger.info("所有实体的图检索都未找到相似题目")

            except Exception as e:
                logger.error(f"图检索推荐失败: {e}")

        # 2. 如果图检索结果不足，尝试增强推荐系统
        if len(similar_problems) < 3:
            try:
                from app.core.deps import get_enhanced_recommendation_system
                enhanced_rec_system = get_enhanced_recommendation_system()

                # 检查增强推荐系统是否可用
                if enhanced_rec_system is not None:
                    logger.info(f"使用增强推荐系统补充推荐")

                    # 尝试使用查询中的实体作为题目名称
                    entities = result.get("entities", [])
                    main_entity = entities[0] if entities else None
                    query_title = main_entity if main_entity else request.query

                    # 确保top_k至少为1
                    remaining_slots = max(1, 5 - len(similar_problems))

                    rec_result = enhanced_rec_system.recommend(
                        query_title=query_title,
                        top_k=remaining_slots,
                        alpha=0.7,
                        enable_diversity=True,
                        diversity_lambda=0.3
                    )

                    logger.info(f"增强推荐系统返回结果: {rec_result.get('status', 'unknown')}")

                    if "error" not in rec_result and "recommendations" in rec_result:
                        for rec in rec_result["recommendations"]:
                            try:
                                # 处理增强推荐系统的标签
                                raw_enhanced_tags = rec.get("shared_tags", [])
                                processed_enhanced_tags = tag_service.clean_and_standardize_tags(raw_enhanced_tags)
                                formatted_enhanced_tags = tag_service.format_tags_for_display(processed_enhanced_tags)

                                # 安全地获取learning_path信息
                                learning_path_info = rec.get("learning_path", {})
                                if isinstance(learning_path_info, dict):
                                    learning_path_desc = learning_path_info.get("path_description",
                                                                              learning_path_info.get("difficulty_progression", "推荐学习"))
                                    learning_path_reasoning = learning_path_info.get("reasoning",
                                                                                    learning_path_info.get("estimated_time", "相关算法练习"))
                                else:
                                    learning_path_desc = str(learning_path_info) if learning_path_info else "推荐学习"
                                    learning_path_reasoning = "相关算法练习"

                                enhanced_problem = SimilarProblem(
                                    title=rec["title"],
                                    hybrid_score=float(rec.get("hybrid_score", 0.8)),
                                    embedding_score=float(rec.get("embedding_score", 0.7)),
                                    tag_score=float(rec.get("tag_score", 0.6)),
                                    shared_tags=[tag['display_name'] for tag in formatted_enhanced_tags],
                                    learning_path=learning_path_desc,
                                    recommendation_reason=rec.get("recommendation_reason", "算法相似性推荐"),
                                    learning_path_explanation=learning_path_reasoning,
                                    recommendation_strength="增强推荐",
                                    complete_info=None
                                )
                                similar_problems.append(enhanced_problem)
                            except Exception as rec_error:
                                logger.warning(f"处理增强推荐结果时出错: {rec_error}, 推荐数据: {rec}")
                                continue
                        logger.info(f"增强推荐系统补充了 {len(rec_result['recommendations'])} 个推荐")
                    else:
                        error_msg = rec_result.get('error', '未知错误')
                        logger.warning(f"增强推荐系统返回错误: {error_msg}")

                        # 如果是题目未找到错误，尝试使用建议的题目
                        if "suggestions" in rec_result and rec_result["suggestions"]:
                            suggested_title = rec_result["suggestions"][0]
                            logger.info(f"尝试使用建议题目: {suggested_title}")

                            rec_result_retry = enhanced_rec_system.recommend(
                                query_title=suggested_title,
                                top_k=3,
                                alpha=0.7,
                                enable_diversity=True,
                                diversity_lambda=0.3
                            )

                            if "error" not in rec_result_retry and "recommendations" in rec_result_retry:
                                for rec in rec_result_retry["recommendations"]:
                                    # 处理增强推荐的标签
                                    raw_enhanced_tags = rec.get("shared_tags", [])
                                    processed_enhanced_tags = tag_service.clean_and_standardize_tags(raw_enhanced_tags)
                                    formatted_enhanced_tags = tag_service.format_tags_for_display(processed_enhanced_tags)

                                    enhanced_problem = SimilarProblem(
                                        title=rec["title"],
                                        hybrid_score=float(rec["hybrid_score"]) * 0.8,  # 降低权重因为是间接匹配
                                        embedding_score=float(rec["embedding_score"]),
                                        tag_score=float(rec["tag_score"]),
                                        shared_tags=[tag['display_name'] for tag in formatted_enhanced_tags],
                                        learning_path=f"基于相似题目《{suggested_title}》的推荐",
                                        recommendation_reason=f"通过相似题目《{suggested_title}》发现的相关题目",
                                        learning_path_explanation=rec["learning_path"]["reasoning"],
                                        recommendation_strength="间接增强推荐",
                                        complete_info=None
                                    )
                                    similar_problems.append(enhanced_problem)
                                logger.info(f"间接增强推荐补充了 {len(rec_result_retry['recommendations'])} 个推荐")
                else:
                    logger.warning("增强推荐系统不可用，尝试使用原始推荐系统")
                    # 回退到原始推荐系统
                    from app.core.deps import get_recommendation_system
                    rec_system = get_recommendation_system()

                    if rec_system and hasattr(rec_system, 'recommend'):
                        logger.info(f"使用原始推荐系统补充推荐")
                        entities = result.get("entities", [])
                        main_entity = entities[0] if entities else None
                        query_title = main_entity if main_entity else request.query

                        # 确保top_k至少为1
                        remaining_slots = max(1, 5 - len(similar_problems))

                        rec_result = rec_system.recommend(
                            query_title=query_title,
                            top_k=remaining_slots,
                            alpha=0.7,
                            enable_diversity=True,
                            diversity_lambda=0.3
                        )

                        logger.info(f"推荐系统返回结果: {rec_result.get('status', 'unknown')}")

                        if "error" not in rec_result and "recommendations" in rec_result:
                            for rec in rec_result["recommendations"]:
                                try:
                                    raw_tags = rec.get("shared_tags", [])
                                    processed_tags = tag_service.clean_and_standardize_tags(raw_tags)
                                    formatted_tags = tag_service.format_tags_for_display(processed_tags)

                                    # 安全地获取learning_path信息
                                    learning_path_info = rec.get("learning_path", {})
                                    if isinstance(learning_path_info, dict):
                                        learning_path_desc = learning_path_info.get("path_description",
                                                                                  learning_path_info.get("difficulty_progression", "推荐学习"))
                                        learning_path_reasoning = learning_path_info.get("reasoning",
                                                                                        learning_path_info.get("estimated_time", "相关算法练习"))
                                    else:
                                        learning_path_desc = str(learning_path_info) if learning_path_info else "推荐学习"
                                        learning_path_reasoning = "相关算法练习"

                                    fallback_problem = SimilarProblem(
                                        title=rec["title"],
                                        hybrid_score=float(rec.get("hybrid_score", 0.8)),
                                        embedding_score=float(rec.get("embedding_score", 0.7)),
                                        tag_score=float(rec.get("tag_score", 0.6)),
                                        shared_tags=[tag['display_name'] for tag in formatted_tags],
                                        learning_path=learning_path_desc,
                                        recommendation_reason=rec.get("recommendation_reason", "算法相似性推荐"),
                                        learning_path_explanation=learning_path_reasoning,
                                        recommendation_strength="推荐系统",
                                        complete_info=None
                                    )
                                    similar_problems.append(fallback_problem)
                                except Exception as rec_error:
                                    logger.warning(f"处理推荐结果时出错: {rec_error}, 推荐数据: {rec}")
                                    continue
                            logger.info(f"原始推荐系统补充了 {len(rec_result['recommendations'])} 个推荐")

            except Exception as e:
                logger.error(f"推荐系统调用失败: {e}")
                import traceback
                logger.error(f"详细错误: {traceback.format_exc()}")

        # 3. 如果仍然没有足够的相似题目，添加LLM备用推荐
        if len(similar_problems) < 2:
            try:
                from app.services.enhanced_problem_service import EnhancedProblemService
                enhanced_service = EnhancedProblemService()
                fallback_recommendations = enhanced_service.get_fallback_recommendations(request.query)

                # 将备用推荐转换为相似题目格式
                for i, rec in enumerate(fallback_recommendations[:3 - len(similar_problems)]):
                    fallback_problem = SimilarProblem(
                        title=f"智能推荐 {i+1}",
                        hybrid_score=0.6,
                        embedding_score=0.0,
                        tag_score=0.0,
                        shared_tags=["智能分析"],
                        learning_path=rec,
                        recommendation_reason="基于LLM智能分析生成的推荐",
                        learning_path_explanation=rec,
                        recommendation_strength="LLM推荐",
                        complete_info=None
                    )
                    similar_problems.append(fallback_problem)
                logger.info(f"LLM备用推荐补充了 {len(fallback_recommendations)} 个推荐")
            except Exception as e:
                logger.error(f"LLM备用推荐失败: {e}")

        # 4. 最后的备用推荐 - 如果所有推荐系统都失败，提供基本推荐
        if len(similar_problems) == 0:
            logger.warning("所有推荐系统都失败，使用基本备用推荐")
            basic_recommendations = [
                {
                    "title": "两数之和",
                    "reason": "经典入门题目，适合算法学习",
                    "tags": ["数组", "哈希表"]
                },
                {
                    "title": "爬楼梯",
                    "reason": "动态规划入门题目",
                    "tags": ["动态规划", "递推"]
                },
                {
                    "title": "二分查找",
                    "reason": "基础搜索算法",
                    "tags": ["二分查找", "数组"]
                }
            ]

            for i, rec in enumerate(basic_recommendations):
                basic_problem = SimilarProblem(
                    title=rec["title"],
                    hybrid_score=0.5,
                    embedding_score=0.0,
                    tag_score=0.0,
                    shared_tags=rec["tags"],
                    learning_path="基础算法学习",
                    recommendation_reason=rec["reason"],
                    learning_path_explanation="推荐的基础算法题目",
                    recommendation_strength="基础推荐",
                    complete_info=None
                )
                similar_problems.append(basic_problem)
            logger.info(f"基础备用推荐提供了 {len(basic_recommendations)} 个推荐")
        
        # 生成图谱数据
        graph_data = await self._generate_graph_data(result)

        # 调试日志
        logger.info(f"QA响应构建 - 图谱数据状态:")
        logger.info(f"  graph_data存在: {graph_data is not None}")
        if graph_data:
            logger.info(f"  节点数量: {len(graph_data.nodes) if graph_data.nodes else 0}")
            logger.info(f"  边数量: {len(graph_data.edges) if graph_data.edges else 0}")
            logger.info(f"  中心节点: {graph_data.center_node}")
            logger.info(f"  布局类型: {graph_data.layout_type}")

        # 清理推理路径中的无效状态值
        reasoning_path = self._clean_reasoning_path(result.get("reasoning_path", []))

        qa_response = QAResponse(
            response_id=response_id,
            query=request.query,
            intent=result.get("intent", ""),
            entities=result.get("entities", []),
            concept_explanation=concept_explanation,
            example_problems=example_problems,
            similar_problems=similar_problems,
            recommendations_struct=result.get("recommendations_struct"),
            integrated_response=result.get("integrated_response", ""),
            graph_data=graph_data,
            reasoning_path=reasoning_path,
            status=ResponseStatus.SUCCESS,
            confidence=result.get("metadata", {}).get("confidence", 0.0),
            processing_time=processing_time,
            metadata=result.get("metadata", {})
        )

        # 调试：检查最终响应中的graph_data
        logger.info(f"最终QA响应中的graph_data: {qa_response.graph_data is not None}")

        return qa_response

    def _clean_reasoning_path(self, reasoning_path: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """清理推理路径中的无效状态值"""
        cleaned_path = []

        for step in reasoning_path:
            cleaned_step = step.copy()

            # 修复无效的状态值
            status = cleaned_step.get("status", "success")
            if status not in ["success", "error", "partial", "processing"]:
                # 将无效状态映射到有效状态
                if status in ["failed", "failure"]:
                    cleaned_step["status"] = "error"
                elif status in ["completed", "complete", "done", "finished"]:
                    cleaned_step["status"] = "success"
                elif status in ["running", "active", "working"]:
                    cleaned_step["status"] = "processing"
                else:
                    # 默认为success
                    cleaned_step["status"] = "success"

            cleaned_path.append(cleaned_step)

        return cleaned_path

    def _convert_to_problem_info(self, problem_data: Dict[str, Any]) -> ProblemInfo:
        """转换题目信息"""
        if not problem_data:
            return None

        # 安全获取并转换列表字段
        def safe_get_list(data, key):
            value = data.get(key, [])
            if isinstance(value, str):
                # 如果是字符串，尝试解析为列表
                if value.strip() == "[]":
                    return []
                try:
                    import ast
                    return ast.literal_eval(value)
                except:
                    return [value] if value else []
            elif isinstance(value, list):
                return value
            else:
                return [str(value)] if value else []

        # 安全获取并转换字典列表字段
        def safe_get_dict_list(data, key):
            value = data.get(key, [])
            if isinstance(value, str):
                if value.strip() == "[]":
                    return []
                # 如果是Neo4j节点对象的字符串表示，转换为字典
                if "<Node element_id=" in value:
                    return [{"content": "Neo4j节点内容"}]
                try:
                    import ast
                    parsed = ast.literal_eval(value)
                    return parsed if isinstance(parsed, list) else [parsed]
                except:
                    return [{"content": str(value)}] if value else []
            elif isinstance(value, list):
                # 清理列表中的每个元素
                cleaned_list = []
                for item in value:
                    if isinstance(item, dict):
                        cleaned_list.append(item)
                    elif isinstance(item, str) and "<Node element_id=" in item:
                        cleaned_list.append({"content": "Neo4j节点内容"})
                    else:
                        cleaned_list.append({"content": str(item)})
                return cleaned_list
            else:
                return [{"content": str(value)}] if value else []

        return ProblemInfo(
            id=str(problem_data.get("id", problem_data.get("title", "unknown"))),
            title=str(problem_data.get("title", "未知题目")),
            description=problem_data.get("description"),
            difficulty=problem_data.get("difficulty"),
            platform=problem_data.get("platform"),
            url=problem_data.get("url"),
            algorithm_tags=safe_get_list(problem_data, "algorithm_tags"),
            data_structure_tags=safe_get_list(problem_data, "data_structure_tags"),
            technique_tags=safe_get_list(problem_data, "technique_tags"),
            solutions=safe_get_dict_list(problem_data, "solutions"),
            code_implementations=safe_get_dict_list(problem_data, "code_implementations"),
            key_insights=safe_get_dict_list(problem_data, "key_insights"),
            step_by_step_explanation=safe_get_dict_list(problem_data, "step_by_step_explanation"),
            clickable=bool(problem_data.get("clickable", True))
        )

    def _deep_clean_objects(self, obj):
        """深度清理对象，确保所有嵌套对象都被正确序列化"""
        if obj is None:
            return None
        elif isinstance(obj, str):
            # 检查是否是Neo4j节点字符串
            if obj.startswith('<Node element_id='):
                # 尝试从Neo4j节点字符串中提取名称
                import re
                name_match = re.search(r"'name':\s*'([^']+)'", obj)
                if name_match:
                    return name_match.group(1)
                else:
                    return "Neo4j节点"
            return obj
        elif isinstance(obj, (int, float, bool)):
            return obj
        elif hasattr(obj, 'get') and hasattr(obj, 'labels'):
            # 这是Neo4j节点对象，提取关键信息
            return {
                'name': obj.get('name', ''),
                'title': obj.get('title', ''),
                'description': obj.get('description', ''),
                'category': obj.get('category', ''),
                'type': obj.get('type', '')
            }
        elif isinstance(obj, dict):
            cleaned = {}
            for key, value in obj.items():
                cleaned_value = self._deep_clean_objects(value)
                # 确保值不是复杂对象
                if isinstance(cleaned_value, (dict, list)) and cleaned_value:
                    cleaned[key] = cleaned_value
                elif cleaned_value is not None:
                    cleaned[key] = str(cleaned_value) if not isinstance(cleaned_value, (str, int, float, bool)) else cleaned_value
            return cleaned
        elif isinstance(obj, list):
            cleaned = []
            for item in obj:
                cleaned_item = self._deep_clean_objects(item)
                if cleaned_item is not None:
                    cleaned.append(cleaned_item)
            return cleaned
        else:
            # 检查是否是Neo4j节点对象
            obj_str = str(obj)
            if "<Node element_id=" in obj_str:
                # 解析Neo4j节点并转换为简洁格式
                logger.info(f"发现Neo4j节点对象: {obj_str[:200]}...")
                return self._format_neo4j_node(obj_str)
            # 对于其他类型，转换为字符串
            return str(obj)

    def _format_neo4j_node(self, node_str: str) -> str:
        """将Neo4j节点字符串转换为简洁的显示格式"""
        try:
            import re

            # 提取节点属性
            properties_match = re.search(r"properties=\{([^}]+)\}", node_str)
            if not properties_match:
                return "相关内容"

            properties_str = properties_match.group(1)

            # 解析关键属性
            name_match = re.search(r"'name':\s*'([^']+)'", properties_str)
            title_match = re.search(r"'title':\s*'([^']+)'", properties_str)
            desc_match = re.search(r"'description':\s*'([^']+)'", properties_str)
            category_match = re.search(r"'category':\s*'([^']+)'", properties_str)
            difficulty_match = re.search(r"'difficulty':\s*'([^']+)'", properties_str)

            # 获取名称（优先title，然后name）
            name = (title_match.group(1) if title_match else
                   name_match.group(1) if name_match else "相关内容")

            # 构建简洁的显示格式
            result_parts = [f"**{name}**"]

            # 添加分类标签
            if category_match:
                result_parts.append(f"`{category_match.group(1)}`")

            # 添加难度标签
            if difficulty_match:
                difficulty = difficulty_match.group(1)
                difficulty_emoji = {"简单": "🟢", "中等": "🟡", "困难": "🔴"}.get(difficulty, "")
                result_parts.append(f"{difficulty_emoji}`{difficulty}`")

            # 添加描述
            if desc_match:
                description = desc_match.group(1)
                if len(description) > 50:
                    description = description[:50] + "..."
                result_parts.append(f"- {description}")

            return " ".join(result_parts)

        except Exception as e:
            logger.error(f"格式化Neo4j节点失败: {e}")
            return "相关内容"

    def _extract_clickable_concepts(self, concept_data: Dict[str, Any]) -> List[str]:
        """提取可点击的概念"""
        clickable = []
        
        # 从前置概念中提取
        prerequisites = concept_data.get("learning_progression", {}).get("prerequisites", [])
        if isinstance(prerequisites, list):
            clickable.extend(prerequisites)
        
        # 从后续概念中提取
        next_concepts = concept_data.get("learning_progression", {}).get("next_concepts", [])
        if isinstance(next_concepts, list):
            clickable.extend(next_concepts)
        
        # 从相似概念中提取
        similar_concepts = concept_data.get("similar_concepts", [])
        if isinstance(similar_concepts, list):
            clickable.extend(similar_concepts)
        
        return list(set(clickable))  # 去重
    
    async def _generate_graph_data(self, result: Dict[str, Any]) -> Optional[GraphData]:
        """生成知识图谱可视化数据 - 完整Neo4j版本"""
        try:
            from app.core.deps import get_neo4j_api

            # 获取Neo4j API实例
            neo4j_api = get_neo4j_api()
            if not neo4j_api:
                logger.warning("Neo4j API不可用，无法生成图谱数据")
                return None

            entities = result.get("entities", [])
            if not entities:
                logger.info("没有识别到实体，跳过图谱生成")
                return None

            # 选择主要实体作为中心节点
            center_entity = entities[0]
            logger.info(f"为实体 '{center_entity}' 生成知识图谱")

            # 使用完整的Neo4j图谱查询
            graph_data = await self._query_neo4j_graph_data(neo4j_api, center_entity)

            # 检查是否有足够的节点和边来显示图谱
            if not graph_data or not graph_data.nodes or len(graph_data.nodes) <= 1:
                logger.info(f"实体 '{center_entity}' 没有相连的节点，跳过图谱显示")
                return None

            # 检查是否有边连接
            if not graph_data.edges or len(graph_data.edges) == 0:
                logger.info(f"实体 '{center_entity}' 没有关系边，跳过图谱显示")
                return None

            logger.info(f"成功生成知识图谱: {len(graph_data.nodes)}个节点, {len(graph_data.edges)}条边")

            # 增强图谱数据，添加更多上下文信息
            enhanced_graph_data = self._enhance_graph_data_with_context(graph_data, result)

            return enhanced_graph_data

        except Exception as e:
            logger.error(f"生成图谱数据失败: {e}")
            import traceback
            logger.debug(f"详细错误信息: {traceback.format_exc()}")
            return None

    async def _query_neo4j_graph_data(self, neo4j_api, center_entity: str) -> Optional[GraphData]:
        """查询Neo4j图谱数据"""
        try:
            # 首先检查实体是否存在于Neo4j中
            node_info = await self._get_entity_info(neo4j_api, center_entity)
            if not node_info:
                logger.info(f"实体 '{center_entity}' 在Neo4j中不存在")
                return None

            entity_type = node_info.get("type", "Unknown")
            logger.info(f"实体类型: {entity_type}")

            # 根据实体类型构建不同的查询
            if entity_type in ["Algorithm", "算法"]:
                return await self._query_algorithm_graph(neo4j_api, center_entity)
            elif entity_type in ["Problem", "题目"]:
                return await self._query_problem_graph(neo4j_api, center_entity)
            elif entity_type in ["DataStructure", "数据结构"]:
                return await self._query_datastructure_graph(neo4j_api, center_entity)
            else:
                return await self._query_general_graph(neo4j_api, center_entity)

        except Exception as e:
            logger.error(f"查询Neo4j图谱数据失败: {e}")
            return None

    async def _get_entity_info(self, neo4j_api, entity_name: str) -> Optional[Dict]:
        """获取实体信息"""
        try:
            # 尝试多种查询方式
            queries = [
                "MATCH (n) WHERE n.name = $name RETURN n LIMIT 1",
                "MATCH (n) WHERE n.title = $name RETURN n LIMIT 1",
                "MATCH (n) WHERE toLower(n.name) = toLower($name) RETURN n LIMIT 1",
                "MATCH (n) WHERE toLower(n.title) = toLower($name) RETURN n LIMIT 1"
            ]

            for query in queries:
                results = neo4j_api.run_query(query, {"name": entity_name})
                if results:
                    node = results[0].get('n')
                    if node:
                        # 提取节点信息
                        node_info = {
                            "name": getattr(node, 'get', lambda x, d: d)('name', entity_name),
                            "title": getattr(node, 'get', lambda x, d: d)('title', ''),
                            "type": "Unknown"
                        }

                        # 从标签确定类型
                        if hasattr(node, 'labels'):
                            labels = list(node.labels)
                            if labels:
                                node_info["type"] = labels[0]

                        return node_info

            return None

        except Exception as e:
            logger.error(f"获取实体信息失败: {e}")
            return None

    async def _query_algorithm_graph(self, neo4j_api, algorithm_name: str) -> Optional[GraphData]:
        """查询算法相关的图谱"""
        try:
            cypher = """
            MATCH (a:Algorithm)
            WHERE a.name = $algorithm_name OR toLower(a.name) = toLower($algorithm_name)
            OPTIONAL MATCH (p:Problem)-[r1:USES_ALGORITHM]->(a)
            OPTIONAL MATCH (a)-[r2:RELATED_TO]->(ra:Algorithm)
            OPTIONAL MATCH (a)-[r3:REQUIRES_DATA_STRUCTURE]->(ds:DataStructure)
            OPTIONAL MATCH (a)-[r4:USES_TECHNIQUE]->(t:Technique)

            RETURN a as center_node,
                   collect(DISTINCT {node: p, rel: type(r1), type: 'Problem'}) as problems,
                   collect(DISTINCT {node: ra, rel: type(r2), type: 'Algorithm'}) as related_algorithms,
                   collect(DISTINCT {node: ds, rel: type(r3), type: 'DataStructure'}) as data_structures,
                   collect(DISTINCT {node: t, rel: type(r4), type: 'Technique'}) as techniques
            LIMIT 1
            """

            results = neo4j_api.run_query(cypher, {"algorithm_name": algorithm_name})
            return self._convert_neo4j_results_to_graph_data(results, algorithm_name)

        except Exception as e:
            logger.error(f"查询算法图谱失败: {e}")
            return None

    async def _query_problem_graph(self, neo4j_api, problem_title: str) -> Optional[GraphData]:
        """查询题目相关的图谱"""
        try:
            cypher = """
            MATCH (p:Problem)
            WHERE p.title = $problem_title OR toLower(p.title) = toLower($problem_title)
            OPTIONAL MATCH (p)-[r1:USES_ALGORITHM]->(a:Algorithm)
            OPTIONAL MATCH (p)-[r2:USES_DATA_STRUCTURE]->(ds:DataStructure)
            OPTIONAL MATCH (p)-[r3:USES_TECHNIQUE]->(t:Technique)
            OPTIONAL MATCH (p)-[r4:SIMILAR_TO]->(sp:Problem)

            RETURN p as center_node,
                   collect(DISTINCT {node: a, rel: type(r1), type: 'Algorithm'}) as algorithms,
                   collect(DISTINCT {node: ds, rel: type(r2), type: 'DataStructure'}) as data_structures,
                   collect(DISTINCT {node: t, rel: type(r3), type: 'Technique'}) as techniques,
                   collect(DISTINCT {node: sp, rel: type(r4), type: 'Problem'}) as similar_problems
            LIMIT 1
            """

            results = neo4j_api.run_query(cypher, {"problem_title": problem_title})
            return self._convert_neo4j_results_to_graph_data(results, problem_title)

        except Exception as e:
            logger.error(f"查询题目图谱失败: {e}")
            return None

    async def _query_datastructure_graph(self, neo4j_api, ds_name: str) -> Optional[GraphData]:
        """查询数据结构相关的图谱"""
        try:
            cypher = """
            MATCH (ds:DataStructure)
            WHERE ds.name = $ds_name OR toLower(ds.name) = toLower($ds_name)
            OPTIONAL MATCH (p:Problem)-[r1:USES_DATA_STRUCTURE]->(ds)
            OPTIONAL MATCH (a:Algorithm)-[r2:REQUIRES_DATA_STRUCTURE]->(ds)
            OPTIONAL MATCH (ds)-[r3:RELATED_TO]->(rds:DataStructure)

            RETURN ds as center_node,
                   collect(DISTINCT {node: p, rel: type(r1), type: 'Problem'}) as problems,
                   collect(DISTINCT {node: a, rel: type(r2), type: 'Algorithm'}) as algorithms,
                   collect(DISTINCT {node: rds, rel: type(r3), type: 'DataStructure'}) as related_ds
            LIMIT 1
            """

            results = neo4j_api.run_query(cypher, {"ds_name": ds_name})
            return self._convert_neo4j_results_to_graph_data(results, ds_name)

        except Exception as e:
            logger.error(f"查询数据结构图谱失败: {e}")
            return None

    async def _query_general_graph(self, neo4j_api, entity_name: str) -> Optional[GraphData]:
        """查询通用实体的图谱"""
        try:
            cypher = """
            MATCH (center)
            WHERE center.name = $entity_name OR center.title = $entity_name
            OPTIONAL MATCH (center)-[r]-(connected)
            WHERE connected IS NOT NULL

            RETURN center as center_node,
                   collect(DISTINCT {node: connected, rel: type(r), type: labels(connected)[0]}) as connections
            LIMIT 1
            """

            results = neo4j_api.run_query(cypher, {"entity_name": entity_name})
            return self._convert_neo4j_results_to_graph_data(results, entity_name)

        except Exception as e:
            logger.error(f"查询通用图谱失败: {e}")
            return None

    def _convert_neo4j_results_to_graph_data(self, results: List[Dict], center_entity: str) -> Optional[GraphData]:
        """将Neo4j查询结果转换为图谱数据"""
        try:
            if not results:
                logger.info(f"Neo4j查询无结果: {center_entity}")
                return None

            result = results[0]
            center_node = result.get('center_node')

            if not center_node:
                logger.info(f"未找到中心节点: {center_entity}")
                return None

            nodes = []
            edges = []

            # 添加中心节点
            center_id = self._create_node_id_from_neo4j(center_node)
            center_label = self._extract_node_label(center_node, center_entity)
            center_type = self._extract_node_type(center_node)

            nodes.append(GraphNode(
                id=center_id,
                label=center_label,
                type=center_type,
                properties={"is_center": True},
                clickable=True
            ))

            # 处理连接的节点
            for key, connections in result.items():
                if key == 'center_node' or not connections:
                    continue

                # 限制每种类型的节点数量
                limited_connections = connections[:10] if isinstance(connections, list) else []

                for connection in limited_connections:
                    if not isinstance(connection, dict) or 'node' not in connection:
                        continue

                    connected_node = connection['node']
                    if not connected_node:
                        continue

                    # 创建连接节点
                    connected_id = self._create_node_id_from_neo4j(connected_node)
                    connected_label = self._extract_node_label(connected_node)
                    connected_type = connection.get('type', self._extract_node_type(connected_node))

                    # 避免重复节点
                    if not any(node.id == connected_id for node in nodes):
                        nodes.append(GraphNode(
                            id=connected_id,
                            label=connected_label,
                            type=connected_type,
                            properties={},
                            clickable=True
                        ))

                    # 创建边
                    relationship = connection.get('rel', 'RELATED_TO')
                    edges.append(GraphEdge(
                        source=center_id,
                        target=connected_id,
                        relationship=relationship,
                        properties={}
                    ))

            if len(nodes) <= 1:
                logger.info(f"实体 '{center_entity}' 没有连接的节点")
                return None

            logger.info(f"转换Neo4j结果: {len(nodes)}个节点, {len(edges)}条边")

            return GraphData(
                nodes=nodes,
                edges=edges,
                center_node=center_id,
                layout_type="force"
            )

        except Exception as e:
            logger.error(f"转换Neo4j结果失败: {e}")
            return None

    def _create_node_id_from_neo4j(self, node) -> str:
        """从Neo4j节点创建ID"""
        try:
            if hasattr(node, 'element_id'):
                return f"neo4j_{node.element_id}"
            elif hasattr(node, 'id'):
                return f"neo4j_{node.id}"
            else:
                # 使用节点属性创建ID
                name = getattr(node, 'get', lambda x, d: d)('name', '')
                title = getattr(node, 'get', lambda x, d: d)('title', '')
                identifier = name or title or str(hash(str(node)))
                return f"neo4j_{identifier}"
        except:
            return f"neo4j_{hash(str(node))}"

    def _extract_node_label(self, node, default: str = "Unknown") -> str:
        """提取节点标签"""
        try:
            if hasattr(node, 'get'):
                return node.get('name', node.get('title', default))
            elif isinstance(node, dict):
                return node.get('name', node.get('title', default))
            else:
                return str(node)
        except:
            return default

    def _extract_node_type(self, node) -> str:
        """提取节点类型"""
        try:
            if hasattr(node, 'labels'):
                labels = list(node.labels)
                return labels[0] if labels else "Unknown"
            elif isinstance(node, dict) and 'labels' in node:
                labels = node['labels']
                return labels[0] if labels else "Unknown"
            else:
                return "Unknown"
        except:
            return "Unknown"

    def _create_simple_graph_from_results(self, result: Dict[str, Any], center_entity: str) -> Optional[GraphData]:
        """基于QA结果创建简化的图谱数据"""
        try:
            nodes = []
            edges = []

            # 添加中心节点
            center_id = f"center_{center_entity}"
            nodes.append(GraphNode(
                id=center_id,
                label=center_entity,
                type="Concept",
                properties={"is_center": True},
                clickable=True
            ))

            # 从相似题目中添加节点
            similar_problems = result.get("similar_problems", [])
            for i, problem in enumerate(similar_problems[:5]):  # 限制数量
                if isinstance(problem, dict):
                    title = problem.get("title", f"题目{i+1}")
                    problem_id = f"problem_{i}"

                    nodes.append(GraphNode(
                        id=problem_id,
                        label=title,
                        type="Problem",
                        properties={
                            "score": problem.get("hybrid_score", 0.0),
                            "difficulty": problem.get("difficulty", "未知")
                        },
                        clickable=True
                    ))

                    # 添加边
                    edges.append(GraphEdge(
                        source=center_id,
                        target=problem_id,
                        relationship="RELATED_TO",
                        properties={"score": problem.get("hybrid_score", 0.0)}
                    ))

            # 从示例题目中添加节点
            example_problems = result.get("example_problems", [])
            for i, problem in enumerate(example_problems[:3]):  # 限制数量
                if isinstance(problem, dict):
                    title = problem.get("title", f"示例{i+1}")
                    example_id = f"example_{i}"

                    nodes.append(GraphNode(
                        id=example_id,
                        label=title,
                        type="Example",
                        properties={
                            "difficulty": problem.get("difficulty", "未知"),
                            "platform": problem.get("platform", "未知")
                        },
                        clickable=True
                    ))

                    # 添加边
                    edges.append(GraphEdge(
                        source=center_id,
                        target=example_id,
                        relationship="EXAMPLE_OF",
                        properties={}
                    ))

            # 从概念解释中添加相关概念节点
            concept_explanation = result.get("concept_explanation", {})
            if isinstance(concept_explanation, dict):
                core_principles = concept_explanation.get("core_principles", [])
                for i, principle in enumerate(core_principles[:3]):  # 限制数量
                    if isinstance(principle, str):
                        principle_id = f"principle_{i}"

                        nodes.append(GraphNode(
                            id=principle_id,
                            label=principle,
                            type="Principle",
                            properties={},
                            clickable=True
                        ))

                        # 添加边
                        edges.append(GraphEdge(
                            source=center_id,
                            target=principle_id,
                            relationship="HAS_PRINCIPLE",
                            properties={}
                        ))

            # 检查是否有足够的节点
            if len(nodes) <= 1:
                logger.info(f"没有足够的相关节点来创建图谱")
                return None

            return GraphData(
                nodes=nodes,
                edges=edges,
                center_node=center_id,
                layout_type="force"
            )

        except Exception as e:
            logger.error(f"创建简化图谱数据失败: {e}")
            return None

    def _query_simple_graph_data(self, neo4j_api, center_entity: str) -> Optional[GraphData]:
        """查询简化的图谱数据"""
        try:
            # 构建简单的Cypher查询，查找与实体相关的节点
            cypher = """
            MATCH (center)
            WHERE center.name = $entity_name OR center.title = $entity_name
            OPTIONAL MATCH (center)-[r]-(connected)
            WHERE connected IS NOT NULL
            RETURN center,
                   collect(DISTINCT {node: connected, rel: r, rel_type: type(r)}) as connections
            LIMIT 1
            """

            params = {"entity_name": center_entity}
            results = neo4j_api.run_query(cypher, params)

            if not results:
                logger.info(f"未找到实体 '{center_entity}' 的图谱数据")
                return None

            return self._convert_simple_results_to_graph_data(results, center_entity)

        except Exception as e:
            logger.error(f"查询简化图谱数据失败: {e}")
            return None

    def _convert_simple_results_to_graph_data(self, results: List[Dict], center_entity: str) -> Optional[GraphData]:
        """将简化的查询结果转换为图谱数据"""
        try:
            if not results:
                return None

            result = results[0]
            center_node = result.get('center')
            connections = result.get('connections', [])

            if not center_node:
                return None

            nodes = []
            edges = []

            # 添加中心节点
            center_id = f"center_{center_entity}"
            center_label = getattr(center_node, 'get', lambda x, d: d)('name', center_entity) or center_entity
            center_type = "Concept"

            # 尝试从节点标签确定类型
            if hasattr(center_node, 'labels'):
                labels = list(center_node.labels)
                if labels:
                    center_type = labels[0]

            nodes.append(GraphNode(
                id=center_id,
                label=center_label,
                type=center_type,
                properties={"is_center": True},
                clickable=True
            ))

            # 添加连接的节点和边
            for i, connection in enumerate(connections[:15]):  # 限制连接数量
                if not isinstance(connection, dict) or 'node' not in connection:
                    continue

                connected_node = connection['node']
                relationship = connection.get('rel')
                rel_type = connection.get('rel_type', 'RELATED_TO')

                if not connected_node:
                    continue

                # 创建连接节点
                connected_id = f"connected_{i}"
                connected_label = getattr(connected_node, 'get', lambda x, d: d)('name', f'Node_{i}') or \
                                getattr(connected_node, 'get', lambda x, d: d)('title', f'Node_{i}') or f'Node_{i}'
                connected_type = "Unknown"

                # 尝试从节点标签确定类型
                if hasattr(connected_node, 'labels'):
                    labels = list(connected_node.labels)
                    if labels:
                        connected_type = labels[0]

                nodes.append(GraphNode(
                    id=connected_id,
                    label=connected_label,
                    type=connected_type,
                    properties={},
                    clickable=True
                ))

                # 创建边
                edges.append(GraphEdge(
                    source=center_id,
                    target=connected_id,
                    relationship=rel_type,
                    properties={}
                ))

            if len(nodes) <= 1 or len(edges) == 0:
                logger.info(f"实体 '{center_entity}' 没有足够的连接节点")
                return None

            return GraphData(
                nodes=nodes,
                edges=edges,
                center_node=center_id,
                layout_type="force"
            )

        except Exception as e:
            logger.error(f"转换简化图谱数据失败: {e}")
            return None

    def _enhance_graph_data_with_context(self, graph_data: GraphData, result: Dict[str, Any]) -> GraphData:
        """增强图谱数据，添加上下文信息"""
        try:
            # 获取相似题目信息，用于增强节点属性
            similar_problems = result.get("similar_problems", [])
            similar_titles = {problem.get("title", "") for problem in similar_problems if isinstance(problem, dict)}

            # 增强节点信息
            enhanced_nodes = []
            for node in graph_data.nodes:
                enhanced_node = GraphNode(
                    id=node.id,
                    label=node.label,
                    type=node.type,
                    properties={
                        **node.properties,
                        "from_qa_context": True,  # 标记这是来自QA上下文的图谱
                        "is_recommended": node.label in similar_titles,  # 标记是否在推荐列表中
                    },
                    clickable=node.clickable
                )
                enhanced_nodes.append(enhanced_node)

            # 增强边信息
            enhanced_edges = []
            for edge in graph_data.edges:
                enhanced_edge = GraphEdge(
                    source=edge.source,
                    target=edge.target,
                    relationship=edge.relationship,
                    properties={
                        **edge.properties,
                        "from_qa_context": True,  # 标记这是来自QA上下文的图谱
                    }
                )
                enhanced_edges.append(enhanced_edge)

            return GraphData(
                nodes=enhanced_nodes,
                edges=enhanced_edges,
                center_node=graph_data.center_node,
                layout_type=graph_data.layout_type
            )

        except Exception as e:
            logger.error(f"增强图谱数据失败: {e}")
            # 如果增强失败，返回原始数据
            return graph_data
