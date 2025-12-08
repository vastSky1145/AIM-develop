import fitz
import json
import sys
import os
import re

def parse_pdf(file_path: str):
    pdf_document = fitz.open(file_path)
    for i,page in enumerate(pdf_document):
        blocks = page.get_text("dict")["blocks"]
        print("="*100)
        print(f"第{i+1}页")
        print("="*100)
        for block in blocks:
            if block["type"] == 0:
                print(block)
        if i == 5:
            break


if __name__ == '__main__':
    # 弹窗选择文件
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    # file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    pdf_file_path = "D:/研究生资料/本科生教改论文/测试.pdf"

    if pdf_file_path:
        print(f"选择的文件: {pdf_file_path}")
        parse_pdf(pdf_file_path)
    else:
        print("未选择文件")
