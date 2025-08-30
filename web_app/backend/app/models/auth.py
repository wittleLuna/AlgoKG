"""
认证相关的数据模型
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    """用户角色枚举"""
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class UserStatus(str, Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

# 基础用户模型
class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: Optional[str] = Field(None, description="邮箱地址")  # 简化版本，不强制要求EmailStr
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    is_active: bool = Field(True, description="是否激活")

class UserCreate(UserBase):
    """创建用户请求模型"""
    password: str = Field(..., min_length=6, max_length=100, description="密码")

class UserUpdate(BaseModel):
    """更新用户请求模型"""
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

class UserChangePassword(BaseModel):
    """修改密码请求模型"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")

class User(UserBase):
    """用户响应模型"""
    id: str = Field(..., description="用户ID")
    is_admin: bool = Field(False, description="是否为管理员")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True

class UserInDB(User):
    """数据库中的用户模型"""
    password_hash: str = Field(..., description="密码哈希")

# 登录相关模型
class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")

class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field("bearer", description="令牌类型")
    user: User = Field(..., description="用户信息")

class TokenData(BaseModel):
    """令牌数据模型"""
    username: Optional[str] = None
    user_id: Optional[str] = None

# 管理员相关模型
class AdminBase(BaseModel):
    """管理员基础模型"""
    username: str = Field(..., min_length=3, max_length=50, description="管理员用户名")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    role: UserRole = Field(UserRole.ADMIN, description="角色")
    permissions: List[str] = Field(default_factory=list, description="权限列表")
    is_active: bool = Field(True, description="是否激活")

class AdminCreate(AdminBase):
    """创建管理员请求模型"""
    password: str = Field(..., min_length=6, max_length=100, description="密码")

class AdminUpdate(BaseModel):
    """更新管理员请求模型"""
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None

class Admin(AdminBase):
    """管理员响应模型"""
    id: str = Field(..., description="管理员ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True

class AdminInDB(Admin):
    """数据库中的管理员模型"""
    password_hash: str = Field(..., description="密码哈希")

# 权限相关模型
class Permission(BaseModel):
    """权限模型"""
    name: str = Field(..., description="权限名称")
    description: str = Field(..., description="权限描述")
    resource: str = Field(..., description="资源")
    action: str = Field(..., description="操作")

# 常用权限定义
class Permissions:
    """权限常量"""
    # 用户管理
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # 笔记管理
    NOTE_READ = "note:read"
    NOTE_CREATE = "note:create"
    NOTE_UPDATE = "note:update"
    NOTE_DELETE = "note:delete"
    NOTE_ADMIN = "note:admin"
    
    # 系统管理
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"
    SYSTEM_BACKUP = "system:backup"
    
    # 管理员权限
    ADMIN_ALL = "admin:all"

# 会话相关模型
class SessionData(BaseModel):
    """会话数据模型"""
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    login_time: datetime = Field(..., description="登录时间")
    last_activity: datetime = Field(..., description="最后活动时间")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")

class Session(BaseModel):
    """会话模型"""
    id: str = Field(..., description="会话ID")
    user_id: str = Field(..., description="用户ID")
    session_data: SessionData = Field(..., description="会话数据")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True

# 响应模型
class MessageResponse(BaseModel):
    """消息响应模型"""
    message: str = Field(..., description="消息内容")
    success: bool = Field(True, description="是否成功")

class UserListResponse(BaseModel):
    """用户列表响应模型"""
    users: List[User] = Field(..., description="用户列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    size: int = Field(..., description="每页大小")

class AdminListResponse(BaseModel):
    """管理员列表响应模型"""
    admins: List[Admin] = Field(..., description="管理员列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    size: int = Field(..., description="每页大小")
