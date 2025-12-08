import pdfplumber
import json
import sys
import os
import re


def parse_pdf(file_path: str, y_tolerance: float = 3.0) -> list:
    """
    提取PDF文本并按坐标排序，返回每页的行列表
    
    Args:
        file_path: PDF文件路径
        y_tolerance: Y坐标容差，用于判断是否为同一行（默认3.0）
    
    Returns:
        所有页面的文本行列表
    """
    all_lines = []
    
    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            # 提取所有文字块及其坐标信息
            words = page.extract_words(
                x_tolerance=3,
                y_tolerance=3,
                keep_blank_chars=True,
                extra_attrs=['fontname', 'size']
            )
            
            if not words:
                continue
            
            # 按Y坐标排序（从上到下）
            words_sorted = sorted(words, key=lambda w: (w['top'], w['x0']))
            
            # 按行分组
            lines = group_by_line(words_sorted, y_tolerance)
            
            # 合并每行文字
            for line in lines:
                line_sorted = sorted(line, key=lambda w: w['x0'])
                line_text = ' '.join(w['text'] for w in line_sorted).strip()
                if line_text:
                    all_lines.append(line_text)
    
    return all_lines


def parse_pdf_to_json(file_path: str, y_tolerance: float = 3.0) -> dict:
    """
    解析PDF并生成层次结构的JSON
    
    Args:
        file_path: PDF文件路径
        y_tolerance: Y坐标容差
    
    Returns:
        包含层次结构的字典
    """
    lines = parse_pdf(file_path, y_tolerance)
    return build_structure(lines)


def build_structure(lines: list) -> dict:
    """
    从文本行列表构建层次结构
    
    Args:
        lines: 文本行列表
    
    Returns:
        层次结构字典
    """
    result = {
        "paper_title": "",
        "sections": []
    }
    
    # 章节编号正则模式：匹配 1, 2.1, 3.2.1 等格式
    section_pattern = re.compile(r'^(\d+(?:\.\d+)*)(?:\s+|\s*$)')
    
    # 存储所有解析出的章节
    sections = []
    current_section = None
    
    # 跳过页眉页脚等信息，提取标题
    title_found = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 第一个非空行作为标题
        if not title_found:
            result["paper_title"] = line
            title_found = True
            continue
        
        # 尝试匹配章节编号
        match = section_pattern.match(line)
        if match:
            section_num = match.group(1)
            # 获取章节标题（编号后的文字）
            title_text = line[match.end():].strip()
            
            # 如果标题为空，可能是编号和标题分开在两行
            if not title_text:
                title_text = f"章节 {section_num}"
            
            new_section = {
                "num": section_num,
                "id": f"ppt{section_num}",
                "title": title_text,
                "content": "",
                "children": []
            }
            sections.append(new_section)
            current_section = new_section
        else:
            # 非章节编号行，作为当前章节的内容
            if current_section:
                # 清理内容前缀（如 p, w 等标记）
                content_line = clean_content_line(line)
                if content_line:
                    if current_section["content"]:
                        current_section["content"] += "\n" + content_line
                    else:
                        current_section["content"] = content_line
    
    # 构建层次结构
    result["sections"] = build_hierarchy(sections)
    
    return result


def clean_content_line(line: str) -> str:
    """
    清理内容行，移除前缀标记
    
    Args:
        line: 原始文本行
    
    Returns:
        清理后的内容
    """
    # 移除开头的 p, w 等标记
    line = line.strip()
    if line.startswith(('p ', 'w ')):
        line = line[2:].strip()
    return line


def build_hierarchy(sections: list) -> list:
    """
    将扁平的章节列表构建为层次结构
    
    Args:
        sections: 扁平的章节列表，每个元素包含 num 字段（如 "1", "2.1", "3.2.1"）
    
    Returns:
        层次结构的章节列表
    """
    if not sections:
        return []
    
    root_sections = []
    section_map = {}  # 用于快速查找父章节
    
    for section in sections:
        num = section["num"]
        parts = num.split(".")
        
        # 移除 num 字段，最终输出不需要
        section_copy = {
            "id": section["id"],
            "title": section["title"],
            "content": section["content"],
            "children": section["children"]
        }
        
        if len(parts) == 1:
            # 顶级章节（如 1, 2, 3）
            root_sections.append(section_copy)
            section_map[num] = section_copy
        else:
            # 子章节，找到父章节
            parent_num = ".".join(parts[:-1])
            parent = section_map.get(parent_num)
            if parent:
                parent["children"].append(section_copy)
                section_map[num] = section_copy
            else:
                # 找不到父章节，作为顶级章节处理
                root_sections.append(section_copy)
                section_map[num] = section_copy
    
    return root_sections


def group_by_line(words: list, y_tolerance: float = 3.0) -> list:
    """
    将文字块按Y坐标分组（同一行）
    
    Args:
        words: 已按Y坐标排序的文字块列表
        y_tolerance: Y坐标容差
        
    Returns:
        按行分组的列表，每个元素是一行的文字块列表
    """
    if not words:
        return []
    
    lines = []
    current_line = [words[0]]
    current_y = words[0]['top']
    
    for word in words[1:]:
        # 如果Y坐标差距在容差范围内，视为同一行
        if abs(word['top'] - current_y) <= y_tolerance:
            current_line.append(word)
        else:
            # 开始新的一行
            lines.append(current_line)
            current_line = [word]
            current_y = word['top']
    
    # 添加最后一行
    if current_line:
        lines.append(current_line)
    
    return lines


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
        result = parse_pdf_to_json(pdf_file_path)
        
        # 输出JSON（美化格式）
        json_output = json.dumps(result, ensure_ascii=False, indent=2)
        print("\n解析结果：")
        print(json_output)
        
        # 保存到文件
        output_path = os.path.splitext(pdf_file_path)[0] + "_structure.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json_output)
        print(f"\n已保存到: {output_path}")
    else:
        print("未选择文件")




