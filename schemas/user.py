"""
用户相关数据模型
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, description="密码")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "sxs",
                "password": "123456"
            }
        }

class UserRegister(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, description="密码")
    email: Optional[EmailStr] = Field(None, description="邮箱（可选）")

class UserInfo(BaseModel):
    """用户信息"""
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: Optional[str] = Field(None, description="邮箱")

class LoginResponse(BaseModel):
    """登录响应"""
    token: str = Field(..., description="JWT令牌")
    user_info: UserInfo = Field(..., description="用户信息")
    expires_in: int = Field(..., description="令牌有效期（秒）")

class ChangePassword(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., min_length=6, description="旧密码")
    new_password: str = Field(..., min_length=6, description="新密码")
    
    class Config:
        json_schema_extra = {
            "example": {
                "old_password": "123456",
                "new_password": "654321"
            }
        }

