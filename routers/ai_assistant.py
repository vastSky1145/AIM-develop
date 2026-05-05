"""
AI辅助写作相关路由
"""
from fastapi import APIRouter, HTTPException, Depends
from schemas.ai import GenerateContentRequest, ModifyContentRequest, GenerateContentResponse, SubmitRatingRequest
from schemas.common import Response
from routers.auth import get_current_user
from AI import llm
import asyncio
from concurrent.futures import ThreadPoolExecutor
from mongodb import LogDatabase

router = APIRouter()
log_database = LogDatabase()

# 创建线程池执行器
executor = ThreadPoolExecutor(max_workers=4)

def call_llm_sync(prompt: str) -> str:
    """
    同步调用LLM（在线程池中执行）
    """
    try:
        completion = llm.chat.completions.create(
            # model="gemini-2.5-flash-preview-05-20",
            # model="deepseek-v3",
            model="DeepSeek-V4-Flash",
            reasoning_effort="low",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        raise Exception(f"调用LLM失败: {str(e)}")

@router.post("/generate", response_model=Response[GenerateContentResponse], summary="生成内容")
async def generate_content(
    request: GenerateContentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    使用AI生成论文内容
    
    - **existing_text**: 已有内容
    - **kb_content**: 知识库参考内容
    - **section_text**: 章节参考内容
    - **prompt_template**: Prompt模板（使用$$作为占位符）
    
    模板中的占位符将被替换：
    - 第一个$$：已有内容
    - 第二个$$：知识库内容
    - 第三个$$：章节参考内容
    """
    # 验证prompt模板
    if request.prompt_template.count('$$') < 2:
        raise HTTPException(
            status_code=400,
            detail="Prompt模板中必须包含至少两个$$作为占位符"
        )
    
    # 构造完整prompt
    full_prompt = request.prompt_template
    full_prompt = full_prompt.replace('$$', request.existing_text, 1)
    full_prompt = full_prompt.replace('$$', request.kb_content, 1)
    
    if request.prompt_template.count('$$') >= 3:
        full_prompt = full_prompt.replace('$$', request.section_text, 1)
    
    if not full_prompt.strip():
        raise HTTPException(
            status_code=400,
            detail="生成的Prompt内容为空"
        )
    
    try:
        # 在线程池中异步调用LLM
        loop = asyncio.get_event_loop()
        generated_text = await loop.run_in_executor(
            executor,
            call_llm_sync,
            full_prompt
        )
        
        #返回结果前,记录日志
        log = {
            "user_id": current_user.get("uid"),#用户名
            "u_id": current_user.get("user_id"),#用户在mongodb中的id
            "existing_text": request.existing_text,
            "kb_content": request.kb_content,
            "section_text": request.section_text,
            "prompt_template": request.prompt_template,
            "generated_content": generated_text,
        }
        log_id = log_database.save_generate_log(log)
        
        response = GenerateContentResponse(
            generated_content=generated_text,
            tokens_used=None,  # 可以后续添加token统计
            generated_id=log_id
        )
        
        return Response(
            success=True,
            message="内容生成成功",
            data=response
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成内容失败: {str(e)}"
        )

@router.post("/modify", response_model=Response[GenerateContentResponse], summary="修改内容")
async def modify_content(
    request: ModifyContentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    使用AI修改内容
    
    - **original_content**: 原始内容
    - **modification_instruction**: 修改指令
    """
    # 构造修改prompt
    prompt = f"这是已有内容：{request.original_content}\n\n{request.modification_instruction}"
    
    try:
        # 在线程池中异步调用LLM
        loop = asyncio.get_event_loop()
        modified_text = await loop.run_in_executor(
            executor,
            call_llm_sync,
            prompt
        )

        #返回结果前,记录日志
        log = {
            "user_id": current_user.get("uid"),#用户名
            "u_id": current_user.get("user_id"),#用户在mongodb中的id
            "original_content": request.original_content,
            "modification_instruction": request.modification_instruction,
            "modified_content": modified_text,
        }
        log_id = log_database.save_modify_log(log)
        
        response = GenerateContentResponse(
            generated_content=modified_text,
            tokens_used=None,
            generated_id=log_id
        )
        
        return Response(
            success=True,
            message="内容修改成功",
            data=response
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"修改内容失败: {str(e)}"
        )

@router.post("/rating", response_model=Response[bool], summary="提交用户评价和评分")
async def submit_rating(
    request: SubmitRatingRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    提交用户评价和评分
    """
    try:
        #返回结果前,记录日志
        log = {
            "user_id": current_user.get("uid"),#用户名
            "u_id": current_user.get("user_id"),#用户在mongodb中的id
            "generated_id": request.generated_id,#用户对ai生成内容的评价，id指的是本次生成在mongodb中的id
            "score": request.score,#用户评分
            "comment": request.comment,#用户评价
        }
        log_id = log_database.save_rating_log(log)
        return Response(
            success=True,
            message="用户评价和评分提交成功",
            data=True
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"提交用户评价和评分失败: {str(e)}"
        )