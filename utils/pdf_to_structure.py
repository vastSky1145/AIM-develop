"""
PDF层次化结构提取 - 主入口

将PDF文档转换为层次化JSON结构，支持：
- 自动识别章节标题和层级
- 过滤页眉页脚等无关内容
- 可配置的最大层级深度
- LLM驱动的语义理解

使用示例:
    from utils.pdf_to_structure import pdf_to_structured_json
    
    result = pdf_to_structured_json(
        pdf_path="path/to/document.pdf",
        uid="user123",
        max_depth=3,
        filter_keywords=["中南大学", "作者姓名"]
    )
"""

import json
import os
from typing import List, Optional, Dict, Any

from utils.pdf_extractor import PDFTextExtractor, extract_pdf_for_agent, PageContent
from utils.pdf_structure_agent import (
    DEFAULT_MAX_PARALLEL_SECTIONS,
    DEFAULT_OUTLINE_MAX_TOKENS,
    DEFAULT_SECTION_MAX_TOKENS,
    PDFStructureAgent,
    create_pdf_structure_agent,
)


def pdf_to_structured_json(
    pdf_path: str,
    uid: str = "default",
    max_depth: int = 3,
    paper_title: str = "",
    # filter_keywords: List[str] = None,
    # filter_patterns: List[str] = None,
    api_key: str = None,
    base_url: str = None,
    model_name: str = None,
    verbose: bool = True,
    output_path: str = None,
    outline_max_tokens: int = DEFAULT_OUTLINE_MAX_TOKENS,
    section_max_tokens: int = DEFAULT_SECTION_MAX_TOKENS,
    max_parallel_sections: int = DEFAULT_MAX_PARALLEL_SECTIONS,
) -> Dict[str, Any]:
    """
    将PDF转换为层次化JSON结构
    
    Args:
        pdf_path: PDF文件路径
        uid: 用户ID，用于JSON中的uid字段
        max_depth: 最大章节层级深度（默认3层）
        paper_title: 论文标题（可选，如不提供则由Agent识别）
        filter_keywords: 需要过滤的关键词列表（如学校名、作者名）
        filter_patterns: 额外的正则过滤模式
        api_key: LLM API密钥（默认从环境变量读取）
        base_url: LLM API地址（默认从环境变量读取）
        model_name: 模型名称（默认从环境变量读取）
        verbose: 是否打印详细日志
        output_path: 输出JSON文件路径（可选）
        
    Returns:
        结构化的JSON字典，格式如下：
        {
            "uid": "user_id",
            "paper_title": "论文标题",
            "sections": [
                {
                    "id": "sec1",
                    "title": "章节1",
                    "content": "内容...",
                    "children": [...]
                },
                ...
            ]
        }
    """
    if verbose:
        print(f"[PDF结构化] 开始处理: {pdf_path}")
        print(f"[PDF结构化] 最大层级: {max_depth}")
    
    # Step 1: 提取PDF文本
    if verbose:
        print("[PDF结构化] 正在提取PDF文本...")
    
    extractor = PDFTextExtractor()
    
    # if filter_keywords:
    #     extractor.add_filter_keywords(filter_keywords)
    #     if verbose:
    #         print(f"[PDF结构化] 过滤关键词: {filter_keywords}")
    #
    # if filter_patterns:
    #     for pattern in filter_patterns:
    #         extractor.add_filter_pattern(pattern)
    
    pages = extractor.extract_pages(pdf_path)

    
    if verbose:
        print(f"[PDF结构化] 共提取 {len(pages)} 页")
        total_chars = sum(len(p.text) for p in pages)
        print(f"[PDF结构化] 总字符数: {total_chars}")
    
    # Step 2: 转换为Agent所需格式
    from utils.pdf_structure_agent import PageContent as AgentPageContent
    agent_pages = [
        AgentPageContent(page_num=p.page_num, text=p.text)
        for p in pages
    ]
    
    # Step 3: 创建并运行Agent
    if verbose:
        print("[PDF结构化] 正在创建Agent...")
    
    agent = create_pdf_structure_agent(
        uid=uid,
        max_depth=max_depth,
        api_key=api_key,
        base_url=base_url,
        model_name=model_name,
        verbose=verbose,
        outline_max_tokens=outline_max_tokens,
        section_max_tokens=section_max_tokens,
        max_parallel_sections=max_parallel_sections,
    )

    if verbose:
        print("[PDF结构化] 开始结构化分析（多 Agent 协同）...")

    result = agent.process_pages(agent_pages, paper_title=paper_title)
    
    # Step 4: 保存结果（如果指定了输出路径）
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        if verbose:
            print(f"[PDF结构化] 结果已保存到: {output_path}")
    
    return result


def pdf_to_structured_json_string(
    pdf_path: str,
    uid: str = "default",
    max_depth: int = 3,
    **kwargs
) -> str:
    """
    将PDF转换为层次化JSON字符串
    
    参数与 pdf_to_structured_json 相同
    
    Returns:
        格式化的JSON字符串
    """
    result = pdf_to_structured_json(
        pdf_path=pdf_path,
        uid=uid,
        max_depth=max_depth,
        **kwargs
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


# 命令行入口
if __name__ == "__main__":
    # import argparse
    # import tkinter as tk
    # from tkinter import filedialog
    
    # parser = argparse.ArgumentParser(description="PDF层次化结构提取")
    # parser.add_argument("--pdf", type=str, help="PDF文件路径")
    # parser.add_argument("--uid", type=str, default="default", help="用户ID")
    # parser.add_argument("--max-depth", type=int, default=3, help="最大层级深度")
    # parser.add_argument("--output", type=str, help="输出JSON文件路径")
    # parser.add_argument("--filter", type=str, nargs="+", help="过滤关键词")
    # parser.add_argument("--quiet", action="store_true", help="静默模式")
    
    # args = parser.parse_args()
    
    # # 如果没有指定PDF路径，弹出文件选择对话框
    # pdf_path = args.pdf
    # if not pdf_path:
    #     root = tk.Tk()
    #     root.withdraw()
    #     pdf_path = filedialog.askopenfilename(
    #         title="选择PDF文件",
    #         filetypes=[("PDF Files", "*.pdf")]
    #     )
    #     if not pdf_path:
    #         print("未选择文件，退出")
    #         exit(0)
    
    # python utils/pdf_to_structure.py --pdf "C:\Users\29938\Downloads\OSCC.pdf" --max-depth 5

    # 处理PDF
    # result = pdf_to_structured_json(
    #     pdf_path=pdf_path,
    #     uid=args.uid,
    #     max_depth=args.max_depth,
    #     filter_keywords=args.filter,
    #     output_path=args.output,
    #     verbose=not args.quiet
    # )
    result = pdf_to_structured_json_string(
        pdf_path='C:\\Users\\29938\\Downloads\\OSCC.pdf',
        uid='default',
        max_depth=5,
        # filter_keywords=None,
        output_path='OSCC.jsonl',
    )
    
    # 打印结果
    # if not args.output:
    print("\n" + "="*60)
    print("结构化结果:")
    print("="*60)
    print(json.dumps(result, ensure_ascii=False, indent=2))

# C:\Users\29938\anaconda3\envs\pytorch_env\python.exe -m utils.pdf_to_structure