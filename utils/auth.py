"""
认证相关工具函数
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
import os

# JWT配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌
    
    Args:
        data: 要编码的数据字典
        expires_delta: 过期时间增量
    
    Returns:
        JWT令牌字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        # expire = datetime.utcnow() + expires_delta
        expire = datetime.now() + expires_delta
    else:
        # expire = datetime.utcnow() + timedelta(days=7)
        expire = datetime.now() + timedelta(days=7)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict]:
    """
    验证JWT令牌
    
    Args:
        token: JWT令牌字符串
    
    Returns:
        解码后的payload，如果验证失败则返回None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # Token已过期
        return None
    except jwt.JWTError:
        # Token无效
        return None

