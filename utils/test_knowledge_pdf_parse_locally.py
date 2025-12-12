import pdfplumber
from PyPDF2 import PdfFileReader
import json
import sys
import os
import re


def get_knowledge_pdf_text_by_page_in_plumber(pdf_file_path):
    """按页提取PDF文本"""
    with pdfplumber.open(pdf_file_path) as pdf:
        texts_in_page = []
        for page in pdf.pages:
            texts_in_page.append(page.extract_text())
        return texts_in_page

def get_knowledge_pdf_text_by_page_in_pypdf2(pdf_file_path):#推荐优先使用，识别更准，但会因编码格式报错
    """按页提取PDF文本"""
    with open(pdf_file_path, 'rb') as file:
        reader = PdfReader(file)
        texts_in_page = []
        for page in reader.pages:
            texts_in_page.append(page.extract_text())
        return texts_in_page



if __name__ == '__main__':
    # 弹窗选择文件
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    pdf_file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    # pdf_file_path = "D:/研究生资料/本科生教改论文/测试.pdf"
    # pdf_file_path = "D:/研究生资料/本科生教改论文/本科生教改-修改稿 - 12.6.pdf"

    if pdf_file_path:
        print(f"选择的文件: {pdf_file_path}")
        
        # 解析PDF并生成JSON
        result = parse_pdf_to_json_locally(pdf_file_path)
        
        # 输出JSON（美化格式）
        json_output = json.dumps(result, ensure_ascii=False, indent=2)
        print("\n解析结果：")
        print(json_output)
        
        # 保存到文件
        # output_path = os.path.splitext(pdf_file_path)[0] + "_structure.json"
        # with open(output_path, 'w', encoding='utf-8') as f:
        #     f.write(json_output)
        # print(f"\n已保存到: {output_path}")
    else:
        print("未选择文件")




