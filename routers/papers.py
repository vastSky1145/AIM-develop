"""
论文管理相关路由
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.params import Body
from fastapi.responses import FileResponse

from pdf_to_json import pdf_to_json
from schemas.paper import (
# from schemas.paper import (
    PaperCreate, PaperUpdate, PaperResponse,
    PaperListItem, DeletePaperRequest
)
from schemas.common import Response
from mongodb import PaperDatabase
from routers.auth import get_current_user
# from ppt_to_json import ppt_to_json
from typing import List
import json
import tempfile
import os
from pathlib import Path
import uuid
import asyncio

from utils.test_pdf_parse_locally import parse_pdf_to_json_locally
from utils.pdf_to_structure import pdf_to_structured_json

router = APIRouter()
db = PaperDatabase()

# 内存任务状态表 {task_id: {status, progress, data, error}} — Agent PDF 解析
_tasks: dict = {}

@router.get("/list", response_model=Response[List[PaperResponse]], summary="获取论文列表")
async def get_paper_list(current_user: dict = Depends(get_current_user)):
    """
    获取当前用户的所有论文列表
    """
    # user_id = current_user.get("user_id") #68edf79cf014443c949b3f48
    user_id = current_user.get("uid") #sxs
    print(f"用户的信息：{current_user}")


    result = db.query_papers_by_uid(user_id)

    if not result["success"]:
        return Response(
            success=False,
            message=result["message"],
            data=[]
        )

    papers = result.get("papers", [])

    return Response(
        success=True,
        message=f"成功获取{len(papers)}篇论文",
        data=papers
    )

#旧api，上传参数为file，现在改为pdf文件
# @router.post("/upload-ppt", response_model=Response[PaperResponse], summary="上传PPT并解析")
# async def upload_ppt(
#     file: UploadFile = File(..., description="PPT文件"),
#     current_user: dict = Depends(get_current_user)
# ):
#     """
#     上传PPT文件并解析为论文结构
#
#     - 支持.ppt和.pptx格式
#     - 自动解析为结构化JSON
#     - 保存到数据库
#     """
#     # user_id = current_user.get("user_id")
#     user_id = current_user.get("uid")
#
#     # 验证文件类型
#     if not file.filename.endswith(('.ppt', '.pptx')):
#         raise HTTPException(
#             status_code=400,
#             detail="只支持PPT文件格式（.ppt或.pptx）"
#         )
#
#     # 保存临时文件
#     try:
#         # 创建临时文件
#         suffix = Path(file.filename).suffix
#         with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
#             content = await file.read()
#             tmp_file.write(content)
#             tmp_file_path = tmp_file.name
#
#         # 调用PPT解析函数
#         json_content = ppt_to_json(tmp_file_path, user_id)
#         paper_data = json.loads(json_content)
#
#         # 保存到数据库
#         paper_id = db.save_paper(paper_data)
#
#         if paper_id is None:
#             raise HTTPException(
#                 status_code=500,
#                 detail="保存论文到数据库失败"
#             )
#
#         return Response(
#             success=True,
#             message="PPT解析成功",
#             data=paper_data
#         )
#
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"PPT解析失败: {str(e)}"
#         )
#     finally:
#         # 清理临时文件
#         if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
#             os.unlink(tmp_file_path)

#新api，上传参数为pdf文件（由用户在本地ppt转化的pdf文件）
# @router.post("/upload-pdf", response_model=Response[PaperResponse], summary="上传pdf文件并解析")
# async def upload_pdf(
#     file: UploadFile = File(..., description="pdf文件"),
#     current_user: dict = Depends(get_current_user)
# ):
#     """
#     上传pdf文件并解析为论文结构
#
#     - 支持.pdf格式
#     - 自动解析为结构化JSON
#     - 保存到数据库
#     """
#     # user_id = current_user.get("user_id")
#     user_id = current_user.get("uid")
#
#     # 验证文件类型
#     if not file.filename.endswith(('.pdf')):
#         raise HTTPException(
#             status_code=400,
#             detail="只支持pdf文件格式（.pdf）"
#         )
#
#     # 保存临时文件
#     try:
#         # 创建临时文件
#         suffix = Path(file.filename).suffix#suffix函数返回文件的后缀名
#         with tempfile.NamedTemporaryFile(delete=True, suffix=suffix) as tmp_file:
#             content = await file.read()
#             tmp_file.write(content)
#             tmp_file_path = tmp_file.name
#
#         # 调用PPT解析函数
#         json_content = pdf_to_json(tmp_file_path, user_id)
#         paper_data = json.loads(json_content)
#
#         # 保存到数据库
#         paper_id = db.save_paper(paper_data)
#
#         if paper_id is None:
#             raise HTTPException(
#                 status_code=500,
#                 detail="保存论文到数据库失败"
#             )
#
#         return Response(
#             success=True,
#             message="PPT解析成功",
#             data=paper_data
#         )
#
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"PPT解析失败: {str(e)}"
#         )
#     finally:
#         # 清理临时文件
#         if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
#             os.unlink(tmp_file_path)

# ==================== Agent PDF 解析（异步，LLM）====================

async def _run_agent_task(task_id: str, pdf_path: str, user_id: str):
    """后台运行 Agent 解析，完成后更新任务状态并入库"""
    try:
        _tasks[task_id]["progress"] = "Agent 正在分析文档结构，请耐心等待..."
        result = await asyncio.to_thread(
            pdf_to_structured_json,
            pdf_path,
            user_id
        )
        result["uid"] = user_id

        _tasks[task_id]["progress"] = "解析完成，正在保存到数据库..."
        paper_id = db.save_paper(result)
        if paper_id is None:
            raise RuntimeError("保存论文到数据库失败")

        _tasks[task_id].update({
            "status": "completed",
            "progress": "保存成功",
            "data": result
        })
    except Exception as e:
        _tasks[task_id].update({
            "status": "failed",
            "progress": "",
            "error": str(e)
        })
    finally:
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


@router.post("/upload-pdf", response_model=Response[dict], summary="上传 PDF 并用 Agent 解析（异步）")
async def upload_pdf_agent(
    file: UploadFile = File(..., description="PDF 文件"),
    current_user: dict = Depends(get_current_user)
):
    """
    上传 PDF，立即返回 task_id，解析在后台由 LangChain Agent 完成。
    前端应轮询 GET /papers/task/{task_id} 查询进度。
    """
    user_id = current_user.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="无法获取用户信息")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只支持 PDF 文件格式（.pdf）")

    suffix = Path(file.filename).suffix
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    finally:
        tmp_file.close()

    task_id = str(uuid.uuid4())
    _tasks[task_id] = {
        "status": "processing",
        "progress": "正在启动 Agent 解析...",
        "data": None,
        "error": None
    }

    asyncio.create_task(_run_agent_task(task_id, tmp_file_path, user_id))

    return Response(
        success=True,
        message="任务已提交，请轮询查询进度",
        data={"task_id": task_id, "status": "processing"}
    )


@router.get("/task/{task_id}", response_model=Response[dict], summary="查询 Agent 解析任务状态")
async def get_task_status(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    task = _tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")

    return Response(
        success=True,
        message="获取任务状态成功",
        data=task
    )


# ==================== 旧方法 PDF 解析（同步，字符串匹配）====================

@router.post("/upload-pdf-fast", response_model=Response[PaperResponse], summary="上传 PDF 并用字符串匹配解析（同步）")
async def upload_pdf_fast(
    file: UploadFile = File(..., description="PDF 文件"),
    current_user: dict = Depends(get_current_user)
):
    """
    上传 PDF，使用字符串匹配方式同步解析，速度快但精度较低。
    """
    user_id = current_user.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="无法获取用户信息")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只支持 PDF 文件格式（.pdf）")

    suffix = Path(file.filename).suffix
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    finally:
        tmp_file.close()

    try:
        json_content = await asyncio.to_thread(parse_pdf_to_json_locally, tmp_file_path)
        paper_data = json.loads(json_content)
        paper_data["uid"] = user_id

        paper_id = db.save_paper(paper_data)
        if paper_id is None:
            raise RuntimeError("保存论文到数据库失败")

        return Response(
            success=True,
            message="PDF 解析成功（字符串匹配）",
            data=paper_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 解析失败: {str(e)}")
    finally:
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)


@router.post("/create", response_model=Response[PaperResponse], summary="创建新论文")
async def create_paper(
    paper: PaperCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    创建新论文
    """
    user_id = current_user.get("uid")

    # 确保uid与当前用户匹配
    paper_data = paper.model_dump()
    paper_data["uid"] = user_id

    try:
        paper_id = db.save_paper(paper_data)

        if paper_id is None:
            raise HTTPException(
                status_code=500,
                detail="保存论文失败"
            )

        return Response(
            success=True,
            message="论文创建成功",
            data=paper_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"创建论文失败: {str(e)}"
        )

@router.put("/update", response_model=Response[PaperResponse], summary="更新论文")
async def update_paper(
    paper: PaperCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    更新论文内容
    """
    user_id = current_user.get("uid")
    paper_title = current_user.get("paper_title")

    # 确保uid与当前用户匹配
    paper_data = paper.model_dump()
    paper_data["uid"] = user_id

    try:
        paper_id = db.save_paper(paper_data)

        return Response(
            success=True,
            message="论文更新成功",
            data=paper_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"更新论文失败: {str(e)}"
        )

@router.delete("/delete", response_model=Response[bool], summary="删除论文")
async def delete_paper(
    request: DeletePaperRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    删除论文
    """
    user_id = current_user.get("uid")

    # 验证是否是当前用户的论文
    if request.uid != user_id:
        raise HTTPException(
            status_code=403,
            detail="无权删除其他用户的论文"
        )

    try:
        success = db.delete_paper_by_title_and_uid(request.paper_title, user_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail="论文不存在或删除失败"
            )

        return Response(
            success=True,
            message="论文删除成功",
            data=True
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"删除论文失败: {str(e)}"
        )

@router.get("/get/{paper_title}", response_model=Response[PaperResponse], summary="获取论文详情")
async def get_paper(
    paper_title: str,
    current_user: dict = Depends(get_current_user)
):
    """
    根据标题获取论文详情
    """
    user_id = current_user.get("uid")

    result = db.query_papers_by_uid(user_id)

    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail=result["message"]
        )

    # 查找匹配的论文
    papers = result.get("papers", [])
    paper = next((p for p in papers if p.get("paper_title") == paper_title), None)

    if paper is None:
        raise HTTPException(
            status_code=404,
            detail="论文不存在"
        )

    return Response(
        success=True,
        message="获取成功",
        data=paper
    )

