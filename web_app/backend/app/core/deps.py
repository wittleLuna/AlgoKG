from typing import Generator, Optional
import redis
from neo4j import GraphDatabase
import sys
import os
from pathlib import Path
from fastapi import Depends

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent.parent  # 指向 algokg_platform
sys.path.append(str(project_root))
print(f"添加到Python路径: {project_root}")

from app.core.config import settings

# 强制使用真实的推荐系统
try:
    # 首先尝试导入真实的推荐系统
    from qa.embedding_qa import EnhancedRecommendationSystem
    print("✅ 成功导入真实推荐系统")
    RECOMMENDATION_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  无法导入真实推荐系统: {e}")
    from app.core.mock_qa import MockEnhancedRecommendationSystem as EnhancedRecommendationSystem
    RECOMMENDATION_SYSTEM_AVAILABLE = False

# 导入新的增强推荐系统
try:
    from app.services.enhanced_recommendation_service import EnhancedRecommendationSystem
    ENHANCED_RECOMMENDATION_AVAILABLE = True
    print("✅ 成功导入增强推荐系统")
except ImportError as e:
    print(f"⚠️  无法导入增强推荐系统: {e}")
    ENHANCED_RECOMMENDATION_AVAILABLE = False

# 尝试导入其他模块，失败时使用模拟模块
try:
    from qa.multi_agent_qa import GraphEnhancedMultiAgentSystem
    from backend.neo4j_loader.neo4j_api import Neo4jKnowledgeGraphAPI
    from extractors.extract_knowledgePoint import QwenClientNative as QwenClient
    ORIGINAL_MODULES_AVAILABLE = True
    print("✅ 成功导入原始问答系统模块")
except ImportError as e:
    print(f"⚠️  无法导入原始模块: {e}")
    print("🔄 将使用模拟模块进行开发和测试")
    from app.core.mock_qa import (
        MockGraphEnhancedMultiAgentSystem as GraphEnhancedMultiAgentSystem,
        MockNeo4jKnowledgeGraphAPI as Neo4jKnowledgeGraphAPI,
        MockQwenClient as QwenClient
    )
    ORIGINAL_MODULES_AVAILABLE = False

# 全局实例
_redis_client: Optional[redis.Redis] = None
_neo4j_driver = None
_qa_system: Optional[GraphEnhancedMultiAgentSystem] = None
_recommendation_system: Optional[EnhancedRecommendationSystem] = None
_enhanced_recommendation_system: Optional[EnhancedRecommendationSystem] = None

def get_redis() -> redis.Redis:
    """获取Redis客户端"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client

def get_neo4j_driver():
    """获取Neo4j驱动"""
    global _neo4j_driver
    if _neo4j_driver is None:
        _neo4j_driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
    return _neo4j_driver

def get_neo4j_api() -> Neo4jKnowledgeGraphAPI:
    """获取Neo4j API实例"""
    try:
        if not ORIGINAL_MODULES_AVAILABLE:
            # 使用模拟Neo4j API
            print("🔄 使用模拟Neo4j API")
            return Neo4jKnowledgeGraphAPI("", "", "")
        else:
            # 使用真实Neo4j API
            return Neo4jKnowledgeGraphAPI(
                uri=settings.NEO4J_URI,
                user=settings.NEO4J_USER,
                password=settings.NEO4J_PASSWORD
            )
    except Exception as e:
        print(f"⚠️  连接Neo4j失败: {e}")
        print("🔄 使用模拟Neo4j API")
        return Neo4jKnowledgeGraphAPI("", "", "")

def get_recommendation_system() -> EnhancedRecommendationSystem:
    """获取推荐系统实例"""
    global _recommendation_system
    if _recommendation_system is None:
        try:
            if RECOMMENDATION_SYSTEM_AVAILABLE:
                # 使用真实推荐系统，配置真实数据路径（相对于项目根目录）
                import os
                # 获取项目根目录（从backend目录向上两级）
                backend_dir = Path(__file__).parent.parent.parent  # 到web_app/backend
                project_root = backend_dir.parent.parent  # 到项目根目录

                config = {
                    "embedding_path": str(project_root / "models" / "ensemble_gnn_embedding.pt"),
                    "entity2id_path": str(project_root / "data" / "raw" / "entity2id.json"),
                    "id2title_path": str(project_root / "data" / "raw" / "entity_id_to_title.json"),
                    "tag_label_path": str(project_root / "data" / "raw" / "problem_id_to_tags.json")
                }

                # 检查文件是否存在
                missing_files = []
                for key, path in config.items():
                    if not os.path.exists(path):
                        missing_files.append(f"{key}: {path}")

                if missing_files:
                    print(f"⚠️  缺少数据文件: {missing_files}")
                    raise FileNotFoundError(f"缺少必要的数据文件: {missing_files}")

                print(f"🚀 使用真实推荐系统，配置: {config}")
                _recommendation_system = EnhancedRecommendationSystem(**config)
                print("✅ 真实推荐系统初始化成功")
            else:
                # 使用模拟推荐系统
                print("🔄 使用模拟推荐系统")
                _recommendation_system = EnhancedRecommendationSystem()
        except Exception as e:
            print(f"⚠️  初始化真实推荐系统失败: {e}")
            print("🔄 回退到模拟推荐系统")
            from app.core.mock_qa import MockEnhancedRecommendationSystem
            _recommendation_system = MockEnhancedRecommendationSystem()
    return _recommendation_system

def get_enhanced_recommendation_system() -> Optional[EnhancedRecommendationSystem]:
    """获取增强推荐系统实例"""
    global _enhanced_recommendation_system
    if _enhanced_recommendation_system is None:
        try:
            if ENHANCED_RECOMMENDATION_AVAILABLE:
                # 使用增强推荐系统，配置真实数据路径
                import os
                backend_dir = Path(__file__).parent.parent.parent  # 到web_app/backend
                project_root = backend_dir.parent.parent  # 到项目根目录

                config = {
                    "embedding_path": str(project_root / "models" / "ensemble_gnn_embedding.pt"),
                    "entity2id_path": str(project_root / "data" / "raw" / "entity2id.json"),
                    "id2title_path": str(project_root / "data" / "raw" / "entity_id_to_title.json"),
                    "tag_label_path": str(project_root / "data" / "raw" / "problem_id_to_tags.json")
                }

                # 检查文件是否存在
                missing_files = []
                for key, path in config.items():
                    if not os.path.exists(path):
                        missing_files.append(f"{key}: {path}")

                if missing_files:
                    print(f"⚠️  增强推荐系统缺少数据文件: {missing_files}")
                    return None

                print(f"🚀 使用增强推荐系统，配置: {config}")
                _enhanced_recommendation_system = EnhancedRecommendationSystem(**config)
                print("✅ 增强推荐系统初始化成功")
            else:
                print("⚠️  增强推荐系统不可用")
                return None
        except Exception as e:
            print(f"⚠️  初始化增强推荐系统失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    return _enhanced_recommendation_system

def get_qa_system() -> GraphEnhancedMultiAgentSystem:
    """获取问答系统实例"""
    global _qa_system
    if _qa_system is None:
        try:
            if not ORIGINAL_MODULES_AVAILABLE:
                # 使用模拟模块
                print("🔄 使用模拟问答系统")
                _qa_system = GraphEnhancedMultiAgentSystem()
            else:
                # 使用原始模块
                rec_system = get_recommendation_system()
                neo4j_api = get_neo4j_api()

                if rec_system is None:
                    print("⚠️  推荐系统初始化失败，使用模拟模式")
                    _qa_system = GraphEnhancedMultiAgentSystem()
                else:
                    # 只有在有API密钥时才创建真实的客户端
                    qwen_client = None
                    api_key = settings.DASHSCOPE_API_KEY or settings.QWEN_API_KEY
                    if api_key and api_key.strip():
                        try:
                            qwen_client = QwenClient(api_key=api_key)
                        except Exception as e:
                            print(f"⚠️  Qwen客户端初始化失败: {e}")
                            qwen_client = None

                    _qa_system = GraphEnhancedMultiAgentSystem(
                        rec_system=rec_system,
                        neo4j_api=neo4j_api,
                        entity_id_to_title_path=settings.ID2TITLE_PATH,
                        qwen_client=qwen_client
                    )
        except Exception as e:
            print(f"⚠️  初始化问答系统失败: {e}")
            print("🔄 回退到模拟模式")
            # 强制使用模拟模块
            from app.core.mock_qa import MockGraphEnhancedMultiAgentSystem
            _qa_system = MockGraphEnhancedMultiAgentSystem()
    return _qa_system

def get_qwen_client() -> Optional[QwenClient]:
    """获取Qwen客户端"""
    if settings.QWEN_API_KEY:
        return QwenClient()
    return None

# 依赖注入函数
async def get_current_qa_system():
    """依赖注入：获取当前问答系统"""
    qa_system = get_qa_system()
    if qa_system is None:
        print("⚠️  问答系统未正确初始化，创建模拟系统")
        from app.core.mock_qa import MockGraphEnhancedMultiAgentSystem
        qa_system = MockGraphEnhancedMultiAgentSystem()
    return qa_system

async def get_current_redis():
    """依赖注入：获取当前Redis客户端"""
    return get_redis()

async def get_current_neo4j_api():
    """依赖注入：获取当前Neo4j API"""
    return get_neo4j_api()

# 清理函数
def cleanup_resources():
    """清理资源"""
    global _redis_client, _neo4j_driver, _qa_system, _recommendation_system, _enhanced_recommendation_system

    if _redis_client:
        _redis_client.close()
        _redis_client = None

    if _neo4j_driver:
        _neo4j_driver.close()
        _neo4j_driver = None

    # 其他资源清理
    _qa_system = None
    _recommendation_system = None
    _enhanced_recommendation_system = None

# 健康检查函数
async def check_services_health() -> dict:
    """检查各服务健康状态"""
    health_status = {}
    
    # 检查Redis
    try:
        redis_client = get_redis()
        redis_client.ping()
        health_status["redis"] = "healthy"
    except Exception as e:
        health_status["redis"] = f"unhealthy: {str(e)}"
    
    # 检查Neo4j
    try:
        neo4j_api = get_neo4j_api()
        if ORIGINAL_MODULES_AVAILABLE and hasattr(neo4j_api, 'driver') and neo4j_api.driver:
            # 真实Neo4j连接测试
            with neo4j_api.driver.session() as session:
                session.run("RETURN 1")
            health_status["neo4j"] = "healthy"
        else:
            # 模拟模式
            health_status["neo4j"] = "healthy (mock mode)"
    except Exception as e:
        health_status["neo4j"] = f"unhealthy: {str(e)}"

    # 检查问答系统
    try:
        qa_system = get_qa_system()
        if qa_system is not None:
            if ORIGINAL_MODULES_AVAILABLE:
                health_status["qa_system"] = "healthy"
            else:
                health_status["qa_system"] = "healthy (mock mode)"
        else:
            health_status["qa_system"] = "unhealthy: not initialized"
    except Exception as e:
        health_status["qa_system"] = f"unhealthy: {str(e)}"
    
    return health_status


# 用户认证相关依赖注入
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from app.core.auth import security, verify_token, get_token_from_credentials
from app.services.user_service import UserService
from app.models.user import User

# 用户服务实例
_user_service: Optional[UserService] = None

def get_user_service() -> UserService:
    """获取用户服务实例"""
    global _user_service
    if _user_service is None:
        _user_service = UserService()
    return _user_service


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """获取当前用户"""
    try:
        # 提取令牌
        token = get_token_from_credentials(credentials)

        # 验证令牌
        token_data = verify_token(token)
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 获取用户信息
        user_service = get_user_service()
        user = user_service.get_user_by_id(token_data.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 转换为公开用户信息
        user_dict = user.dict()
        del user_dict['hashed_password']
        return User(**user_dict)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if current_user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用"
        )
    return current_user


async def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """获取当前管理员用户"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def get_current_moderator_user(current_user: User = Depends(get_current_active_user)) -> User:
    """获取当前审核员用户"""
    if current_user.role not in ["admin", "moderator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要审核员权限"
        )
    return current_user


def get_optional_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
    """获取可选的当前用户（用于可选认证的接口）"""
    if credentials is None:
        return None

    try:
        # 提取令牌
        token = get_token_from_credentials(credentials)

        # 验证令牌
        token_data = verify_token(token)
        if token_data is None:
            return None

        # 获取用户信息
        user_service = get_user_service()
        user = user_service.get_user_by_id(token_data.user_id)
        if user is None:
            return None

        # 转换为公开用户信息
        user_dict = user.dict()
        del user_dict['hashed_password']
        return User(**user_dict)

    except Exception:
        return None
