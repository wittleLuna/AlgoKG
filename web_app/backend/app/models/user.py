"""
用户相关的数据模型
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import re
from enum import Enum


class UserRole(str, Enum):
    """用户角色枚举"""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class UserStatus(str, Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class UserBase(BaseModel):
    """用户基础信息"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱地址")
    full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")

    def validate_email(self):
        """验证邮箱格式"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.email):
            raise ValueError("邮箱格式不正确")


class UserCreate(UserBase):
    """创建用户请求模型"""
    password: str = Field(..., min_length=6, max_length=128, description="密码")


class UserUpdate(BaseModel):
    """更新用户信息请求模型"""
    full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")


class UserPasswordUpdate(BaseModel):
    """更新密码请求模型"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")


class UserInDB(UserBase):
    """数据库中的用户模型"""
    id: int
    hashed_password: str
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    login_count: int = 0
    
    class Config:
        from_attributes = True


class User(UserBase):
    """返回给前端的用户模型（不包含敏感信息）"""
    id: int
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    login_count: int = 0
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """用户登录请求模型"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class Token(BaseModel):
    """JWT令牌响应模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User


class TokenData(BaseModel):
    """JWT令牌数据模型"""
    user_id: Optional[int] = None
    username: Optional[str] = None


class UserStats(BaseModel):
    """用户统计信息"""
    total_questions: int = 0
    total_sessions: int = 0
    total_favorites: int = 0
    total_uploads: int = 0
    last_activity: Optional[datetime] = None


class UserProfile(User):
    """用户详细资料（包含统计信息）"""
    stats: UserStats


# 收藏相关模型
class FavoriteBase(BaseModel):
    """收藏基础模型"""
    item_type: str = Field(..., description="收藏项类型：question, session, graph_node")
    item_id: str = Field(..., description="收藏项ID")
    title: Optional[str] = Field(None, description="收藏项标题")
    description: Optional[str] = Field(None, description="收藏项描述")


class FavoriteCreate(FavoriteBase):
    """创建收藏请求模型"""
    pass


class Favorite(FavoriteBase):
    """收藏响应模型"""
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# 搜索历史相关模型
class SearchHistoryBase(BaseModel):
    """搜索历史基础模型"""
    query: str = Field(..., max_length=500, description="搜索查询")
    search_type: str = Field(..., description="搜索类型：qa, graph, problem")
    results_count: int = Field(0, description="搜索结果数量")


class SearchHistoryCreate(SearchHistoryBase):
    """创建搜索历史请求模型"""
    pass


class SearchHistory(SearchHistoryBase):
    """搜索历史响应模型"""
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# 用户会话相关模型
class SessionBase(BaseModel):
    """会话基础模型"""
    title: str = Field(..., max_length=200, description="会话标题")
    description: Optional[str] = Field(None, max_length=1000, description="会话描述")


class SessionCreate(SessionBase):
    """创建会话请求模型"""
    pass


class SessionUpdate(BaseModel):
    """更新会话请求模型"""
    title: Optional[str] = Field(None, max_length=200, description="会话标题")
    description: Optional[str] = Field(None, max_length=1000, description="会话描述")


class Session(SessionBase):
    """会话响应模型"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    
    class Config:
        from_attributes = True


# 会话消息相关模型
class MessageBase(BaseModel):
    """消息基础模型"""
    content: str = Field(..., description="消息内容")
    message_type: str = Field(..., description="消息类型：user, assistant, system")


class MessageCreate(MessageBase):
    """创建消息请求模型"""
    session_id: int = Field(..., description="会话ID")


class Message(MessageBase):
    """消息响应模型"""
    id: int
    session_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
