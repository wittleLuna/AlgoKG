from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

class ResponseStatus(str, Enum):
    """响应状态枚举"""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"
    PROCESSING = "processing"

class AgentStep(BaseModel):
    """智能体执行步骤"""
    agent_name: str = Field(..., description="智能体名称")
    step_type: str = Field(..., description="步骤类型")
    description: str = Field(..., description="步骤描述")
    status: ResponseStatus = Field(..., description="执行状态")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    result: Optional[Dict[str, Any]] = Field(None, description="执行结果")
    confidence: Optional[float] = Field(None, description="置信度")

class ConceptExplanation(BaseModel):
    """概念解释"""
    concept_name: str = Field(..., description="概念名称")
    definition: str = Field(..., description="定义")
    core_principles: List[str] = Field(default_factory=list, description="核心原理")
    when_to_use: Optional[str] = Field(None, description="使用场景")
    advantages: List[str] = Field(default_factory=list, description="优点")
    disadvantages: List[str] = Field(default_factory=list, description="缺点")
    implementation_key_points: List[str] = Field(default_factory=list, description="实现要点")
    common_variations: List[str] = Field(default_factory=list, description="常见变种")
    real_world_applications: List[str] = Field(default_factory=list, description="实际应用")
    learning_progression: Dict[str, List[str]] = Field(default_factory=dict, description="学习路径")
    visual_explanation: Optional[str] = Field(None, description="可视化解释")
    clickable_concepts: List[str] = Field(default_factory=list, description="可点击的相关概念")

class ProblemInfo(BaseModel):
    """题目信息"""
    id: str = Field(..., description="题目ID")
    title: str = Field(..., description="题目标题")
    description: Optional[str] = Field(None, description="题目描述")
    difficulty: Optional[str] = Field(None, description="难度")
    platform: Optional[str] = Field(None, description="平台")
    url: Optional[str] = Field(None, description="链接")
    algorithm_tags: List[str] = Field(default_factory=list, description="算法标签")
    data_structure_tags: List[str] = Field(default_factory=list, description="数据结构标签")
    technique_tags: List[str] = Field(default_factory=list, description="技巧标签")
    solutions: List[Dict[str, Any]] = Field(default_factory=list, description="解决方案")
    code_implementations: List[Dict[str, Any]] = Field(default_factory=list, description="代码实现")
    key_insights: List[Dict[str, Any]] = Field(default_factory=list, description="关键洞察")
    step_by_step_explanation: List[Dict[str, Any]] = Field(default_factory=list, description="步骤解释")
    clickable: bool = Field(default=True, description="是否可点击")

class SimilarProblem(BaseModel):
    """相似题目"""
    title: str = Field(..., description="题目标题")
    hybrid_score: float = Field(..., description="混合相似度分数")
    embedding_score: float = Field(..., description="嵌入相似度分数")
    tag_score: float = Field(..., description="标签相似度分数")
    shared_tags: List[str] = Field(default_factory=list, description="共享标签")
    learning_path: str = Field(..., description="学习路径")
    recommendation_reason: str = Field(..., description="推荐理由")
    learning_path_explanation: str = Field(..., description="学习路径解释")
    recommendation_strength: str = Field(..., description="推荐强度")
    complete_info: Optional[ProblemInfo] = Field(None, description="完整题目信息")
    clickable: bool = Field(default=True, description="是否可点击")

class RecommendationCard(BaseModel):
    """推荐卡片"""
    title: str = Field(..., description="标题")
    hybrid_score: float = Field(..., description="混合分数")
    embedding_score: float = Field(..., description="嵌入分数")
    tag_score: float = Field(..., description="标签分数")
    shared_tags: List[str] = Field(default_factory=list, description="共享标签")
    learning_path: str = Field(..., description="学习路径")
    recommendation_reason: str = Field(..., description="推荐理由")
    learning_path_explanation: str = Field(..., description="学习路径解释")
    clickable: bool = Field(default=True, description="是否可点击")

class GraphNode(BaseModel):
    """图节点"""
    id: str = Field(..., description="节点ID")
    label: str = Field(..., description="节点标签")
    type: str = Field(..., description="节点类型")
    properties: Dict[str, Any] = Field(default_factory=dict, description="节点属性")
    clickable: bool = Field(default=True, description="是否可点击")

class GraphEdge(BaseModel):
    """图边"""
    source: str = Field(..., description="源节点ID")
    target: str = Field(..., description="目标节点ID")
    relationship: str = Field(..., description="关系类型")
    properties: Dict[str, Any] = Field(default_factory=dict, description="边属性")

class GraphData(BaseModel):
    """图数据"""
    nodes: List[GraphNode] = Field(default_factory=list, description="节点列表")
    edges: List[GraphEdge] = Field(default_factory=list, description="边列表")
    center_node: Optional[str] = Field(None, description="中心节点ID")
    layout_type: str = Field(default="force", description="布局类型")

class QAResponse(BaseModel):
    """问答响应"""
    response_id: str = Field(..., description="响应ID")
    query: str = Field(..., description="原始查询")
    intent: str = Field(..., description="查询意图")
    entities: List[str] = Field(default_factory=list, description="识别的实体")
    
    # 核心内容
    concept_explanation: Optional[ConceptExplanation] = Field(None, description="概念解释")
    example_problems: List[ProblemInfo] = Field(default_factory=list, description="示例题目")
    similar_problems: List[SimilarProblem] = Field(default_factory=list, description="相似题目")
    recommendations_struct: Optional[Dict[str, Any]] = Field(None, description="推荐结构")
    integrated_response: str = Field(..., description="整合回答")
    
    # 可视化数据
    graph_data: Optional[GraphData] = Field(None, description="图谱数据")
    reasoning_path: List[AgentStep] = Field(default_factory=list, description="推理路径")
    
    # 元数据
    status: ResponseStatus = Field(default=ResponseStatus.SUCCESS, description="响应状态")
    confidence: float = Field(default=0.0, description="整体置信度")
    processing_time: float = Field(default=0.0, description="处理时间(秒)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class StreamingResponse(BaseModel):
    """流式响应"""
    type: str = Field(..., description="消息类型")
    data: Dict[str, Any] = Field(..., description="数据内容")
    step_id: Optional[str] = Field(None, description="步骤ID")
    is_final: bool = Field(default=False, description="是否为最终消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")

class ErrorResponse(BaseModel):
    """错误响应"""
    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="版本号")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    services: Dict[str, str] = Field(default_factory=dict, description="依赖服务状态")
