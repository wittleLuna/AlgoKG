# ===== 基础镜像 =====
FROM python:3.10-slim

# ===== 基础环境 =====
ENV PYTHONUNBUFFERED=1 \
    # 统一项目根目录，和你的 config.py 的 BASE_DIR 取值一致
    BASE_DIR=/app \
    # 扩展 Python 搜索路径，确保能 import backend/ 与 extractors/ 的模块
    PYTHONPATH=/app:/app/backend:/app/extractors:/app/qa \
    # 默认 CORS（可在 docker run 覆盖）
    CORS_ORIGINS='["http://146.56.243.91:3000","http://localhost:3000","http://127.0.0.1:3000"]' \
    # 默认外部服务（可在 docker run 覆盖）
    NEO4J_URI="bolt://1.117.77.19:7687" \
    NEO4J_USER="neo4j" \
    NEO4J_PASSWORD="Abcd1234!" \
    REDIS_URL="redis://1.117.77.19:6379" \
    # LLM 相关（如用本地 qwen，可不设）
    QWEN_API_KEY="" \
    DASHSCOPE_API_KEY="" \
    QWEN_MODEL="qwen3:8b" \
    OLLAMA_HOST=http://localhost:11434 \
    # 打开 FastAPI reload 日志级别等（生产可关）
    DEBUG="true"

# ===== 系统依赖（清华源）=====
RUN rm -rf /etc/apt/sources.list.d/* && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ trixie main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ trixie-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security trixie-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends \
        gcc g++ curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# ===== pip 清华源 =====
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# ===== 工作目录 =====
WORKDIR /app

# ===== 先装依赖（利用缓存）=====
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && rm -rf ~/.cache/pip

# ===== 拷贝代码 =====
# 你的 FastAPI 主应用在 web_app/backend/app/
COPY web_app/backend/app/ ./app/
# 其余模块（问答/抽取/后端工具/模型/数据/gnn等）
COPY qa/ ./qa/
COPY extractors/ ./extractors/
COPY backend/ ./backend/
# 如果要把模型、数据打进镜像，取消下面两行注释；否则建议用 -v 映射
COPY models/ ./models/
COPY data/ ./data/
# 如果没有 node_modules，可以去掉这行
COPY node_modules/ ./node_modules/

# ===== 预建必须目录（不写占位文件，避免误判“模型已就绪”）=====
RUN mkdir -p /app/models /app/data/raw /app/backend /app/qa /app/extractors

# ===== 端口 & 健康检查 =====
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1
    
# ===== 固定软链接，确保 config.py 里的路径能找到 =====
RUN ln -sf /app/models /models && \
    mkdir -p /app/data/raw && ln -sf /app/data /data

# ===== 启动 =====
# 直接从 app.main:app 启动；你的 config.py 会在导入时打印路径检查信息
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
