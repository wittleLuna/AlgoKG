from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse as FastAPIStreamingResponse
from typing import List, Dict, Any
import json
import asyncio
import logging

from app.models import (
    QARequest, QAResponse, SimilarProblemsRequest, 
    ConceptLinkRequest, FeedbackRequest, StreamingResponse,
    ErrorResponse
)
from app.services.qa_service import QAService
from app.core.deps import get_current_qa_system
from qa.multi_agent_qa import GraphEnhancedMultiAgentSystem

logger = logging.getLogger(__name__)
router = APIRouter()

# 依赖注入：获取QA服务
async def get_qa_service(
    qa_system: GraphEnhancedMultiAgentSystem = Depends(get_current_qa_system)
) -> QAService:
    return QAService(qa_system)

@router.post("/query", response_model=QAResponse)
async def process_query(
    request: QARequest,
    qa_service: QAService = Depends(get_qa_service)
):
    """
    处理问答查询
    
    - **query**: 用户查询内容
    - **query_type**: 查询类型（可选）
    - **difficulty**: 难度级别（可选）
    - **context**: 上下文信息（可选）
    - **session_id**: 会话ID（可选）
    """
    try:
        response = await qa_service.process_query(request)
        return response
    except Exception as e:
        logger.error(f"处理查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query/stream")
async def process_query_streaming(
    request: QARequest,
    qa_service: QAService = Depends(get_qa_service)
):
    """
    流式处理问答查询，实时返回推理过程
    """
    async def generate_stream():
        try:
            async for chunk in qa_service.process_query_streaming(request):
                # 转换为SSE格式
                data = json.dumps(chunk.dict(), ensure_ascii=False, default=str)
                yield f"data: {data}\n\n"
        except Exception as e:
            logger.error(f"流式处理失败: {e}")
            error_chunk = StreamingResponse(
                type="error",
                data={"error": str(e)},
                is_final=True
            )
            data = json.dumps(error_chunk.dict(), ensure_ascii=False, default=str)
            yield f"data: {data}\n\n"
    
    return FastAPIStreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@router.post("/similar-problems", response_model=List[Dict[str, Any]])
async def get_similar_problems(
    request: SimilarProblemsRequest,
    qa_service: QAService = Depends(get_qa_service)
):
    """
    获取相似题目推荐
    
    - **problem_title**: 目标题目标题
    - **count**: 推荐数量
    - **include_solutions**: 是否包含解决方案
    """
    try:
        similar_problems = await qa_service.get_similar_problems(
            request.problem_title, 
            request.count
        )
        return [problem.dict() for problem in similar_problems]
    except Exception as e:
        logger.error(f"获取相似题目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/concept/click", response_model=QAResponse)
async def handle_concept_click(
    request: ConceptLinkRequest,
    qa_service: QAService = Depends(get_qa_service)
):
    """
    处理概念点击事件，触发新一轮问答
    
    - **concept_name**: 点击的概念名称
    - **source_query**: 来源查询
    - **context_type**: 上下文类型
    - **session_id**: 会话ID（可选）
    """
    try:
        response = await qa_service.handle_concept_click(
            request.concept_name,
            request.source_query,
            request.context_type
        )
        return response
    except Exception as e:
        logger.error(f"处理概念点击失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    background_tasks: BackgroundTasks
):
    """
    提交用户反馈
    
    - **session_id**: 会话ID
    - **query**: 原始查询
    - **response_id**: 响应ID
    - **rating**: 评分(1-5)
    - **feedback_text**: 反馈文本（可选）
    - **helpful_parts**: 有用的部分（可选）
    - **improvement_suggestions**: 改进建议（可选）
    """
    try:
        # 在后台处理反馈
        background_tasks.add_task(process_feedback, request)
        return {"message": "反馈已提交，感谢您的建议！"}
    except Exception as e:
        logger.error(f"提交反馈失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/history")
async def get_session_history(
    session_id: str,
    limit: int = 10,
    qa_service: QAService = Depends(get_qa_service)
):
    """
    获取会话历史记录
    
    - **session_id**: 会话ID
    - **limit**: 返回记录数量限制
    """
    try:
        if session_id in qa_service.active_sessions:
            queries = qa_service.active_sessions[session_id]["queries"]
            return {
                "session_id": session_id,
                "total_queries": len(queries),
                "queries": queries[-limit:] if limit > 0 else queries
            }
        else:
            return {
                "session_id": session_id,
                "total_queries": 0,
                "queries": []
            }
    except Exception as e:
        logger.error(f"获取会话历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}")
async def clear_session(
    session_id: str,
    qa_service: QAService = Depends(get_qa_service)
):
    """
    清除会话数据
    
    - **session_id**: 会话ID
    """
    try:
        if session_id in qa_service.active_sessions:
            del qa_service.active_sessions[session_id]
            return {"message": f"会话 {session_id} 已清除"}
        else:
            return {"message": f"会话 {session_id} 不存在"}
    except Exception as e:
        logger.error(f"清除会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 后台任务：处理用户反馈
async def process_feedback(feedback: FeedbackRequest):
    """处理用户反馈的后台任务"""
    try:
        # 这里可以将反馈存储到数据库或发送到分析系统
        logger.info(f"收到用户反馈: 会话={feedback.session_id}, 评分={feedback.rating}")
        
        # 可以添加以下功能：
        # 1. 存储到数据库
        # 2. 发送到监控系统
        # 3. 触发模型优化流程
        # 4. 生成反馈报告
        
        # 模拟处理时间
        await asyncio.sleep(1)
        
        logger.info(f"反馈处理完成: {feedback.response_id}")
        
    except Exception as e:
        logger.error(f"处理反馈失败: {e}")

# 注意：异常处理器应该在main.py中的FastAPI应用实例上注册，而不是在router上
# 这里移除了错误的exception_handler装饰器
