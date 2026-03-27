"""
Prompt模板管理相关路由
"""
from fastapi import APIRouter, HTTPException, Depends
from schemas.prompt import PromptTemplateCreate, PromptTemplateResponse
from schemas.common import Response
from routers.auth import get_current_user
from mongodb import PaperDatabase
from models import Prompt_Template
from utils.rate_limiter import rate_limiter
from config import settings

router = APIRouter()
db = PaperDatabase()

# 以包为粒度的速率限制依赖（prompts 包统一限速）
_rate_limit = rate_limiter.make_dependency(
    package_name="prompts",
    get_user_fn=get_current_user,
    **settings.RATE_LIMITS["prompts"],
)

@router.get("/get/{ppt_id}", response_model=Response[PromptTemplateResponse], summary="获取Prompt模板")
async def get_prompt(
    ppt_id: str,
    current_user: dict = Depends(_rate_limit)
):
    """
    根据PPT章节ID获取Prompt模板
    
    - **ppt_id**: PPT章节ID（如：ppt1.1）
    """
    prompt = db.get_prompt(ppt_id)
    
    if prompt is None:
        # 返回默认模板
        default_template = (
            "你是一个研究视频传输的专家，是一个美国教授。 请将下述已有内容\n$$\n"
            "补全为完整的段落.\n要求保持子目录组织结构不变。\n"
            "补全段落时以下面的知识库位参考资料\n$$。\n"
            "写作逻辑要和以下章节的逻辑内容呼应\n$$。\n"
            "补全段落时要求生成的内容是对已有内容的补充，不改变已有内容的目录结构，"
            "可以适当对已有内容的句子扩充，但要保证句子之间逻辑结构和原来一致，扩充内容不要超过1句。"
            "知识库中的知识只能作为参考，总结归纳其中语义相关的知识作为参照，而不是直接引用。"
            "知识库中出现的图表，若已有内容中没有，则认为该知识不相关，不能作为参考。"
            "生成内容和知识库中的原句不可以一样。 latex公式不要编译。要求英文撰写。"
            "凝练成逻辑严密的一段话。不要目录结构，不要出现目录编号。"
            "生成的文字中要包括已有内容里对图或者表的引用。要求语言风格比较学术化。"
        )
        
        response = PromptTemplateResponse(
            ppt_id=ppt_id,
            prompt_json=default_template
        )
        
        return Response(
            success=True,
            message="返回默认模板",
            data=response
        )
    
    response = PromptTemplateResponse(
        ppt_id=prompt.ppt_id,
        prompt_json=prompt.prompt_json
    )
    
    return Response(
        success=True,
        message="获取成功",
        data=response
    )

@router.post("/save", response_model=Response[bool], summary="保存Prompt模板")
async def save_prompt(
    prompt: PromptTemplateCreate,
    current_user: dict = Depends(_rate_limit)
):
    """
    保存或更新Prompt模板
    
    - **ppt_id**: PPT章节ID
    - **prompt_json**: Prompt模板内容
    """
    try:
        prompt_obj = Prompt_Template(
            ppt_id=prompt.ppt_id,
            prompt_json=prompt.prompt_json
        )
        
        success = db.save_prompt(prompt_obj)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="保存Prompt模板失败"
            )
        
        return Response(
            success=True,
            message="Prompt模板保存成功",
            data=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"保存失败: {str(e)}"
        )

