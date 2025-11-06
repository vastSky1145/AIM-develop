"""
FastAPI主应用入口
"""
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import uvicorn
from datetime import datetime, timedelta
import jwt

# 导入路由
from routers import auth, papers, ai_assistant, knowledge, prompts

# 设置环境变量（避免TensorFlow警告）
os.environ["TRANSFORMERS_NO_TF"] = "1"

# 创建FastAPI应用
app = FastAPI(
    title="AI论文辅助系统API",
    description="基于FastAPI的AI论文写作辅助系统后端接口",
    version="1.0.0"
)

# CORS配置 - 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该配置具体的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(papers.router, prefix="/api/papers", tags=["论文管理"])
app.include_router(ai_assistant.router, prefix="/api/ai", tags=["AI辅助"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["知识库"])
app.include_router(prompts.router, prefix="/api/prompts", tags=["Prompt模板"])

# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": f"服务器内部错误: {str(exc)}",
            "data": None
        }
    )

# 根路径
@app.get("/")
async def root():
    return {
        "message": "AI论文辅助系统API",
        "status": "运行中"
    }

# 健康检查
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # 开发环境运行
    uvicorn.run(
        "app:app",
        # app,
        host="0.0.0.0",
        port=8000,
        reload=True  # 开发模式下自动重载
    )

