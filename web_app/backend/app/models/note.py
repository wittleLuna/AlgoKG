"""
笔记相关的数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class FileFormat(str, Enum):
    """文件格式枚举"""
    TXT = "txt"
    MD = "md"
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"

class NoteType(str, Enum):
    """笔记类型枚举"""
    ALGORITHM = "algorithm"
    DATA_STRUCTURE = "data_structure"
    PROBLEM_SOLVING = "problem_solving"
    THEORY = "theory"
    GENERAL = "general"

# 内容分析结果
class ContentAnalysis(BaseModel):
    """内容分析结果"""
    word_count: int = Field(0, description="词数统计")
    algorithm_keywords: List[str] = Field(default_factory=list, description="算法关键词")
    complexity_mentions: List[str] = Field(default_factory=list, description="复杂度提及")
    code_blocks: List[Dict[str, str]] = Field(default_factory=list, description="代码块")
    difficulty_level: str = Field("unknown", description="难度级别")
    topics: List[str] = Field(default_factory=list, description="主题")
    summary: str = Field("", description="摘要")

# 基础笔记模型
class NoteBase(BaseModel):
    """笔记基础模型"""
    title: str = Field(..., min_length=1, max_length=200, description="笔记标题")
    description: str = Field("", max_length=1000, description="笔记描述")
    note_type: NoteType = Field(NoteType.GENERAL, description="笔记类型")
    file_format: FileFormat = Field(FileFormat.TXT, description="文件格式")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    is_public: bool = Field(False, description="是否公开")

class NoteUploadRequest(NoteBase):
    """笔记上传请求模型"""
    extract_entities: bool = Field(True, description="是否抽取实体")
    file_content: Optional[str] = Field(None, description="直接文本内容")
    file_data: Optional[bytes] = Field(None, description="文件二进制数据")

class Note(NoteBase):
    """笔记模型"""
    id: str = Field(..., description="笔记ID")
    content: str = Field(..., description="笔记内容")
    file_size: int = Field(0, description="文件大小")
    user_id: str = Field(..., description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    analysis_data: Dict[str, Any] = Field(default_factory=dict, description="分析数据")

    class Config:
        from_attributes = True

class NoteResponse(NoteBase):
    """笔记响应模型"""
    id: str = Field(..., description="笔记ID")
    content: str = Field(..., description="笔记内容")
    file_size: int = Field(0, description="文件大小")
    user_id: str = Field(..., description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    analysis_data: Dict[str, Any] = Field(default_factory=dict, description="分析数据")
    entities_extracted: bool = Field(False, description="是否已抽取实体")
    entity_count: int = Field(0, description="实体数量")

    class Config:
        from_attributes = True

# 笔记列表请求
class NoteListRequest(BaseModel):
    """笔记列表请求模型"""
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页大小")
    note_type: Optional[NoteType] = Field(None, description="笔记类型筛选")
    search_query: Optional[str] = Field(None, max_length=200, description="搜索关键词")

class NoteListResponse(BaseModel):
    """笔记列表响应模型"""
    notes: List[NoteResponse] = Field(..., description="笔记列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")

# 实体相关模型
class EntityInfo(BaseModel):
    """实体信息"""
    id: str = Field(..., description="实体ID")
    name: str = Field(..., description="实体名称")
    type: str = Field(..., description="实体类型")
    description: str = Field("", description="实体描述")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="置信度")

class RelationInfo(BaseModel):
    """关系信息"""
    source: str = Field(..., description="源实体")
    target: str = Field(..., description="目标实体")
    type: str = Field(..., description="关系类型")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="置信度")

class EntityExtractionResult(BaseModel):
    """实体抽取结果"""
    note_id: str = Field(..., description="笔记ID")
    entities: List[EntityInfo] = Field(default_factory=list, description="实体列表")
    relations: List[RelationInfo] = Field(default_factory=list, description="关系列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    extracted: bool = Field(False, description="是否已抽取")

# 知识图谱融合相关模型
class GraphNodeCandidate(BaseModel):
    """图节点候选"""
    entity_id: str = Field(..., description="实体ID")
    entity_name: str = Field(..., description="实体名称")
    entity_type: str = Field(..., description="实体类型")
    should_merge: bool = Field(False, description="是否应该合并")
    existing_node_id: Optional[str] = Field(None, description="现有节点ID")
    merge_confidence: float = Field(0.0, description="合并置信度")
    source_note_id: str = Field(..., description="来源笔记ID")

class GraphIntegrationPlan(BaseModel):
    """图谱集成计划"""
    note_id: str = Field(..., description="笔记ID")
    new_nodes: List[GraphNodeCandidate] = Field(default_factory=list, description="新节点")
    merge_nodes: List[GraphNodeCandidate] = Field(default_factory=list, description="合并节点")
    new_relations: List[RelationInfo] = Field(default_factory=list, description="新关系")
    integration_strategy: str = Field("conservative", description="集成策略")

class GraphIntegrationResult(BaseModel):
    """图谱集成结果"""
    note_id: str = Field(..., description="笔记ID")
    nodes_created: int = Field(0, description="创建的节点数")
    nodes_merged: int = Field(0, description="合并的节点数")
    relations_created: int = Field(0, description="创建的关系数")
    success: bool = Field(False, description="是否成功")
    error_message: Optional[str] = Field(None, description="错误信息")
    integration_details: Dict[str, Any] = Field(default_factory=dict, description="集成详情")

# 统计信息模型
class NoteStatistics(BaseModel):
    """笔记统计信息"""
    total_notes: int = Field(0, description="总笔记数")
    notes_by_type: Dict[str, int] = Field(default_factory=dict, description="按类型统计")
    notes_with_entities: int = Field(0, description="已抽取实体的笔记数")
    total_entities: int = Field(0, description="总实体数")
    entities_by_type: Dict[str, int] = Field(default_factory=dict, description="按类型统计实体")
    recent_uploads: int = Field(0, description="最近上传数")

# 搜索相关模型
class NoteSearchRequest(BaseModel):
    """笔记搜索请求"""
    query: str = Field(..., min_length=1, description="搜索查询")
    note_types: Optional[List[NoteType]] = Field(None, description="笔记类型筛选")
    tags: Optional[List[str]] = Field(None, description="标签筛选")
    entity_types: Optional[List[str]] = Field(None, description="实体类型筛选")
    include_content: bool = Field(True, description="是否包含内容搜索")
    include_entities: bool = Field(True, description="是否包含实体搜索")
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页大小")

class NoteSearchResult(BaseModel):
    """笔记搜索结果"""
    note: NoteResponse = Field(..., description="笔记信息")
    relevance_score: float = Field(0.0, description="相关性得分")
    matched_entities: List[str] = Field(default_factory=list, description="匹配的实体")
    matched_content: Optional[str] = Field(None, description="匹配的内容片段")

class NoteSearchResponse(BaseModel):
    """笔记搜索响应"""
    results: List[NoteSearchResult] = Field(..., description="搜索结果")
    total: int = Field(..., description="总结果数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    query: str = Field(..., description="搜索查询")
    search_time: float = Field(0.0, description="搜索耗时(秒)")
