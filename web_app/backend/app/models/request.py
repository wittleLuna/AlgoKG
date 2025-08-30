from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class QueryType(str, Enum):
    """查询类型枚举"""
    CONCEPT_EXPLANATION = "concept_explanation"
    PROBLEM_RECOMMENDATION = "problem_recommendation"
    SIMILAR_PROBLEMS = "similar_problems"
    LEARNING_PATH = "learning_path"
    CODE_IMPLEMENTATION = "code_implementation"

class DifficultyLevel(str, Enum):
    """难度级别枚举"""
    EASY = "简单"
    MEDIUM = "中等"
    HARD = "困难"

class QARequest(BaseModel):
    """问答请求模型"""
    query: str = Field(..., description="用户查询内容", min_length=1, max_length=1000)
    query_type: Optional[QueryType] = Field(None, description="查询类型")
    difficulty: Optional[DifficultyLevel] = Field(None, description="难度级别")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="上下文信息")
    session_id: Optional[str] = Field(None, description="会话ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "请解释动态规划的概念和原理",
                "query_type": "concept_explanation",
                "difficulty": "中等",
                "context": {},
                "session_id": "session_123"
            }
        }

class SimilarProblemsRequest(BaseModel):
    """相似题目推荐请求"""
    problem_title: str = Field(..., description="目标题目标题")
    count: int = Field(default=5, ge=1, le=20, description="推荐数量")
    include_solutions: bool = Field(default=True, description="是否包含解决方案")
    
    class Config:
        json_schema_extra = {
            "example": {
                "problem_title": "不同的子序列",
                "count": 5,
                "include_solutions": True
            }
        }

class GraphQueryRequest(BaseModel):
    """图谱查询请求"""
    entity_name: str = Field(..., description="实体名称")
    entity_type: Optional[str] = Field(None, description="实体类型")
    depth: int = Field(default=2, ge=1, le=5, description="查询深度")
    limit: int = Field(default=20, ge=1, le=100, description="结果限制")
    
    class Config:
        json_schema_extra = {
            "example": {
                "entity_name": "动态规划",
                "entity_type": "Algorithm",
                "depth": 2,
                "limit": 20
            }
        }

class ReasoningPathRequest(BaseModel):
    """推理路径请求"""
    query: str = Field(..., description="查询内容")
    enable_streaming: bool = Field(default=True, description="是否启用流式响应")
    include_intermediate_steps: bool = Field(default=True, description="是否包含中间步骤")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "推荐一些动态规划的题目",
                "enable_streaming": True,
                "include_intermediate_steps": True
            }
        }

class FeedbackRequest(BaseModel):
    """用户反馈请求"""
    session_id: str = Field(..., description="会话ID")
    query: str = Field(..., description="原始查询")
    response_id: str = Field(..., description="响应ID")
    rating: int = Field(..., ge=1, le=5, description="评分(1-5)")
    feedback_text: Optional[str] = Field(None, description="反馈文本")
    helpful_parts: Optional[List[str]] = Field(default_factory=list, description="有用的部分")
    improvement_suggestions: Optional[str] = Field(None, description="改进建议")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_123",
                "query": "请解释动态规划",
                "response_id": "resp_456",
                "rating": 4,
                "feedback_text": "解释很清楚，但希望有更多例子",
                "helpful_parts": ["概念解释", "核心原理"],
                "improvement_suggestions": "增加更多实际应用案例"
            }
        }

class ConceptLinkRequest(BaseModel):
    """概念链接点击请求"""
    concept_name: str = Field(..., description="概念名称")
    source_query: str = Field(..., description="来源查询")
    context_type: str = Field(..., description="上下文类型")
    session_id: Optional[str] = Field(None, description="会话ID")

    class Config:
        json_schema_extra = {
            "example": {
                "concept_name": "动态规划",
                "source_query": "请解释算法复杂度",
                "context_type": "concept_explanation",
                "session_id": "session_123"
            }
        }
