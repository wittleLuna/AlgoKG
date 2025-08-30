"""
用户认证相关的API路由
"""
from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from app.models.user import (
    User, UserCreate, UserLogin, Token, UserUpdate, UserProfile,
    Favorite, FavoriteCreate, SearchHistory, SearchHistoryCreate,
    Session, SessionCreate, SessionUpdate, Message, MessageCreate
)
from app.core.auth import (
    create_access_token, verify_token, get_token_from_credentials, 
    security, ACCESS_TOKEN_EXPIRE_MINUTES, validate_password_strength
)
from app.services.user_service import UserService
from app.core.deps import get_current_user, get_current_active_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["认证"])
user_service = UserService()


from fastapi import Request
from pydantic import ValidationError

@router.post("/test-login", response_model=Token, summary="测试登录")
async def test_login():
    """
    测试登录端点，返回测试令牌
    用于开发和测试目的
    """
    try:
        # 创建测试用户数据
        test_user_data = {
            "sub": "user_123",
            "username": "test_user",
            "email": "test@example.com",
            "full_name": "Test User",
            "is_admin": False
        }

        # 创建访问令牌
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data=test_user_data,
            expires_delta=access_token_expires
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserProfile(
                id="user_123",
                username="test_user",
                email="test@example.com",
                full_name="Test User",
                is_admin=False,
                created_at="2024-01-01T00:00:00",
                last_login="2024-01-01T00:00:00"
            )
        )

    except Exception as e:
        logger.error(f"测试登录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="测试登录失败"
        )

@router.post("/register", response_model=Token, summary="用户注册")
async def register(request: Request):
    """
    用户注册

    - **username**: 用户名（3-50字符）
    - **email**: 邮箱地址
    - **password**: 密码（至少6字符）
    - **full_name**: 真实姓名（可选）
    - **avatar_url**: 头像URL（可选）
    - **bio**: 个人简介（可选）
    """
    try:
        # 获取原始请求数据
        raw_data = await request.json()
        logger.info(f"收到注册请求原始数据: {raw_data}")

        # 手动验证和创建UserCreate对象
        try:
            user_data = UserCreate(**raw_data)
            logger.info(f"成功解析用户数据: {user_data.username}, {user_data.email}")
        except ValidationError as e:
            logger.error(f"数据验证失败: {e}")
            # 提取第一个错误信息
            error_msg = "数据验证失败"
            if e.errors():
                first_error = e.errors()[0]
                field = first_error.get('loc', ['unknown'])[-1]
                msg = first_error.get('msg', '验证失败')

                # 自定义错误消息
                if 'string_too_short' in first_error.get('type', ''):
                    if field == 'username':
                        error_msg = "用户名至少需要3个字符"
                    elif field == 'password':
                        error_msg = "密码至少需要6个字符"
                elif 'string_too_long' in first_error.get('type', ''):
                    if field == 'username':
                        error_msg = "用户名最多50个字符"
                else:
                    error_msg = f"{field}: {msg}"

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_msg
            )
        except Exception as e:
            logger.error(f"解析数据失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"解析数据失败: {e}"
            )
        # 验证密码强度
        if not validate_password_strength(user_data.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码强度不足，至少需要6个字符且包含字母和数字"
            )

        # 创建用户
        user = user_service.create_user(user_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户创建失败"
            )

        # 生成访问令牌
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.id, "username": user.username},
            expires_delta=access_token_expires
        )

        # 转换为公开用户信息
        user_dict = user.dict()
        del user_dict['hashed_password']
        user_public = User(**user_dict)

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_public
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except ValueError as e:
        logger.error(f"用户注册失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"用户注册失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )
    except Exception as e:
        logger.error(f"用户注册失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )


@router.post("/login", response_model=Token, summary="用户登录")
async def login(login_data: UserLogin):
    """
    用户登录
    
    - **username**: 用户名或邮箱
    - **password**: 密码
    """
    try:
        # 验证用户
        user = user_service.authenticate_user(login_data.username, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 检查用户状态
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户已被禁用，请联系管理员"
            )
        
        # 生成访问令牌
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.id, "username": user.username},
            expires_delta=access_token_expires
        )
        
        # 转换为公开用户信息
        user_dict = user.dict()
        del user_dict['hashed_password']
        user_public = User(**user_dict)
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_public
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户登录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )


@router.get("/me", response_model=UserProfile, summary="获取当前用户信息")
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """获取当前登录用户的详细信息"""
    try:
        profile = user_service.get_user_profile(current_user.id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户信息不存在"
            )
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )


@router.put("/me", response_model=User, summary="更新当前用户信息")
async def update_current_user_info(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """更新当前登录用户的信息"""
    try:
        updated_user = user_service.update_user(current_user.id, user_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="更新用户信息失败"
            )
        
        # 转换为公开用户信息
        user_dict = updated_user.dict()
        del user_dict['hashed_password']
        return User(**user_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户信息失败"
        )


@router.post("/verify-token", response_model=User, summary="验证令牌")
async def verify_user_token(current_user: User = Depends(get_current_active_user)):
    """验证JWT令牌是否有效"""
    return current_user


@router.post("/logout", summary="用户登出")
async def logout(current_user: User = Depends(get_current_active_user)):
    """
    用户登出
    注意：由于使用JWT，实际的登出需要在前端清除令牌
    """
    return {"message": "登出成功"}


# 收藏相关路由
@router.post("/favorites", response_model=Favorite, summary="添加收藏")
async def add_favorite(
    favorite_data: FavoriteCreate,
    current_user: User = Depends(get_current_active_user)
):
    """添加收藏项"""
    try:
        favorite = user_service.add_favorite(current_user.id, favorite_data)
        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="添加收藏失败"
            )
        return favorite
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加收藏失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="添加收藏失败"
        )


@router.get("/favorites", response_model=list[Favorite], summary="获取收藏列表")
async def get_favorites(
    item_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user)
):
    """获取用户收藏列表"""
    try:
        favorites = user_service.get_user_favorites(
            current_user.id, item_type, limit, offset
        )
        return favorites
        
    except Exception as e:
        logger.error(f"获取收藏列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取收藏列表失败"
        )


@router.delete("/favorites/{item_type}/{item_id}", summary="移除收藏")
async def remove_favorite(
    item_type: str,
    item_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """移除收藏项"""
    try:
        success = user_service.remove_favorite(current_user.id, item_type, item_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="收藏项不存在"
            )
        return {"message": "移除收藏成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"移除收藏失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="移除收藏失败"
        )


# 搜索历史相关路由
@router.post("/search-history", response_model=SearchHistory, summary="添加搜索历史")
async def add_search_history(
    search_data: SearchHistoryCreate,
    current_user: User = Depends(get_current_active_user)
):
    """添加搜索历史"""
    try:
        history = user_service.add_search_history(current_user.id, search_data)
        if not history:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="添加搜索历史失败"
            )
        return history

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加搜索历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="添加搜索历史失败"
        )


@router.get("/search-history", response_model=list[SearchHistory], summary="获取搜索历史")
async def get_search_history(
    search_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user)
):
    """获取用户搜索历史"""
    try:
        history = user_service.get_user_search_history(
            current_user.id, search_type, limit, offset
        )
        return history

    except Exception as e:
        logger.error(f"获取搜索历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取搜索历史失败"
        )


@router.delete("/search-history", summary="清空搜索历史")
async def clear_search_history(
    search_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """清空搜索历史"""
    try:
        success = user_service.clear_search_history(current_user.id, search_type)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="清空搜索历史失败"
            )
        return {"message": "搜索历史已清空"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清空搜索历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="清空搜索历史失败"
        )


# 会话管理相关路由
@router.post("/sessions", response_model=Session, summary="创建新会话")
async def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_active_user)
):
    """创建新会话"""
    try:
        session = user_service.create_session(current_user.id, session_data)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="创建会话失败"
            )
        return session

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建会话失败"
        )


@router.get("/sessions", response_model=list[Session], summary="获取用户会话列表")
async def get_user_sessions(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user)
):
    """获取用户会话列表"""
    try:
        sessions = user_service.get_user_sessions(current_user.id, limit, offset)
        return sessions

    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取会话列表失败"
        )


@router.get("/sessions/{session_id}", response_model=Session, summary="获取会话详情")
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """获取会话详情"""
    try:
        session = user_service.get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )

        # 检查权限
        if session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此会话"
            )

        return session

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取会话详情失败"
        )


@router.put("/sessions/{session_id}", response_model=Session, summary="更新会话信息")
async def update_session(
    session_id: int,
    session_data: SessionUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """更新会话信息"""
    try:
        # 检查会话是否存在且属于当前用户
        session = user_service.get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )

        if session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权修改此会话"
            )

        updated_session = user_service.update_session(session_id, session_data)
        if not updated_session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="更新会话失败"
            )

        return updated_session

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新会话失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新会话失败"
        )


@router.delete("/sessions/{session_id}", summary="删除会话")
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """删除会话"""
    try:
        # 检查会话是否存在且属于当前用户
        session = user_service.get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )

        if session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此会话"
            )

        success = user_service.delete_session(session_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="删除会话失败"
            )

        return {"message": "会话已删除"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除会话失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除会话失败"
        )
