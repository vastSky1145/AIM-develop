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
    original_filename = os.path.basename(file.filename)

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
        existing = collection.get(where={"source": original_filename}, limit=1)
        if len(existing['ids']) == 0:
            existing = collection.get(where={"original_filename": original_filename,"uid": user_id}, limit=1)
        if len(existing['ids']) > 0:
            raise HTTPException(
                status_code=400,
                detail=f"文件已存在：{file.filename}"
            )
    except Exception as e:
        pass

    temp_dir = None
    tmp_file_path = None

    try:
        # 保存临时文件，文件名保持与原始上传文件一致
        temp_dir = tempfile.mkdtemp()
        tmp_file_path = os.path.join(temp_dir, original_filename)
        content = await file.read()
        with open(tmp_file_path, 'wb') as tmp_file:
            tmp_file.write(content)
        print(f"tmp_file_path: {tmp_file_path}")

        # 使用 doc2x 解析 PDF
        app_key = "sk-bzllfk7oftj7tv4he6rc7bfdz92iqtn0"
        cmd = f'doc2x -k {app_key} --graphrag "{tmp_file_path}"'
        subprocess.run(cmd, shell=True, check=True)

        file_stem = Path(original_filename).stem
        output_dir = Path("./Output") / file_stem
        output_txt = output_dir / f"{file_stem}.txt"
        print(f"output_txt: {output_txt}")

        if not output_txt.exists():
            raise FileNotFoundError(f"解析结果未找到：{output_txt}")

        raw_content = output_txt.read_text(encoding='utf-8')

        # 删除 doc2x 生成的原始文本，后续仅保留过滤后内容
        try:
            output_txt.unlink()
        except FileNotFoundError:
            pass

        # 过滤内容
        pure_content = filter_paper_content(raw_content)

        # 保存过滤后的内容
        output_dir.mkdir(parents=True, exist_ok=True)
        filtered_txt = output_dir / f"{file_stem}_filtered.txt"
        filtered_txt.write_text(pure_content, encoding='utf-8')

        # 加载并分割文档
        loader = TextLoader(str(filtered_txt), encoding="UTF-8")
        documents = loader.load()
        docs = text_splitter.split_documents(documents)

        storage_path = str(filtered_txt)
        output_dir_path = str(output_dir)
        uploaded_at = datetime.now().isoformat()

        for index, doc in enumerate(docs):
            doc.metadata["uid"] = str(user_id)
            doc.metadata["uploaded_at"] = uploaded_at
            doc.metadata["original_filename"] = original_filename
            doc.metadata["source"] = original_filename
            doc.metadata["storage_path"] = storage_path
            doc.metadata["output_dir"] = output_dir_path
            doc.metadata["chunk_index"] = index

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
        if 'tmp_file_path' in locals() and tmp_file_path and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        if 'temp_dir' in locals() and temp_dir and os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

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
        
        metadatas = result.get('metadatas', []) or []
        output_dirs = {meta.get("output_dir") for meta in metadatas if meta.get("output_dir")}
        storage_paths = {meta.get("storage_path") for meta in metadatas if meta.get("storage_path")}

        # 删除向量数据库中的文档
        collection.delete(ids=result['ids'])
        
        # 删除相关文件
        deleted_files = []

        for path in storage_paths:
            if path and os.path.exists(path):
                os.remove(path)
                deleted_files.append(path)

        source_stem = Path(request.source).stem

        if not storage_paths:
            fallback_filtered = Path("./Output") / source_stem / f"{source_stem}_filtered.txt"
            if fallback_filtered.exists():
                fallback_filtered.unlink()
                deleted_files.append(str(fallback_filtered))

            legacy_txt = Path(request.source)
            if legacy_txt.exists():
                legacy_txt.unlink()
                deleted_files.append(str(legacy_txt))

        for directory in output_dirs:
            if directory and os.path.exists(directory):
                shutil.rmtree(directory)
                deleted_files.append(directory)

        if not output_dirs:
            fallback_dir = Path("./Output") / source_stem
            if fallback_dir.exists():
                shutil.rmtree(fallback_dir)
                deleted_files.append(str(fallback_dir))
        
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

