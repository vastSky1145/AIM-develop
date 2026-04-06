import json
import os
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

# 导入你原有的解析工具和数据库类
from utils.test_pdf_parse_locally import parse_pdf_to_json_locally
from mongodb import PaperDatabase


def select_file():
    """弹出文件选择对话框"""
    # 初始化 tkinter，并隐藏主窗口
    root = tk.Tk()
    root.withdraw()

    # 强制让窗口置顶（防止弹窗在编辑器后面找不到）
    root.attributes('-topmost', True)

    # 弹出选择文件界面
    file_path = filedialog.askopenfilename(
        title="选择要解析的 PDF 文件",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
    )

    # 销毁临时窗口
    root.destroy()
    return file_path


def test_pdf_parsing(file_path, user_id):
    """(保留之前的解析逻辑)"""
    if not file_path:
        print("操作取消：未选择任何文件")
        return

    print(f"--- 开始处理文件: {file_path} ---")

    # ... 原有的解析逻辑代码 (同上一回复) ...
    try:
        json_content = parse_pdf_to_json_locally(file_path)
        # 假设这里返回的是解析后的内容
        print("解析成功！")
        return json_content
    except Exception as e:
        print(f"解析出错: {e}")


# --- 测试执行部分 ---
if __name__ == "__main__":
    # 1. 自动弹出界面选择文件
    # selected_path = select_file()
    selected_path = "C:/Users/29938/Downloads/OSCC.pdf"
    print(selected_path)

    if selected_path:
        # 2. 调用测试函数
        TEST_USER_ID = "test_user_001"
        res = test_pdf_parsing(selected_path, TEST_USER_ID)
        print(res)
    else:
        print("未选择文件，程序退出。")