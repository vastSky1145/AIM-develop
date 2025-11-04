import json

def print_hierarchy(paper):
    full_content=""
    """
    将 JSON 格式的论文结构按层次打印为纯文本。
    paper: {
      "paper_title": "...",
      "sections": [
        {
          "id": "ppt1",
          "title": "...",
          "content": "...",
          "children": [ ... ]
        },
        ...
      ]
    }
    """
    # 打印论文标题
    if paper.get("paper_title"):
        full_content = ''.join(paper["paper_title"])
        print(paper["paper_title"])
        print("=" * len(paper["paper_title"]))
        print()

    def _print_sections(sections, indent=0):
        for node in sections:
            # 缩进 + 编号 + 标题
            print("    " * indent + f"{node['id']} {node['title']}")
            full_content = ''.join(paper["paper_title"])
            # 如果有纯文本内容，也一并打印
            if node.get("content"):
                for line in node["content"].splitlines():
                    print("    " * (indent + 1) + line)
            # 递归打印子节点
            if node.get("children"):
                _print_sections(node["children"], indent + 1)

    _print_sections(paper.get("sections", []))
    return full_content

if __name__ == "__main__":
    # 假设已经有一个变量 paper_json_str 存储了上一步生成的 JSON 字符串
    # 你也可以从文件里读： paper = json.load(open("structure.json", "r", encoding="utf-8"))
    with open("./sxs_json.json", "r", encoding="utf-8") as f:
        paper = json.load(f)
    print_hierarchy(paper)
