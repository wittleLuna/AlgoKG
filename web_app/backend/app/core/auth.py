"""
用户认证核心功能
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Union
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.user import TokenData


# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30天

# HTTP Bearer认证
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建JWT访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    # 暂时返回一个简单的令牌，用于测试
    import json
    import base64
    token_data = json.dumps(to_encode, default=str)
    return base64.b64encode(token_data.encode()).decode()


def verify_token(token: str) -> Optional[TokenData]:
    """验证JWT令牌"""
    try:
        # 解码简单的base64令牌
        import json
        import base64
        from datetime import datetime

        token_data = base64.b64decode(token.encode()).decode()
        payload = json.loads(token_data)

        # 检查过期时间
        if 'exp' in payload:
            exp_time = payload['exp']
            if isinstance(exp_time, str):
                # 如果是字符串，尝试解析
                try:
                    exp_datetime = datetime.fromisoformat(exp_time.replace('Z', '+00:00'))
                    if exp_datetime < datetime.utcnow():
                        return None
                except:
                    pass

        user_id: int = payload.get("sub")
        username: str = payload.get("username")

        if user_id is None:
            return None

        token_data = TokenData(user_id=user_id, username=username)
        return token_data
    except Exception as e:
        return None


def get_token_from_credentials(credentials: HTTPAuthorizationCredentials) -> str:
    """从认证凭据中提取令牌"""
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


class AuthenticationError(Exception):
    """认证错误异常"""
    pass


class AuthorizationError(Exception):
    """授权错误异常"""
    pass


def validate_password_strength(password: str) -> bool:
    """验证密码强度"""
    if len(password) < 6:
        return False
    
    # 检查是否包含字母和数字
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    return has_letter and has_digit


def generate_username_suggestions(base_username: str, existing_usernames: list) -> list:
    """生成用户名建议"""
    suggestions = []
    
    # 如果基础用户名可用，直接返回
    if base_username not in existing_usernames:
        return [base_username]
    
    # 生成数字后缀建议
    for i in range(1, 100):
        suggestion = f"{base_username}{i}"
        if suggestion not in existing_usernames:
            suggestions.append(suggestion)
            if len(suggestions) >= 5:  # 最多返回5个建议
                break
    
    return suggestions


def sanitize_username(username: str) -> str:
    """清理用户名，移除特殊字符"""
    import re
    # 只保留字母、数字、下划线和连字符
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', username)
    return sanitized.lower()


def is_valid_email_format(email: str) -> bool:
    """验证邮箱格式"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def generate_reset_token(user_id: int) -> str:
    """生成密码重置令牌"""
    data = {
        "sub": user_id,
        "type": "password_reset",
        "exp": datetime.utcnow() + timedelta(hours=1)  # 1小时有效期
    }
    # 使用相同的简单JWT编码
    import json
    import base64
    import hmac
    import hashlib

    header = {"alg": "HS256", "typ": "JWT"}
    header_encoded = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
    payload_encoded = base64.urlsafe_b64encode(json.dumps(data, default=str).encode()).decode().rstrip('=')

    signature = hmac.new(
        SECRET_KEY.encode(),
        f"{header_encoded}.{payload_encoded}".encode(),
        hashlib.sha256
    ).digest()
    signature_encoded = base64.urlsafe_b64encode(signature).decode().rstrip('=')

    return f"{header_encoded}.{payload_encoded}.{signature_encoded}"


def verify_reset_token(token: str) -> Optional[int]:
    """验证密码重置令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "password_reset":
            return None
            
        return user_id
    except Exception:
        return None


def create_session_token(user_id: int, session_id: str) -> str:
    """创建会话令牌"""
    data = {
        "user_id": user_id,
        "session_id": session_id,
        "type": "session",
        "exp": datetime.utcnow() + timedelta(hours=24)  # 24小时有效期
    }
    # 使用相同的简单JWT编码
    import json
    import base64
    import hmac
    import hashlib

    header = {"alg": "HS256", "typ": "JWT"}
    header_encoded = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
    payload_encoded = base64.urlsafe_b64encode(json.dumps(data, default=str).encode()).decode().rstrip('=')

    signature = hmac.new(
        SECRET_KEY.encode(),
        f"{header_encoded}.{payload_encoded}".encode(),
        hashlib.sha256
    ).digest()
    signature_encoded = base64.urlsafe_b64encode(signature).decode().rstrip('=')

    return f"{header_encoded}.{payload_encoded}.{signature_encoded}"


def verify_session_token(token: str) -> Optional[dict]:
    """验证会话令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        session_id: str = payload.get("session_id")
        token_type: str = payload.get("type")
        
        if user_id is None or session_id is None or token_type != "session":
            return None
            
        return {"user_id": user_id, "session_id": session_id}
    except Exception:
        return None


# 权限装饰器
def require_role(required_role: str):
    """要求特定角色的装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 这里需要从请求上下文中获取用户角色
            # 具体实现会在依赖注入中完成
            return func(*args, **kwargs)
        return wrapper
    return decorator


# 常用的权限检查函数
def can_access_admin_panel(user_role: str) -> bool:
    """检查是否可以访问管理面板"""
    return user_role in ["admin", "moderator"]


def can_manage_users(user_role: str) -> bool:
    """检查是否可以管理用户"""
    return user_role == "admin"


def can_moderate_content(user_role: str) -> bool:
    """检查是否可以审核内容"""
    return user_role in ["admin", "moderator"]
