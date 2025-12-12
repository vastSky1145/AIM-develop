import pdfplumber


def get_pdf_text_by_page(pdf_file_path):
    with pdfplumber.open(pdf_file_path) as pdf:
        texts_in_page = []
        for page in pdf.pages:
            texts_in_page.append(page.extract_text())
        return texts_in_page

def parse_pdf_to_json(pdf_file_path):
    texts_in_page = get_pdf_text_by_page(pdf_file_path)
    for page_index, text in enumerate(texts_in_page):
        print("="*100)
        print(f"第{page_index+1}页")
        print("="*100)
        print(text)


import fitz  # PyMuPDF


def extract_with_pymupdf(pdf_path):
    """
    使用 PyMuPDF 按阅读顺序提取双栏文本
    """
    doc = fitz.open(pdf_path)
    full_text = []

    for page_num in range(len(doc)):
        page = doc[page_num]

        # 获取文本块，按位置排序
        blocks = page.get_text("dict")["blocks"]

        # 按 y 坐标（垂直位置）排序
        text_blocks = []
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text_blocks.append({
                            "text": span["text"],
                            "x": span["bbox"][0],
                            "y": span["bbox"][1]
                        })

        # 按 y 坐标分组，然后在每组内按 x 坐标排序
        # 这样可以正确处理双栏布局
        page_width = page.rect.width
        mid_point = page_width / 2

        # 分别收集左右栏的文本
        left_blocks = [b for b in text_blocks if b["x"] < mid_point]
        right_blocks = [b for b in text_blocks if b["x"] >= mid_point]

        # 按 y 坐标排序
        left_blocks.sort(key=lambda x: x["y"])
        right_blocks.sort(key=lambda x: x["y"])

        # 合并文本
        left_text = " ".join([b["text"] for b in left_blocks])
        right_text = " ".join([b["text"] for b in right_blocks])

        full_text.append(left_text)
        full_text.append(right_text)

    doc.close()
    return "\n\n".join(full_text)

if __name__ == '__main__':
    # 弹窗选择文件
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    pdf_file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    # pdf_file_path = "D:/研究生资料/本科生教改论文/测试.pdf"

    if pdf_file_path:
        print(f"选择的文件: {pdf_file_path}")

        # 解析PDF并生成JSON
        res = extract_with_pymupdf(pdf_file_path)
        print(res)
    else:
        print("未选择文件")




