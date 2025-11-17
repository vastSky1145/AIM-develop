"""
用户Prompt管理相关路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from schemas.user_prompt import (
    FolderCreate, FolderUpdate, FolderResponse,
    PromptCreate, PromptUpdate, PromptResponse,
    PromptVersionResponse
)
from schemas.common import Response
from routers.auth import get_current_user
from mongodb import PromptFolderDatabase
from typing import List, Optional

router = APIRouter()
db = PromptFolderDatabase()

# ============ 收藏夹相关路由 ============

@router.get("/folders", response_model=Response[List[FolderResponse]], summary="获取用户的所有收藏夹")
async def get_folders(
    current_user: dict = Depends(get_current_user)
):
    """
    获取当前用户的所有收藏夹列表
    """
    try:
        user_id = current_user.get('uid')
        folders = db.get_user_folders(user_id)
        
        return Response(
            success=True,
            message=f"获取成功，共{len(folders)}个收藏夹",
            data=folders
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取收藏夹列表失败: {str(e)}"
        )

@router.post("/folders", response_model=Response[FolderResponse], summary="创建收藏夹")
async def create_folder(
    folder: FolderCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    创建新的收藏夹
    
    - **folder_name**: 收藏夹名称（必填）
    - **description**: 收藏夹描述（可选）
    """
    try:
        user_id = current_user.get('uid')
        folder_id = db.create_folder(
            user_id=user_id,
            folder_name=folder.folder_name,
            description=folder.description
        )
        
        if not folder_id:
            raise HTTPException(
                status_code=500,
                detail="创建收藏夹失败"
            )
        
        # 获取创建的收藏夹信息
        created_folder = db.get_folder_by_id(folder_id)
        
        return Response(
            success=True,
            message="收藏夹创建成功",
            data=created_folder
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"创建收藏夹失败: {str(e)}"
        )

@router.put("/folders/{folder_id}", response_model=Response[bool], summary="更新收藏夹")
async def update_folder(
    folder_id: str,
    folder: FolderUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    更新收藏夹信息
    
    - **folder_id**: 收藏夹ID
    - **folder_name**: 新的收藏夹名称（可选）
    - **description**: 新的收藏夹描述（可选）
    """
    try:
        user_id = current_user.get('uid')
        
        # 验证收藏夹是否存在
        existing_folder = db.get_folder_by_id(folder_id)
        if not existing_folder:
            raise HTTPException(
                status_code=404,
                detail="收藏夹不存在"
            )
        
        if existing_folder['user_id'] != user_id:
            raise HTTPException(
                status_code=403,
                detail="无权限修改此收藏夹"
            )
        
        success = db.update_folder(
            folder_id=folder_id,
            user_id=user_id,
            folder_name=folder.folder_name,
            description=folder.description
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="更新收藏夹失败"
            )
        
        return Response(
            success=True,
            message="收藏夹更新成功",
            data=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"更新收藏夹失败: {str(e)}"
        )

@router.delete("/folders/{folder_id}", response_model=Response[bool], summary="删除收藏夹")
async def delete_folder(
    folder_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    删除收藏夹（同时删除其下的所有Prompts）
    
    - **folder_id**: 收藏夹ID
    """
    try:
        user_id = current_user.get('uid')
        
        # 验证收藏夹是否存在
        existing_folder = db.get_folder_by_id(folder_id)
        if not existing_folder:
            raise HTTPException(
                status_code=404,
                detail="收藏夹不存在"
            )
        
        if existing_folder['user_id'] != user_id:
            raise HTTPException(
                status_code=403,
                detail="无权限删除此收藏夹"
            )
        
        success = db.delete_folder(folder_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="删除收藏夹失败"
            )
        
        return Response(
            success=True,
            message="收藏夹删除成功",
            data=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"删除收藏夹失败: {str(e)}"
        )

# ============ Prompt相关路由 ============

@router.get("/list", response_model=Response[List[PromptResponse]], summary="获取指定收藏夹下的所有Prompts")
async def get_prompts_by_folder(
    folder_id: str = Query(..., description="收藏夹ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取指定收藏夹下的所有Prompts
    
    - **folder_id**: 收藏夹ID
    """
    try:
        user_id = current_user.get('uid')
        
        # 验证收藏夹是否存在
        folder = db.get_folder_by_id(folder_id)
        if not folder:
            raise HTTPException(
                status_code=404,
                detail="收藏夹不存在"
            )
        
        if folder['user_id'] != user_id:
            raise HTTPException(
                status_code=403,
                detail="无权限访问此收藏夹"
            )
        
        prompts = db.get_prompts_by_folder(folder_id, user_id)
        
        return Response(
            success=True,
            message=f"获取成功，共{len(prompts)}个Prompt",
            data=prompts
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取Prompt列表失败: {str(e)}"
        )

@router.post("/create", response_model=Response[PromptResponse], summary="创建Prompt")
async def create_prompt(
    prompt: PromptCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    创建新的Prompt
    
    - **folder_id**: 所属收藏夹ID（必填）
    - **prompt_name**: Prompt名称（必填）
    - **prompt_content**: Prompt内容（必填）
    - **description**: Prompt描述（可选）
    - **tags**: 标签列表（可选）
    """
    try:
        user_id = current_user.get('uid')
        
        # 验证收藏夹是否存在
        folder = db.get_folder_by_id(prompt.folder_id)
        if not folder:
            raise HTTPException(
                status_code=404,
                detail="收藏夹不存在"
            )
        
        if folder['user_id'] != user_id:
            raise HTTPException(
                status_code=403,
                detail="无权限在此收藏夹中创建Prompt"
            )
        
        prompt_id = db.create_prompt(
            user_id=user_id,
            folder_id=prompt.folder_id,
            prompt_name=prompt.prompt_name,
            prompt_content=prompt.prompt_content,
            description=prompt.description,
            tags=prompt.tags
        )
        
        if not prompt_id:
            raise HTTPException(
                status_code=500,
                detail="创建Prompt失败"
            )
        
        # 获取创建的Prompt信息
        created_prompt = db.get_prompt_by_id(prompt_id)
        
        return Response(
            success=True,
            message="Prompt创建成功",
            data=created_prompt
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"创建Prompt失败: {str(e)}"
        )

@router.put("/update/{prompt_id}", response_model=Response[bool], summary="更新Prompt")
async def update_prompt(
    prompt_id: str,
    prompt: PromptUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    更新Prompt信息（带版本控制）
    
    - **prompt_id**: Prompt ID
    - **change_description**: 修改描述（必填）
    - **folder_id**: 新的所属收藏夹ID（可选）
    - **prompt_name**: 新的Prompt名称（可选）
    - **prompt_content**: 新的Prompt内容（可选）
    - **description**: 新的Prompt描述（可选）
    - **tags**: 新的标签列表（可选）
    """
    try:
        user_id = current_user.get('uid')
        
        # 验证Prompt是否存在
        existing_prompt = db.get_prompt_by_id(prompt_id)
        if not existing_prompt:
            raise HTTPException(
                status_code=404,
                detail="Prompt不存在"
            )
        
        if existing_prompt['user_id'] != user_id:
            raise HTTPException(
                status_code=403,
                detail="无权限修改此Prompt"
            )
        
        # 如果要更改收藏夹，验证新收藏夹是否存在
        if prompt.folder_id:
            new_folder = db.get_folder_by_id(prompt.folder_id)
            if not new_folder:
                raise HTTPException(
                    status_code=404,
                    detail="目标收藏夹不存在"
                )
            if new_folder['user_id'] != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="无权限将Prompt移动到此收藏夹"
                )
        
        success = db.update_prompt(
            prompt_id=prompt_id,
            user_id=user_id,
            change_description=prompt.change_description,
            folder_id=prompt.folder_id,
            prompt_name=prompt.prompt_name,
            prompt_content=prompt.prompt_content,
            description=prompt.description,
            tags=prompt.tags
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="更新Prompt失败"
            )
        
        return Response(
            success=True,
            message="Prompt更新成功",
            data=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"更新Prompt失败: {str(e)}"
        )

@router.delete("/delete/{prompt_id}", response_model=Response[bool], summary="删除Prompt")
async def delete_prompt(
    prompt_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    删除Prompt
    
    - **prompt_id**: Prompt ID
    """
    try:
        user_id = current_user.get('uid')
        
        # 验证Prompt是否存在
        existing_prompt = db.get_prompt_by_id(prompt_id)
        if not existing_prompt:
            raise HTTPException(
                status_code=404,
                detail="Prompt不存在"
            )
        
        if existing_prompt['user_id'] != user_id:
            raise HTTPException(
                status_code=403,
                detail="无权限删除此Prompt"
            )
        
        success = db.delete_prompt(prompt_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="删除Prompt失败"
            )
        
        return Response(
            success=True,
            message="Prompt删除成功",
            data=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"删除Prompt失败: {str(e)}"
        )

@router.get("/search", response_model=Response[List[PromptResponse]], summary="搜索Prompts")
async def search_prompts(
    keyword: str = Query(..., description="搜索关键词", min_length=1),
    current_user: dict = Depends(get_current_user)
):
    """
    搜索Prompts（按名称、描述、标签）
    
    - **keyword**: 搜索关键词
    """
    try:
        user_id = current_user.get('uid')
        prompts = db.search_prompts(user_id, keyword)
        
        return Response(
            success=True,
            message=f"搜索完成，找到{len(prompts)}个Prompt",
            data=prompts
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"搜索Prompt失败: {str(e)}"
        )

# ============ 版本控制相关路由 ============

@router.get("/versions/{prompt_id}", response_model=Response[List[PromptVersionResponse]], summary="获取Prompt版本历史")
async def get_prompt_versions(
    prompt_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取指定Prompt的所有版本历史
    
    - **prompt_id**: Prompt ID
    """
    try:
        user_id = current_user.get('uid')
        
        # 验证Prompt是否存在
        prompt = db.get_prompt_by_id(prompt_id)
        if not prompt:
            raise HTTPException(
                status_code=404,
                detail="Prompt不存在"
            )
        
        if prompt['user_id'] != user_id:
            raise HTTPException(
                status_code=403,
                detail="无权限查看此Prompt的版本历史"
            )
        
        versions = db.get_prompt_versions(prompt_id, user_id)
        
        return Response(
            success=True,
            message=f"获取成功，共{len(versions)}个版本",
            data=versions
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取版本历史失败: {str(e)}"
        )

