import re


def filter_paper_content(text):
    # 定义严格的保留条件（只保留符合学术正文特征的文本）

    keep_patterns = [
        r'^[A-Z][a-z].*[.,;:]$',  # 标准句子开头（首字母大写，结尾有标点）
        r'^[a-z].*[.,;:]$',  # 段落续行（首字母小写）
        r'^[(\[].*[\])]',  # 括号内的说明文字
        r'\w{3,}\s\w{3,}',  # 至少包含两个单词
        r'\d+\.\d+',  # 保留带小数点的数字

    ]

    # 定义需要删除的模式（全面覆盖）
    exclude_patterns = [
        # 作者和机构信息
        r'^#.*',  # 主标题
       # r'^\S+\s+\S+\s*\{.*\}',  # 作者行（含特殊符号）
        r'^\^?\w\s.*\b(University|School|College)\b',  # 机构行
        r'^\w+@\w+\.\w+',  # 邮箱
        r'^References$',  # 参考文献标题
        r'^CRediT authorship contribution',  # 作者贡献声明
        r'^Declaration of competing',  # 利益冲突声明
        r'^Acknowledgements',  # 致谢
        r'^E-mail addresses:',  # 作者邮箱
        r'^\* Corresponding author\.',  # 通讯作者声明
        # 图片和表格
        r'\.jpg$|\.png$',  # 图片引用
        r'^Fig\.\s*\d+',  # 图片标题
        r'^Table\s*\d+',  # 表格标题
        r'^\|\s*.+\s*\|',  # 表格行（含|符号）
        r'^\+-{3,}\+',  # 表格边框

        # 章节标题
        r'^\d+\.\s+\w+',  # 主章节
        r'^\d+\.\d+\.?\s+\w+',  # 子章节
        r'^[A-Z]{2,}\s+[A-Z]{2,}',  # 全大写标题

        # 技术性内容
        r'^\[[\d,]+\]',  # 参考文献引用
        r'^References$',  # 参考文献标题
        r'^CRediT\b',  # 作者贡献声明
        #r'^[A-Za-z]+\s[A-Za-z]+(\s[A-Za-z]+)*,\s[A-Za-z]+',  # 可能的作者名格式
        r'^[A-Za-z]+\s[A-Za-z]+\s\${.*}\$',  # 作者行（如 "Yuhong Xie ${}^{a}$"）
        # 特殊格式
        r'^[-=*]{3,}',  # 分割线
        r'^\s*$',  # 空行
        #r'^\S+:\s*\S+',  # 键值对（如 Keywords: xxx）
    ]

     #1. 删除所有XML/HTML表格标签（包括跨行结构）
    text = re.sub(r'<table[^>]*>[\s\S]*?</table>', '', text)  # 完整表格
    text = re.sub(r'<tr[^>]*>|</tr>', '', text)  # 行标签
    text = re.sub(r'<td[^>]*>|</td>', '', text)  # 单元格
    text = re.sub(r'\b(rowspan|colspan)\s*=\s*["\']?\d+["\']?', '', text)  # 行列合并属性

    # 2. 删除作者行（包含${}^{a}$格式）
    #text = re.sub(
           # r'^\s*([A-Z][a-z]+ [A-Z][a-z]+)\s*\${[^}]*}\$([,&\s]*([A-Z][a-z]+ [A-Z][a-z]+)\s*\${[^}]*}\$)*\s*$', '',
           # text, flags=re.MULTILINE)

    # 3. 删除机构行（${}^{x}开头 + 机构信息）
    #text = re.sub(r'^\s*\${[^}]*}\s*[A-Z][^\n]*\b(University|Laboratory|School|Institute)\b[^\n]*$', '', text,
                     # flags=re.MULTILINE)


    # 2. 删除机构行（精确匹配你给的格式）
    text = re.sub(
        r'^\$\{\}\^\{[a-z]\}\$ [A-Z][^\n]*(University|China)[^\n]*\d{6}[^\n]*$\n?',
        '',
        text,
        flags=re.MULTILINE
    )

    # 4. 删除关键词块（从Keywords:到第一个空行）
    text = re.sub(r'Keywords:[^\n]*(\n\s*[A-Za-z][^\n]*)*\n\s*\n', '\n', text)
    #author_pattern = r'^([A-Z][a-z]+ [A-Z][a-z]+ \$\{\}\^\{[a-z, *]+\}\$)(, [A-Z][a-z]+ [A-Z][a-z]+ \$\{\}\^\{[a-z, *]+\}\$)*\s*$'
   # text = re.sub(author_pattern, '', text, flags=re.MULTILINE)
    #text = re.sub(r'<[^>]+>', '', text)

    # 5. 清理残留格式
    #text = re.sub(r'\${[^}]*}', '', text)  # 删除所有${}标记
    #text = re.sub(r'\n{3,}', '\n\n', text)  # 合并多余空行
    #text = text.strip()
    lines = text.split('\n')
    filtered_lines = []

    current_paragraph = []

    for line in lines:
        line = line.strip()

        # 判断是否应该排除
        should_exclude = any(re.search(pattern, line) for pattern in exclude_patterns)

        # 判断是否应该保留
        should_keep = any(re.search(pattern, line) for pattern in keep_patterns)

        # 特殊处理：合并段落
        if should_keep and not should_exclude:
            current_paragraph.append(line)
        elif current_paragraph:
            # 遇到非正文行时，将当前段落存入结果
            filtered_lines.append(" ".join(current_paragraph))
            current_paragraph = []

    # 添加最后一个段落
    if current_paragraph:
        filtered_lines.append(" ".join(current_paragraph))



    return '\n\n'.join(filtered_lines)


if __name__ == "__main__":
    input_file = "24-A-Short video preloading via domain knowledge assisted deep reinforcement.txt"
    output_file = "strict_pure_content.txt"

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            paper_text = f.read()

        pure_content = filter_paper_content(paper_text)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(pure_content)
        sds=pure_content.split('\n\n')
        print("=== 过滤结果统计 ===")
        print(f"原始文件行数: {len(paper_text.splitlines())}")
        print(f"过滤后段落数: {len(sds)}")
        print(f"保存路径: {output_file}")

    except Exception as e:
        print(f"处理失败: {str(e)}")
