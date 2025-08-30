# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List, Optional, Union
from pathlib import Path
import os, json

class Settings(BaseSettings):
    # ✅ pydantic v2 推荐：用 model_config 而不是 class Config
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",   # 环境里多余变量忽略掉，避免报错
    )

    # ========= 基础配置 =========
    APP_NAME: str = "AlgoKG智能问答系统"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # 项目根目录（容器里通常是 /app）
    BASE_DIR: str = Field(default_factory=lambda: os.getenv("BASE_DIR") or str(Path(__file__).resolve().parents[2]))

    # ========= CORS =========
    # 支持字符串（JSON 或 逗号分隔）/ 列表两种形式的环境变量
    CORS_ORIGINS: Union[List[str], str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000", "http://frontend:3000"]
    )

    # ========= 外部服务 =========
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "123456"
    REDIS_URL: str = "redis://localhost:6379"

    # ========= 模型/数据 路径 =========
    EMBEDDING_PATH: str = ""     # 运行时在 post_init 里填充
    ENTITY2ID_PATH: str = ""
    ID2TITLE_PATH: str = ""
    TAG_LABEL_PATH: str = ""

    # ========= LLM =========
    QWEN_API_KEY: Optional[str] = None
    DASHSCOPE_API_KEY: Optional[str] = None
    QWEN_MODEL: str = "qwen-turbo"

    # ========= 其他 =========
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS: int = 100
    CACHE_TTL: int = 3600
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # ---- 统一解析 CORS 环境变量（支持 JSON/逗号分隔）----
    @staticmethod
    def _parse_cors(value: Union[List[str], str, None]) -> List[str]:
        if not value:
            return []
        if isinstance(value, list):
            return value
        # 字符串：优先当 JSON 解析，否则按逗号切
        s = value.strip()
        if s.startswith("'") and s.endswith("'"):
            s = s[1:-1]  # 兼容 docker -e '["..."]' 这种外层引号
        try:
            return [x.strip() for x in json.loads(s)]
        except json.JSONDecodeError:
            return [x.strip() for x in s.split(",") if x.strip()]

    def model_post_init(self, __context) -> None:
        # CORS 归一化为列表
        cors = os.getenv("CORS_ORIGINS", self.CORS_ORIGINS)
        object.__setattr__(self, "CORS_ORIGINS", self._parse_cors(cors))

        # 计算数据/模型路径
        base = Path(self.BASE_DIR)
        object.__setattr__(self, "EMBEDDING_PATH", str(base / "models" / "ensemble_gnn_embedding.pt"))
        object.__setattr__(self, "ENTITY2ID_PATH", str(base / "data" / "raw" / "entity2id.json"))
        object.__setattr__(self, "ID2TITLE_PATH", str(base / "data" / "raw" / "entity_id_to_title.json"))
        object.__setattr__(self, "TAG_LABEL_PATH", str(base / "data" / "raw" / "problem_id_to_tags.json"))

    @property
    def cors_origins_list(self) -> List[str]:
        return self._parse_cors(self.CORS_ORIGINS)

# 单例
settings = Settings()

def get_settings() -> Settings:
    return settings

# 可选：启动时验证关键文件是否存在（仅打印警告，不报错）
def validate_paths() -> bool:
    paths = [
        settings.EMBEDDING_PATH,
        settings.ENTITY2ID_PATH,
        settings.ID2TITLE_PATH,
        settings.TAG_LABEL_PATH,
    ]
    missing = [p for p in paths if not Path(p).exists()]
    if missing:
        print(f"警告: 以下文件路径不存在: {missing}")
        print("如需真实推荐/问答功能，请将模型和数据文件放到容器对应目录或用 -v 映射进来")
    return not missing

validate_paths()
