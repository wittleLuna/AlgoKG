from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
import json
import uvicorn
from datetime import datetime

from app.core.config import settings
from app.core.deps import cleanup_resources, check_services_health
from app.api import qa, graph, auth, notes,llm_proxy
from app.models import HealthResponse, ErrorResponse

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# 自定义JSON编码器，处理datetime对象
def json_serializer(obj):
    """JSON序列化器，处理datetime等特殊对象"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时的初始化
    logger.info("正在启动AlgoKG智能问答系统...")
    
    # 检查服务健康状态
    health_status = await check_services_health()
    logger.info(f"服务健康状态: {health_status}")
    
    # 预热系统（可选）
    try:
        # 这里可以添加系统预热逻辑
        logger.info("系统预热完成")
    except Exception as e:
        logger.warning(f"系统预热失败: {e}")
    
    logger.info("AlgoKG智能问答系统启动完成")
    
    yield
    
    # 关闭时的清理
    logger.info("正在关闭AlgoKG智能问答系统...")
    cleanup_resources()
    logger.info("系统关闭完成")

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="""
    AlgoKG智能问答系统 - 基于知识图谱的算法学习助手
    
    ## 主要功能
    
    * **智能问答**: 支持概念解释、题目推荐、相似题目查找等
    * **实时推理**: 流式返回推理过程，展示AI思考路径
    * **交互式内容**: 支持概念和题目的点击跳转
    * **知识图谱**: 动态可视化知识结构和关系
    * **多轮对话**: 支持上下文理解和会话管理
    
    ## 技术特色
    
    * 多智能体协作推理
    * 图神经网络增强推荐
    * 实时流式响应
    * 知识图谱可视化
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 添加中间件
import os
import json
# --- CORS 设置 ---
def get_cors_origins_safe() -> list[str]:
    """
    从 settings 或环境变量读取允许的 Origin 列表；
    未配置时给出包含你公网 IP 的默认值。
    """
    # 1) 优先 settings
    try:
        if hasattr(settings, "CORS_ORIGINS") and settings.CORS_ORIGINS:
            return list(settings.CORS_ORIGINS)
    except Exception:
        pass

    # 2) 退化到环境变量 CORS_ORIGINS（JSON 数组或逗号分隔都支持）
    raw = os.getenv(
        "CORS_ORIGINS",
        '["http://146.56.243.91:3000", "http://localhost:3000", "http://127.0.0.1:3000"]'
    )
    raw = raw.strip().strip("'").strip('"')
    try:
        vals = json.loads(raw)
        if isinstance(vals, list):
            return [str(v).strip() for v in vals if v]
    except Exception:
        # 逗号分隔
        return [v.strip() for v in raw.split(",") if v.strip()]

    return ["http://146.56.243.91:3000"]

cors_origins = get_cors_origins_safe()
print(f"[CORS] allow_origins = {cors_origins}")

# 注意：allow_credentials=True 时不要用 "*" 通配；若要放宽，用 allow_origin_regex。
# 这里既配置 allow_origins（白名单），又加一个正则兜底（允许 localhost/你的IP 任意端口的 http/https）

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,               # 明确白名单
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|146\.56\.243\.91)(:\d+)?$",  # 兜底
    allow_credentials=True,                   # 前端若 withCredentials=true 才能用
    allow_methods=["*"],                      # 允许所有方法
    allow_headers=["*"],                      # 允许所有自定义头
    expose_headers=["*"],                     # 如需在前端读自定义响应头
    max_age=600,                              # 预检缓存 10 分钟
)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # 记录请求信息
    logger.info(f"收到请求: {request.method} {request.url}")
    
    response = await call_next(request)
    
    # 记录响应信息
    process_time = time.time() - start_time
    logger.info(f"请求完成: {request.method} {request.url} - {response.status_code} - {process_time:.3f}s")
    
    # 添加响应头
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"全局异常: {exc}", exc_info=True)

    error_response = ErrorResponse(
        error_code="INTERNAL_SERVER_ERROR",
        error_message="服务器内部错误",
        details={"path": str(request.url), "method": request.method}
    )

    # 使用自定义序列化器
    content = json.loads(json.dumps(error_response.dict(), default=json_serializer))

    return JSONResponse(
        status_code=500,
        content=content
    )

# 注册路由
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}",
    tags=["用户认证"]
)

app.include_router(
    qa.router,
    prefix=f"{settings.API_V1_STR}/qa",
    tags=["问答系统"]
)

app.include_router(
    graph.router,
    prefix=f"{settings.API_V1_STR}/graph",
    tags=["知识图谱"]
)

app.include_router(
    notes.router,
    prefix=f"{settings.API_V1_STR}/notes",
    tags=["笔记管理"]
)

# 健康检查端点
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """系统健康检查"""
    try:
        services_status = await check_services_health()
        
        # 判断整体健康状态
        overall_status = "healthy"
        for service, status in services_status.items():
            if not status.startswith("healthy"):
                overall_status = "degraded"
                break
        
        return HealthResponse(
            status=overall_status,
            version=settings.VERSION,
            services=services_status
        )
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return HealthResponse(
            status="unhealthy",
            version=settings.VERSION,
            services={"error": str(e)}
        )

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用AlgoKG智能问答系统",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/info")
async def app_info():
    """应用信息"""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "debug": settings.DEBUG,
        "api_version": settings.API_V1_STR,
        "features": [
            "智能问答",
            "实时推理路径",
            "交互式内容链接",
            "知识图谱可视化",
            "多轮对话支持"
        ]
    }

# WebSocket支持（用于实时通信）
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    """WebSocket端点，用于实时通信"""
    await websocket.accept()
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            logger.info(f"收到WebSocket消息: {data}")
            
            # 处理消息（这里可以集成实时问答功能）
            response = {"type": "echo", "data": data}
            
            # 发送响应
            await websocket.send_json(response)
            
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
    finally:
        await websocket.close()
        
app.include_router(
    llm_proxy.router,
    prefix=f"{settings.API_V1_STR}/llm",
    tags=["本地LLM代理"]
)

if __name__ == "__main__":
    # 开发环境直接运行
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
