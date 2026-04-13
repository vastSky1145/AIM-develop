"""
配置文件
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Settings:
    """应用配置"""
    
    # FastAPI配置
    APP_NAME = "AI论文辅助系统"
    VERSION = "1.0.0"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    # JWT配置
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRE_DAYS = 7
    
    # MongoDB配置
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
    MONGODB_DB = os.getenv("MONGODB_DB", "research_papers")
    
    # 向量数据库配置
    CHROMA_PERSIST_DIR = "./chroma_db"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    
    # 文档处理配置
    DOC2X_API_KEY = os.getenv("DOC2X_API_KEY", "sk-bzllfk7oftj7tv4he6rc7bfdz92iqtn0")
    OUTPUT_DIR = "./Output"
    
    # LLM配置
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # CORS配置
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    # 文件上传配置
    MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {".pdf", ".ppt", ".pptx"}

    # 速率限制配置（以包为粒度）
    # max_requests: 时间窗口内允许的最大请求次数
    # window_seconds: 滑动时间窗口大小（秒）
    RATE_LIMITS: dict[str, dict[str, int]] = {
        "ai_assistant": {"max_requests": 20,  "window_seconds": 3600},   # AI生成/修改：每小时 20 次
        "knowledge":    {"max_requests": 30,  "window_seconds": 3600},   # 知识库操作：每小时 30 次
        "papers":       {"max_requests": 50,  "window_seconds": 3600},   # 论文管理：每小时 50 次
        "auth":         {"max_requests": 10,  "window_seconds": 900},    # 登录/认证：每 15 分钟 10 次
        "prompts":      {"max_requests": 100, "window_seconds": 3600},   # Prompt模板：每小时 100 次
        "user_prompts": {"max_requests": 100, "window_seconds": 3600},   # 用户Prompt：每小时 100 次
    }

settings = Settings()

