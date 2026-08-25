from openai import OpenAI
import requests
from PyPDF2 import PdfReader
import re

import tkinter as tk
from tkinter import filedialog


llm = OpenAI(
    api_key="sk-sZi4nNPwuQhqBNonGrHL0yATSQKHOi88AJiiGFQfdG5xoD1l",
    base_url="https://api.chat.csu.edu.cn/v1"
)

# def call_llm_sync(prompt: str) -> str:
#     """
#     同步调用LLM（在线程池中执行）
#     """
#     try:
#         for model in llm.models.list():
#             print(f"    -{model.id}")
#         completion = llm.chat.completions.create(
#             # model="gemini-2.5-flash-preview-05-20",
#             model="deepseek-v3",
#             reasoning_effort="low",
#             messages=[
#                 {"role": "system", "content": "You are a helpful assistant."},
#                 {"role": "user", "content": prompt}
#             ]
#         )
#         return completion.choices[0].message.content
#     except Exception as e:
#         raise Exception(f"调用LLM失败: {str(e)}")

def call_llm_sync(prompt: str, enable_reasoning: bool = False) -> tuple:
    """
    同步调用LLM（在线程池中执行）
    :param prompt: 提示词
    :param enable_reasoning: 是否返回深度思考内容，默认为False
    """
    try:
        # 打印模型列表（保留原有逻辑，实际生产中建议注释掉以减少干扰）
        for model in llm.models.list():
            print(f"    -{model.id}")
            
        completion = llm.chat.completions.create(
            # model="gemini-2.5-flash-preview-05-20",
            # model="deepseek-v4",
            model="DeepSeek-V4-Flash",
            reasoning_effort="low",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            extra_body={"chat_template_kwargs": {"thinking": enable_reasoning}}
        )
        
        if completion: #若completion不为空
            if enable_reasoning:
                return completion.choices[0].message.reasoning_content, completion.choices[0].message.content
            else:
                return None, completion.choices[0].message.content
        else:
            raise Exception("调用LLM失败: completion为空")
        
        
    except Exception as e:
        raise Exception(f"调用LLM失败: {str(e)}")

# def upload_file(file_path: str) -> str:
#     """
#     上传文件
#     :param file_path: 本地文件路径
#     :return: 上传后的文件ID
#     """
#     try:
#         with open(file_path, "rb") as f:
#             response = llm.files.create(
#                 file=f,
#                 # purpose 通常为 "assistants" 或 "file-extract"，具体取决于API提供商的要求
#                 purpose="assistants",
#
#             )
#         return response.id
#     except Exception as e:
#         raise Exception(f"上传文件失败: {str(e)}")

def extract_text_from_pdf(pdf_path):
    """支持中英文PDF提取，保留段落结构"""
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PdfReader(f)
        for page in reader.pages:
            # 优化换行处理
            page_text = page.extract_text()
            print(page_text)
            # page_text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', page_text)  # 处理英文换行符
            # page_text = re.sub(r'(?<!\n)\n(?!\n)', ' ', page_text)  # 处理中文换行
            text += page_text + "\n\n"
    return text.strip()

if __name__ == '__main__':
    # res = call_llm_sync("请自我介绍",enable_reasoning=True)
    # print(res)

    # 弹窗选择文件

    # root = tk.Tk()
    # root.withdraw()
    # pdf_file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    # pdf_file_path = "D:/研究生资料/本科生教改论文/测试.pdf"
    # pdf_file_path = "D:/研究生资料/本科生教改论文/WASA_6-17.pdf"

    # if pdf_file_path:
    #     print(f"选择的文件: {pdf_file_path}")

    #     extract_text_from_pdf(pdf_file_path)
    # else:
    #     print("未选择文件")
    call_llm_sync("请自我介绍", enable_reasoning=False)