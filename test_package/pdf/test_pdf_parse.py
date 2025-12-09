import pdfplumber
import json
import sys
import os
import re


def get_pdf_text_by_page(pdf_file_path):
    """按页提取PDF文本"""
    with pdfplumber.open(pdf_file_path) as pdf:
        texts_in_page = []
        for page in pdf.pages:
            texts_in_page.append(page.extract_text())
        return texts_in_page


def parse_page_content(text, is_first_content_page=False):
    """
    解析单页内容，提取章节和内容
    
    Args:
        text: 页面文本
        is_first_content_page: 是否是第一个内容页（可能包含大纲）
    
    Returns:
        dict: {
            'level1': {'num': '2', 'title': 'Python编程教学现状和存在的问题'},
            'subsections': [{'num': '2.1', 'title': '...', 'content': '...'}],
            'content_lines': ['内容1', '内容2']
        }
    """
    if not text:
        return None
    
    lines = text.splitlines()
    result = {
        'level1': None,
        'subsections': [],
        'content_lines': []
    }
    
    # 正则模式
    # 一级标题编号：独立的数字行
    level1_num_pattern = re.compile(r'^(\d+)$')
    # 子章节：p 开头 + 编号 + 标题（如 "p 2.1 教学供给..."）
    subsection_pattern = re.compile(r'^p\s+(\d+(?:\.\d+)+)\s*(.*)$')
    # 内容行：w 开头
    content_pattern = re.compile(r'^w\s+(.+)$')
    # 普通段落：p 开头但不是子章节编号
    paragraph_pattern = re.compile(r'^p\s+(?!\d+\.\d)(.+)$')
    
    # 解析一级标题（页面顶部）
    level1_title = None
    level1_num = None
    
    for i, line in enumerate(lines[:5]):  # 只检查前5行
        line = line.strip()
        if not line:
            continue
        
        # 检查是否是一级标题编号行
        num_match = level1_num_pattern.match(line)
        if num_match:
            level1_num = num_match.group(1)
            # 标题可能在上一行或下一行
            if i > 0 and lines[i-1].strip():
                level1_title = lines[i-1].strip()
            elif i < len(lines) - 1 and lines[i+1].strip():
                level1_title = lines[i+1].strip()
            break
        
        # 检查是否是 "数字 标题" 格式（如 "2 Python编程教学..."）
        combined_match = re.match(r'^(\d+)\s+(.+)$', line)
        if combined_match:
            level1_num = combined_match.group(1)
            level1_title = combined_match.group(2)
            break
        
        # 检查是否是 "数字.标题" 格式（如 "2.Background"）
        dot_match = re.match(r'^(\d+)\.(.+)$', line)
        if dot_match:
            level1_num = dot_match.group(1)
            level1_title = dot_match.group(2)
            break
    
    if level1_num:
        result['level1'] = {
            'num': level1_num,
            'title': level1_title or f'章节 {level1_num}'
        }
    
    # 解析子章节和内容
    current_subsection = None
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
        
        # 检查子章节
        sub_match = subsection_pattern.match(line_stripped)
        if sub_match:
            # 保存之前的子章节
            if current_subsection:
                result['subsections'].append(current_subsection)
            
            current_subsection = {
                'num': sub_match.group(1),
                'title': sub_match.group(2).strip() if sub_match.group(2) else '',
                'content': ''
            }
            continue
        
        # 检查内容行
        content_match = content_pattern.match(line_stripped)
        if content_match:
            content_text = content_match.group(1).strip()
            if current_subsection:
                if current_subsection['content']:
                    current_subsection['content'] += '\n' + content_text
                else:
                    current_subsection['content'] = content_text
            else:
                result['content_lines'].append(content_text)
            continue
        
        # 检查普通段落（p 开头但不是编号）
        para_match = paragraph_pattern.match(line_stripped)
        if para_match:
            content_text = para_match.group(1).strip()
            if current_subsection:
                if current_subsection['content']:
                    current_subsection['content'] += '\n' + content_text
                else:
                    current_subsection['content'] = content_text
            else:
                result['content_lines'].append(content_text)
    
    # 保存最后一个子章节
    if current_subsection:
        result['subsections'].append(current_subsection)
    
    return result


def build_hierarchy(sections_flat: list) -> list:
    """
    将扁平的章节列表构建为层次结构
    
    Args:
        sections_flat: 扁平的章节列表，每个元素包含 'num' 字段（如 "1", "2.1", "3.2.1"）
    
    Returns:
        层次结构的章节列表
    """
    if not sections_flat:
        return []
    
    root_sections = []
    section_map = {}  # 用于快速查找章节：{编号: node}
    
    for section in sections_flat:
        num = section['num']
        parts = num.split('.')
        level = len(parts)
        
        # 创建节点（不包含 num 字段）
        node = {
            'title': section.get('title', ''),
            'content': section.get('content', ''),
            'children': []
        }
        
        # 检查是否已存在同编号的章节（需要合并）
        existing = section_map.get(num)
        if existing:
            # 合并内容
            if section.get('title') and not existing['title']:
                existing['title'] = section['title']
            if section.get('content'):
                if existing['content']:
                    # 避免重复内容
                    if section['content'] not in existing['content']:
                        existing['content'] += '\n' + section['content']
                else:
                    existing['content'] = section['content']
            continue
        
        if level == 1:
            # 顶级章节
            root_sections.append(node)
            section_map[num] = node
        else:
            # 子章节，找到父章节
            parent_num = '.'.join(parts[:-1])
            parent = section_map.get(parent_num)
            
            if parent:
                parent['children'].append(node)
                section_map[num] = node
            else:
                # 父章节不存在，创建占位父章节
                # 递归创建所有缺失的父章节
                current_num = parts[0]
                if current_num not in section_map:
                    parent_node = {'title': '', 'content': '', 'children': []}
                    root_sections.append(parent_node)
                    section_map[current_num] = parent_node
                
                # 创建中间层级
                for i in range(1, level - 1):
                    current_num = '.'.join(parts[:i+1])
                    if current_num not in section_map:
                        intermediate_node = {'title': '', 'content': '', 'children': []}
                        parent_num = '.'.join(parts[:i])
                        section_map[parent_num]['children'].append(intermediate_node)
                        section_map[current_num] = intermediate_node
                
                # 添加当前节点到父节点
                parent_num = '.'.join(parts[:-1])
                section_map[parent_num]['children'].append(node)
                section_map[num] = node
    
    return root_sections


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


def parse_pdf_to_json(pdf_file_path: str) -> dict:
    """
    解析PDF并生成层次结构的JSON
    
    Args:
        pdf_file_path: PDF文件路径
    
    Returns:
        包含层次结构的字典
    """
    texts_in_page = get_pdf_text_by_page(pdf_file_path)
    
    if not texts_in_page:
        return {"paper_title": "", "sections": []}
    
    # 第一页作为论文标题
    paper_title = texts_in_page[0].strip() if texts_in_page[0] else ""
    
    # 收集所有章节（扁平结构）
    sections_flat = []
    
    # 从第二页开始解析
    for page_index, text in enumerate(texts_in_page[1:], start=1):
        if not text:
            continue
        
        page_data = parse_page_content(text, is_first_content_page=(page_index == 1))
        
        if not page_data:
            continue
        
        # 处理一级标题
        if page_data['level1']:
            level1 = page_data['level1']
            sections_flat.append({
                'num': level1['num'],
                'title': level1['title'],
                'content': '\n'.join(page_data['content_lines']) if page_data['content_lines'] else ''
            })
        
        # 处理子章节
        for subsection in page_data['subsections']:
            sections_flat.append({
                'num': subsection['num'],
                'title': subsection['title'],
                'content': subsection['content']
            })
    
    # 构建层次结构
    sections = build_hierarchy(sections_flat)
    
    # 分配ID
    assign_ids(sections)
    
    return {
        "paper_title": paper_title,
        "sections": sections
    }


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
        result = parse_pdf_to_json(pdf_file_path)
        
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




