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
    从文本行列表构建层次结构（使用栈结构，支持跨页合并）
    
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
    # 支持编号后直接跟标题或单独一行编号
    section_pattern = re.compile(r'^(\d+(?:\.\d+)*)(?:\s+(.+))?$')
    
    # 用于追踪层级的栈：[(level, node), ...]
    stack = []
    # 用于快速查找已存在的章节：{编号: node}
    section_map = {}
    # 内容缓冲区
    content_buffer = []
    # 当前节点
    current_node = None
    # 标题是否已找到
    title_found = False
    
    def get_level(section_num: str) -> int:
        """根据编号获取层级，如 '2.1.3' -> 3"""
        return len(section_num.split('.'))
    
    def flush_content():
        """将缓冲区内容写入当前节点"""
        nonlocal content_buffer, current_node
        if current_node is not None and content_buffer:
            txt = '\n'.join(content_buffer).strip()
            if txt:
                # 避免重复添加相同内容
                if txt not in current_node.get('content', ''):
                    if current_node['content']:
                        current_node['content'] += '\n' + txt
                    else:
                        current_node['content'] = txt
        content_buffer = []
    
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
            title_text = match.group(2).strip() if match.group(2) else ""
            level = get_level(section_num)
            
            # 先将缓冲区内容写入上一个节点
            flush_content()
            
            # 检查是否已存在同编号的章节
            existing = section_map.get(section_num)
            
            if existing:
                # 已存在同编号章节，合并到该章节
                current_node = existing
                # 如果新行有标题且旧节点标题是占位符，更新标题
                if title_text and existing['title'].startswith('章节 '):
                    existing['title'] = title_text
                # 弹出栈直到找到正确的父级
                while stack and stack[-1][0] >= level:
                    stack.pop()
                stack.append((level, existing))
            else:
                # 创建新章节
                if not title_text:
                    title_text = f"章节 {section_num}"
                
                new_node = {
                    'title': title_text,
                    'content': '',
                    'children': []
                }
                
                # 确定父节点
                if level == 1:
                    # 顶级章节，直接加入 sections
                    parent_list = result['sections']
                else:
                    # 弹出栈直到找到正确的父级（层级小于当前层级）
                    while stack and stack[-1][0] >= level:
                        stack.pop()
                    
                    if stack:
                        parent_list = stack[-1][1]['children']
                    else:
                        # 找不到父节点，作为顶级处理
                        parent_list = result['sections']
                
                parent_list.append(new_node)
                section_map[section_num] = new_node
                stack.append((level, new_node))
                current_node = new_node
        else:
            # 非章节编号行，清理后加入缓冲区
            content_line = clean_content_line(line)
            if content_line:
                content_buffer.append(content_line)
    
    # 处理最后的缓冲区内容
    flush_content()
    
    # 分配层次化 ID
    assign_ids(result['sections'])
    
    return result


def assign_ids(nodes: list, parent_id: str = None):
    """
    为节点分配层次化ID
    
    Args:
        nodes: 节点列表
        parent_id: 父节点ID
    """
    for idx, node in enumerate(nodes, start=1):
        if parent_id:
            node['id'] = f"{parent_id}.{idx}"
        else:
            node['id'] = f"ppt{idx}"
        if node.get('children'):
            assign_ids(node['children'], node['id'])


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


######################################
# def get_pdf_text_by_page(pdf_file_path):
#     with pdfplumber.open(pdf_file_path) as pdf:
#         texts_in_page = []
#         for page in pdf.pages:
#             texts_in_page.append(page.extract_text())
#         return texts_in_page

# def parse_pdf_to_json(pdf_file_path):
#     texts_in_page = get_pdf_text_by_page(pdf_file_path)
#     for page_index, text in enumerate(texts_in_page):
#         print("="*100)
#         print(f"第{page_index+1}页")
#         print("="*100)
#         print(text)

#     #第一页是论文标题
#     paper_title = texts_in_page[0]
#     print("="*100)
#     print(paper_title)

#     #第二页起是正文
#     #每页最上面两行/或1行是一级标题
#     #对每页提取一级标题
#     for page_index, text in enumerate(texts_in_page):
#         if page_index == 0:
#             continue
#         #每页最上面两行/或1行是一级标题
#         lines = text.splitlines()
#         if len(lines) >= 2:
#             #如果第一行有中文
#             if re.search(r'[\u4e00-\u9fa5]', lines[0]):
#                 #打印这一行+下一行
#                 print(lines[1] + lines[0] )
#                 continue
#             else:
#                 print(lines[0])
#                 continue
#         else:
#             print(lines[0])
#             continue
    return None


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




