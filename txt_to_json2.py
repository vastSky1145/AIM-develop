import re
import json
from json_to_txt import print_hierarchy
# MMD to JSON parser with custom heading levels, parent merging, and hierarchical IDs
# from trans_to_json import txt_to_json
import string

def parse_mmd_to_json(mmd_text,uid):
    # Regex for each level with strict start and whitespace requirements
    level_patterns = [
        #(1, re.compile(r'.*(?:##\s*)?(\d+)\.\s*(.+)')),
        ##(1, re.compile(r'.*(?:##\s*)?(?:Chapter\s*)?(\d+)\.?\s*(.+)')),
        #(1, re.compile(r'.*(?:##\s*)?(?:Chapter\s*)?(\d+)\.?\s+(.+)')),
        #(1, re.compile(r'.*(?:##|#)\s*(\d+)\s+(.+)')),  # 一级：# 或 ## 后接数字+空格+标题
        ##(2, re.compile(r'^\*\s*(\d+\.\d+)(?!\.\d)\s+(.+)')),
        #(2, re.compile(r'.*[*#]?\s*(\d+\.\d+)\s+(.+)')),  # 二级：可选 * 或 #，数字.数字
        ##(3, re.compile(r'^\*\s*(\d+\.\d+\.\d+)\s+(.+)')),
        #(3, re.compile(r'.*[*]?\s*(\d+\.\d+\.\d+)\s+(.+)')),  # 三级：数字.数字.数字
        #(4, re.compile(r'.*[*]?\s*(\d+)\)\s+(.+)')),  # 四级：数字)
        ##(4, re.compile(r'^\*?\s*(\d+)\)\s*(.+)')),
        ##(5, re.compile(r'^\*\s*(?:\*+)?\(\s*(\d+)\s*\)\s*(.+)')),
        #(5, re.compile(r'.*[*]?\s*\((\d+)\)\s+(.+)')),  # 五级：(数字)
        #(5, re.compile(r'^\*\s*(?:\*+)?\(\s*(\d+)\s*\)\s*(.+)$')),  # 五级
        #(5, re.compile(r'^[\*\-]?\s*\(\s*(\d+)\s*\)\s+(.+)')),
        (5, re.compile(r'^(?:[\*\-\s]*)\(\s*(\d+)\s*\)\s*(.+)')),
       # (4, re.compile(
   # r'^\s*'                          # 行首空白
   # r'(?:#{2,}\s*|[\*\-]\s*)?'       # 可选前缀
  # r'(\d+\.\d+\.\d+\.\d+)'          # 精确匹配四级编号
   # r'\.?\s*'
  #  r'(.+)$'
    #    )),#re.compile(r'^(?:[\*\-]\s*)?(\d+)\)\s*(.+)')),
#
        (4, re.compile(
            r'^\s*'  # 行首空白
            r'(?:#{2,}\s*|[\*\-]\s*)?'  # 可选 Markdown 风格前缀，如 ##、*、-
            r'(?:§\s*)?'  # 可选的 "§" 符号及其后空格
            r'(\d+\.\d+\.\d+\.\d+)'  # 四级编号，如 2.2.1.1
            r'\.?\s*'  # 可选的句点和空格
            r'(.+)$'  # 标题文本
        )),
        (3, re.compile(
            r'^\s*'  # 行首可有空白
            r'(?:(?:#{2,}\s*)|(?:[\*\-]\s*))?'                                                   # 可选 “##…”(2个以上#)+空白 或 “* ” 或 “- ”
            r'(\d+\.\d+\.\d+)'                                                                 # 捕获 “数字.数字.数字”
            r'\.?\s*'                                                                    # 可选一个 “.”，再允许零个或多个空白
            r'(.+)$'
        )),
        (2,

         re.compile(
             r'^\s*'
             r'(?:[-\*\#]{1,3}\s*)?'  # 可选 "-", "*", "##", "###"
             r'(?:[☐§]\s*)?'  # 可选特殊符号
             r'(?:\d+\s+)?'  # 可选整数编号（如 "1 "）
             r'(\d+\.\d+)'  # 捕获“数字.数字”
             r'(?!\.\d)'  # 确保后面不是 .数字（避免 2.2.1）
             r'\s*'
             r'(.+)$'  # 捕获标题
         )
         ),
        (1, re.compile(
            r'^\s*'                                                                      # 行首可有空白
            r'(?:(?:##)(?!#)\s*)?'                                                            # 可选 “## ”，但不匹配 “###”
            r'(?:Chapter\s*)?'                                                            # 可选 “Chapter ”
            r'(\d+)'                                                                       # 捕获章节号
            r'(?:\.(?!\d)\s*|\s+)'                                                          # 必须跟 “.”（后面不能是数字）或 空格
            r'(.+)$'                                                                         # 接着才是标题内容
        )),

        # re.compile(
           # r'^\s*'  # 行首可有空白
           # r'(?:'  # 可选前缀：
           # r'\*\s*|'  # "* 2.2"
           # r'#{3}\s*|'  # "### 2.2"
           # r'##\s*'  # "## "
           # r')?'
           # r'(?:[☐§]\s*)?'  # 可选 “☐ ” 或 “§ ”
           # r'(?:\d+\s+)?'  # 新增：可选的 “1 ”（顶级编号）
           # r'(\d+\.\d+)'  # 捕获主干 “数字.数字”
          #  r'(?!\.\d)'  # 确保不是 “数字.数字.数字”
          #  r'\s*'  # 数字和标题之间可有可无空格
         #   r'(.+)$'
        #)
        #(2, re.compile(
          #  r'^\s*'  # 行首可有空白
          #  r'(?:'  # 可选前缀
          #  r'\*\s*|'  # "* 2.2"
           # r'##\s*\d+\s+|'  # "## 1 4.2"
          #  r'#{3}\s*'  # "### 2.2"
          #  r')?'
          #  r'(\d+\.\d+)'  # 要捕获的“数字.数字”
          #  r'(?!\.\d)\s+'  # 确保后面不是 ".数字"（排除三级）
          #  r'(.+)$'  # 标题
       # )),
        #(3, re.compile(
           # r'^\s*'  # 允许行首空白
           # r'(?:(?:#{2,3}\s*)|(?:[\*\-]\s*))?'  # 可选“## ”或“### ”或“* ”或“- ”
           # r'(\d+\.\d+\.\d+)'  # 捕获“数字.数字.数字”
           # r'(?!\.\d)\s+'  # 确保后面不是“.n”
           # r'(.+)$'  # 标题
        #)),
       # (3, re.compile(
         #   r'^\s*'  # 允许行首空白
         #   r'(?:(?:##\s*)|(?:[\*\-]\s*))?'  # 可选 “## ” 或 “* ”、“- ”
         #   r'(\d+\.\d+\.\d+)'  # 捕获 “数字.数字.数字”
         #   r'(?!\.\d)\s+'  # 确保后面不是 更多 .数字
         #   r'(.+)$'  # 标题
       # )),
        #(2, re.compile(r'^(?:\*\s*|##\s*\d+\s+|#{3}\s*)?(\d+\.\d+)(?!\.\d)\s+(.+)')),
       # (2, re.compile(
          #  r'^\s*'  # 允许行首空白
          #  r'(?:'
          #  r'\*\s*|'  # "* 2.2"
          #  r'##\s*\d+\s+|'  # "## 1 4.2"
          #  r'#{3}\s*'  # "### 2.2"
          #  r')?'
          #  r'(\d+\.\d+)'  # 捕获 “数字.数字”
          #  r'(?!\.\d)\s+'  # 确保不是 “数字.数字.数字”
          #  r'(.+)$'  # 标题
       # )),
        # 一级目录

       # (2, re.compile(
         #   r'^(?:'
         #   r'\*\s*|'  # "* 2.2"
         #   r'##\s*\d+\s+|'  # "## 1 4.2"
         #   r'#{3}\s*'  # "### 2.2"
         #   r')?'
        #    r'(\d+\.\d+)'  # 主干“数字.数字”
        #    r'(?!\.\d)\s+'  # 确保不是三级（".n"）
        #    r'(.+)$'  # 标题
       # )),
      #  (1, re.compile(
       #     r'^'
       #     r'(?:(?:##)(?!#)\s*)?'  # 可选 "## "，但不是 "###"
       #     r'(?:Chapter\s*)?'  # 可选 "Chapter "
       #     r'(\d+)\.?\s+'  # 捕获“数字.”
        #    r'(?!\d+\.\d)'  # 如果后面是“数字.数字”就不匹配一级
       #     r'(.+)'  # 标题
       #    r'$'
       # )),
       # (1, re.compile(
          #  r'^(?:(?:##)(?!#)\s*)?'  # 可选 "## "
          #  r'(?:Chapter\s*)?'  # 可选 "Chapter "
          #  r'(\d+)\.?\s+'  # 编号 + 点号(可选) + 至少一个空格
          #  r'(?!(?:\d+\.\d))'  # 后面**不能**是 数字.数字 开头
          #  r'(.+)$'  # 标题至少一个字符
        #)),
       # (2, re.compile(r'^(?:\*\s*|##\s*\d+\s+|#{3}\s*)?(\d+\.\d+)(?!\.\d)\s+(.+)')),
        #(1, re.compile(
        #    r'^(?:(?:##)(?!#)\s*)?'  # 可选 "## "
        #    r'(?:Chapter\s*)?'  # 可选 "Chapter "
         #   r'(\d+)\.?\s+'  # 编号 + 点号(可选) + 至少一个空格
        #    r'(?!(?:\d+\.\d))'  # 后面**不能**是 数字.数字 开头
        #    r'(.+)$'  # 标题至少一个字符
       # )),


       # (2, re.compile(r'^(?:\*\s*|##\s*\d+\s+|#{3}\s*)?(\d+\.\d+)(?!\.\d)\s+(.+)')),
        #(1, re.compile(
           #     r'^(?:(?:##)(?!#)\s*)?'  # 可选 “## ” 前缀
          #  r'(?:Chapter\s*)?'  # 可选 “Chapter ” 前缀
          #  r'(\d+)\.?\s+'  # 编号 + 点号（可选）+ 至少一个空格
          #  r'(.+)$'  # 标题至少一个字符
          #  )),
        #(1, re.compile(
            # r'^(?:(?:##)(?!#)\s*)?'
            # r'(?:Chapter\s*)?'
            # r'(\d+)\.?\s*'
            # r'(.*)$')),

       # (1, re.compile(r'^##\s+(\d+)\s+(.+)')),            # Level 1: ## <number> <Title>
       # (2, re.compile(r'^[#*]\s+(\d+\.\d+)\s+(.+)')),   # Level 2: * or # <num.num> <Title>
       # (3, re.compile(r'^\*\s+(\d+\.\d+\.\d+)\s+(.+)')),  # Level 3: * <num.num.num> <Title>
       # (4, re.compile(r'^\*\s+(\d+)\)\s+(.+)')),        # Level 4: * <number>) <Title>
       # (5, re.compile(r'^\*\s+\((\d+)\)\s+(.+)')),     # Level 5: * (<number>) <Title>
    ]
    lines = mmd_text.splitlines()



    # Step 1: 提取论文 title（从 /////// 到第一个目录前）
    #title_match = re.search(r"///////\s*(.*?)\n(?:\s*(?:\d+\s|#))", lines, re.DOTALL)
    #print("tit",title_match)

    #paper = {'paper_title': lines[2], 'uid':uid,'sections': []}

    # 初始化paper结构
    paper = {'paper_title': '', 'uid': uid, 'sections': []}
    stack = []
    content_buffer = []
    current_node = None

    # 提取第一个匹配目录前的标题区域
    first_match_line_idx = None
    lines_after_title = []
    title_lines = []

    # Step 1: 遍历找到第一个匹配目录的行号
    for idx, line in enumerate(lines):
        stripped = line.strip()
        for lvl, pat in sorted(level_patterns, key=lambda x: x[0], reverse=True):
            if pat.match(stripped):
                first_match_line_idx = idx
                break
        if first_match_line_idx is not None:
            break

    # Step 2: 提取从 //////// 开始到第一个目录之间的纯文本，作为 title
    #title_started = False
    #for i in range(first_match_line_idx):
     #   line = lines[i].strip()
       # if not title_started and line.startswith("////"):
        #    title_started = True
      #      continue
      #  if title_started and line:
      #      title_lines.append(line)
    #title_lines = []
    title_lines = []
    if lines and lines[0].strip() and not re.match(r'^(//+|#+|\s+)', lines[0]):
        # 文件以正文字符开始：抓取第一个目录前所有非空行作为标题
        for i in range(first_match_line_idx):
            line = lines[i].strip()
            if line:
                title_lines.append(line)
    else:
        for i in range(min(first_match_line_idx, 5)):  # 限制最多前10行作为候选
            line = lines[i].strip()
            if not line:
                continue
            if re.match(r'^(//+|#+|\s+)', line):  # 以 //、# 或空格开头
                if any(c.isalpha() for c in line):  # 至少含有一个英文字母
                    clean_line = re.sub(r'^(//+|#+|\s+)', '', line)  # 去除开头标记
                    title_lines.append(clean_line)

    # 组合标题
    if title_lines:
        paper['paper_title'] = ' '.join(title_lines).strip()
   # if title_lines:
      #  paper['paper_title'] = ' '.join(title_lines).strip()

    #print("cccc",lines[2])
    def flush_content():
        nonlocal content_buffer, current_node
        if current_node is not None:
            txt = '\n'.join(content_buffer).strip()
            if txt:
                current_node.setdefault('content', '')
                if txt not in current_node['content']:#new
                    if current_node['content']:
                        current_node['content'] += '\n'
                    current_node['content'] += txt
        content_buffer = []

    for line in lines:
        stripped = line.strip()
        matched = False
        # 子目录优先：倒序遍历 level_patterns
        for lvl, pat in sorted(level_patterns, key=lambda x: x[0], reverse=True):
        #for lvl, pat in level_patterns:
            m = pat.match(stripped)
            #print("lvl",lvl)
            #print("m", m)
            #print("line", line)
            if m:
                matched = True
                flush_content()
                num, title = m.groups()
                node = {'title': title.strip(), 'content': '', 'children': []}
                # Determine parent list based on level
                if lvl == 1:
                    parent_list = paper['sections']
                else:
                    # Pop stack until parent of lower level is on top
                    while stack and stack[-1][0] >= lvl:
                        stack.pop()
                    parent_list = stack[-1][1]['children'] if stack else paper['sections']
                # Merge identical titles under same parent
                #existing = next((n for n in parent_list if n['title'] == node['title']), None)
                key = (title.strip(), lvl)
                existing = next((n for n in parent_list if n['title'] == key[0]), None)

                if existing:
                    node = existing
                else:
                    parent_list.append(node)

                stack.append((lvl, node))
                current_node = node
                break
        if not matched:
            content_buffer.append(line)
    flush_content()

    # Extract paper title from first bold line (**Title**)
    if lines:
        m = re.match(r'^\*\*(.+)\*\*', lines[0])
        if m:
            paper['paper_title'] = m.group(1).strip()
            print("kill",m.group(1).strip())


    # Assign hierarchical IDs: ppt1, ppt1.1, ppt1.1.1, ...
    def assign_ids(nodes, parent_id=None):
        for idx, node in enumerate(nodes, start=1):
            if parent_id:
                node['id'] = f"{parent_id}.{idx}"
            else:
                node['id'] = f"ppt{idx}"
            if node.get('children'):
                assign_ids(node['children'], node['id'])
    assign_ids(paper['sections'])

    return paper

if __name__ == '__main__':

    fname = "E:\workflow\Output\WASA\WASA.txt"
    with open(fname, 'r', encoding='utf-8') as f:
        mmd = f.read()
    result = parse_mmd_to_json(mmd,111)
    #print("re", result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    #print(print_hierarchy(result))
    txt_content=print_hierarchy(result)
    with open("./sxs_json.json", 'w', encoding='utf-8') as f:
        json.dump( result , f, indent=2, ensure_ascii=False)

    #paper_title = txt_content.split('\n')[0].strip().rstrip('=')
    #result_json = txt_to_json(txt_content, paper_title)
    #print(result_json)
    #with open("./sxs_json.json", 'w', encoding='utf-8') as f:
       # json.dump(result_json , f, indent=2, ensure_ascii=False)
    #