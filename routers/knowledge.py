"""
知识库管理相关路由
"""
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from schemas.knowledge import (
    KnowledgeSearchRequest, KnowledgeSearchResponse,
    KnowledgeDocument, KnowledgeSource, DeleteKnowledgeRequest
)
from schemas.common import Response
from routers.auth import get_current_user
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from filter import filter_paper_content
from typing import List
import os
import tempfile
import subprocess
from pathlib import Path
import shutil
from collections import defaultdict

router = APIRouter()

# 配置 HuggingFace 镜像源，避免直接访问官方站点导致超时
if not os.environ.get("HF_ENDPOINT") and not os.environ.get("HUGGINGFACE_HUB_BASE_URL"):
    mirror_url = "https://hf-mirror.com"
    os.environ["HF_ENDPOINT"] = mirror_url
    os.environ["HUGGINGFACE_HUB_BASE_URL"] = mirror_url

# 初始化向量数据库
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=1)

@router.post("/search", response_model=Response[KnowledgeSearchResponse], summary="检索知识库")
async def search_knowledge(
    request: KnowledgeSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    在知识库中检索相关内容

    - **query**: 查询文本
    - **k**: 返回结果数量（1-20）
    """
    user_id = current_user.get("uid")# or current_user.get("user_id") or current_user.get("id") or current_user.get("username")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="无法获取用户信息"
        )

    try:
        # 执行相似度搜索
        docs = vectorstore.similarity_search(request.query, k=request.k, filter={"uid": user_id})

        # 构造响应
        documents = [
            KnowledgeDocument(
                content=doc.page_content,
                source=doc.metadata.get('source', '未知'),
                metadata=doc.metadata
            )
            for doc in docs
        ]

        response = KnowledgeSearchResponse(
            documents=documents,
            total=len(documents)
        )

        return Response(
            success=True,
            message=f"找到{len(documents)}个相关结果",
            data=response
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"检索失败: {str(e)}"
        )

@router.post("/upload-pdf", response_model=Response[dict], summary="上传PDF到知识库")
async def upload_pdf(
    file: UploadFile = File(..., description="PDF文件"),
    current_user: dict = Depends(get_current_user)
):
    """
    上传PDF文件到知识库

    - 自动解析PDF内容
    - 过滤无关内容
    - 分块存储到向量数据库
    """
    user_id = current_user.get("uid")# or current_user.get("user_id") or current_user.get("id") or current_user.get("username")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="无法获取用户信息"
        )

    # 验证文件类型
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="只支持PDF文件格式"
        )

    # 验证文件名（不允许空格）
    if ' ' in file.filename:
        raise HTTPException(
            status_code=400,
            detail=f"文件名不允许包含空格：{file.filename}"
        )

    # 检查是否已存在
    try:
        collection = vectorstore._collection
        existing = collection.get(where={"source": file.filename}, limit=1)
        if len(existing['ids']) > 0:
            raise HTTPException(
                status_code=400,
                detail=f"文件已存在：{file.filename}"
            )
    except Exception as e:
        pass

    try:
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            print(f"tmp_file: {tmp_file.name}")
            tmp_file_path = tmp_file.name
            print(f"tmp_file_path: {tmp_file_path}")

        # 使用doc2x解析PDF
        app_key = "sk-bzllfk7oftj7tv4he6rc7bfdz92iqtn0"
        cmd = f"doc2x -k {app_key} --graphrag {tmp_file_path}"
        subprocess.run(cmd, shell=True, check=True)

        # 读取解析结果
        cc = Path(tmp_file_path).name.rstrip('pdf')
        co = Path(cc).name.rstrip('.')
        output_txt = f"./Output/{co}/{co}.txt"
        print(f"output_txt: {output_txt}")
        with open(output_txt, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        #删除output_txt文件
        if os.path.exists(output_txt):
            os.remove(output_txt)

        # 过滤内容
        pure_content = filter_paper_content(raw_content)

        # 保存过滤后的内容
        filtered_txt = f"{co}.txt"
        with open(filtered_txt, 'w', encoding='utf-8') as f:
            f.write(pure_content)

        # 加载并分割文档
        loader = TextLoader(filtered_txt, encoding="UTF-8")
        documents = loader.load()
        docs = text_splitter.split_documents(documents)

        for doc in docs:
            doc.metadata["uid"] = str(user_id)
            doc.metadata["uploaded_at"] = datetime.now().isoformat()
            doc.metadata["original_filename"] = file.filename

        # 添加到向量数据库
        vectorstore.add_documents(docs)

        return Response(
            success=True,
            message=f"PDF已成功添加到知识库，共{len(docs)}个文档块",
            data={
                "filename": file.filename,
                "chunks": len(docs),
                "content_preview": pure_content[:500] + "..."
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"处理PDF失败: {str(e)}"
        )
    finally:
        # 清理临时文件
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)

@router.get("/sources", response_model=Response[List[KnowledgeSource]], summary="获取知识来源列表")
async def get_sources(current_user: dict = Depends(get_current_user)):
    """
    获取知识库中所有来源列表
    """
    try:
        user_id = current_user.get("uid")# or current_user.get("user_id") or current_user.get("id") or current_user.get("username")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="无法获取用户信息"
            )
        print(f"用户uid:{user_id}")

        all_docs = vectorstore.get(where={"uid": user_id})['metadatas']
        
        # 按source分组统计
        source_dict = defaultdict(int)
        for doc in all_docs:
            if 'source' in doc:
                source_dict[doc['source']] += 1
        
        sources = [
            KnowledgeSource(source=source, doc_count=count)
            for source, count in source_dict.items()
        ]
        
        return Response(
            success=True,
            message=f"共{len(sources)}个来源",
            data=sources
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取来源列表失败: {str(e)}"
        )

@router.delete("/delete", response_model=Response[bool], summary="删除知识")
async def delete_knowledge(
    request: DeleteKnowledgeRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    根据来源删除知识库内容
    """
    try:
        collection = vectorstore._collection
        result = collection.get(where={"source": request.source})
        
        if not result['ids']:
            raise HTTPException(
                status_code=404,
                detail=f"未找到来源为'{request.source}'的文档"
            )
        
        # 删除向量数据库中的文档
        collection.delete(ids=result['ids'])
        
        # 删除相关文件
        deleted_files = []
        cc = Path(request.source).name.rstrip('pdf')
        co = Path(cc).name.rstrip('.')
        output_dir = f"./Output/{co}"
        
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            deleted_files.append(output_dir)
        
        txt_file = request.source
        if os.path.exists(txt_file):
            os.remove(txt_file)
            deleted_files.append(txt_file)
        
        return Response(
            success=True,
            message=f"已删除{len(result['ids'])}个文档块",
            data=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"删除失败: {str(e)}"
        )

@router.delete("/clear", response_model=Response[bool], summary="清空知识库")
async def clear_knowledge(current_user: dict = Depends(get_current_user)):
    """
    清空整个知识库（危险操作）
    """
    try:
        collection = vectorstore._collection
        collection.delete(where={})
        
        return Response(
            success=True,
            message="知识库已清空",
            data=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"清空失败: {str(e)}"
        )

