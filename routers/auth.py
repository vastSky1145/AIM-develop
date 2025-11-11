"""
用户认证相关路由
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from schemas.user import UserLogin, UserRegister, UserInfo, LoginResponse, ChangePassword
from schemas.common import Response
from mongodb import PaperDatabase
from utils.auth import create_access_token, verify_token
# from schemas.user import UserLogin, UserRegister, UserInfo, LoginResponse
# from schemas.common import Response
# from mongodb import PaperDatabase
# from utils.auth import create_access_token, verify_token
from datetime import timedelta

router = APIRouter()
security = HTTPBearer()

# 初始化数据库
db = PaperDatabase()

# Token有效期（天）
ACCESS_TOKEN_EXPIRE_DAYS = 7

@router.post("/login", response_model=Response[LoginResponse], summary="用户登录")
async def login(user: UserLogin):
    """
    用户登录接口
    
    - **username**: 用户名
    - **password**: 密码
    
    返回JWT令牌和用户信息
    """
    # 验证用户
    verify_result = db.verify_user(user.username, user.password)
    
    if not verify_result.get("verify"):
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误"
        )
    
    user_info = verify_result.get("user_info")
    
    # 生成Token
    #此处代码成屎山了，命名没命好，后期维护的时候注意两者的区别
    token_data = {
        "uid": user_info.get("username"),#用户名 username，暂时为名字缩写 如sxs
        "user_id": str(user_info.get("_id", user.username))#用户ID,存储在数据库中的_id，在数据库中为ObjectId类型
    }
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    )
    
    # 构造响应
    login_response = LoginResponse(
        token=access_token,
        user_info=UserInfo(
            user_id=user.username,
            username=user_info.get("username"),
            email=user_info.get("email")
        ),
        expires_in=ACCESS_TOKEN_EXPIRE_DAYS * 24 * 3600
    )
    
    return Response(
        success=True,
        message="登录成功",
        data=login_response
    )

@router.post("/register", response_model=Response[UserInfo], summary="用户注册")
async def register(user: UserRegister):
    """
    用户注册接口
    
    - **username**: 用户名（3-50个字符）
    - **password**: 密码（至少6个字符）
    - **email**: 邮箱（可选）
    """
    # TODO: 实现用户注册逻辑
    # 这里需要在mongodb.py中添加注册方法
    raise HTTPException(
        status_code=501,
        detail="注册功能暂未实现，请联系管理员创建账户"
    )

# 依赖项：获取当前用户
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    从Token中获取当前用户信息
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="无效的认证凭据"
        )

    print(f"以下是用户信息\n{payload}")
    return payload

@router.get("/me", response_model=Response[UserInfo], summary="获取当前用户信息")
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    获取当前登录用户的信息
    """
    user_info = UserInfo(
        user_id=current_user.get("user_id"),
        username=current_user.get("sub"),
        email=None
    )
    
    return Response(
        success=True,
        message="获取成功",
        data=user_info
    )

@router.post("/change-password", response_model=Response, summary="修改密码")
async def change_password(
    password_data: ChangePassword,
    current_user: dict = Depends(get_current_user)
):
    """
    修改当前用户密码
    
    - **old_password**: 旧密码
    - **new_password**: 新密码（至少6个字符）
    """
    username = current_user.get("uid")
    
    # 调用数据库方法修改密码
    result = db.change_password(
        username=username,
        old_password=password_data.old_password,
        new_password=password_data.new_password
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "密码修改失败")
        )
    
    return Response(
        success=True,
        message="密码修改成功",
        data=None
    )

