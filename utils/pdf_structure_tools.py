"""
PDF层次化结构提取 - JSON骨架操作工具

提供供LangChain Agent调用的工具函数，用于构建层次化JSON结构。
LLM通过调用这些工具来操作JSON，避免直接生成复杂嵌套JSON导致的幻觉问题。
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from langchain_core.tools import tool
import json
import uuid


@dataclass
class SectionNode:
    """章节节点"""
    id: str
    title: str
    content: str = ""
    children: List["SectionNode"] = field(default_factory=list)
    # 该节点对应的 PDF 页码范围（仅供子 agent 派发用，不会输出到最终 JSON）
    page_start: Optional[int] = None
    page_end: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "children": [child.to_dict() for child in self.children]
        }


class PaperStructureManager:
    """
    论文结构管理器
    
    维护一个层次化的JSON结构，提供增删改查方法供Agent调用
    """
    
    def __init__(self, uid: str = "default", max_depth: int = 3):
        self.uid = uid
        self.max_depth = max_depth
        self.paper_title = ""
        self.sections: List[SectionNode] = []
        self._node_map: Dict[str, SectionNode] = {}  # id -> node 快速查找
        self._parent_map: Dict[str, str] = {}  # child_id -> parent_id
    
    def _generate_id(self, parent_id: Optional[str] = None) -> str:
        """生成章节ID，如 sec1, sec1.1, sec1.1.1"""
        if parent_id is None:
            # 一级章节
            idx = len(self.sections) + 1
            return f"sec{idx}"
        else:
            parent = self._node_map.get(parent_id)
            if parent:
                idx = len(parent.children) + 1
                return f"{parent_id}.{idx}"
            return f"sec{uuid.uuid4().hex[:6]}"
    
    def _get_node_depth(self, node_id: str) -> int:
        """获取节点深度，根节点为1"""
        return node_id.count('.') + 1
    
    def set_paper_title(self, title: str) -> str:
        """设置论文标题"""
        self.paper_title = title
        return f"已设置论文标题: {title}"
    
    def create_section(
        self,
        title: str,
        content: str = "",
        parent_id: Optional[str] = None,
        page_start: Optional[int] = None,
        page_end: Optional[int] = None,
    ) -> str:
        """
        创建新章节

        Args:
            title: 章节标题
            content: 章节内容
            parent_id: 父节点ID，None表示一级章节
            page_start: 该章节对应的 PDF 起始页（可选）
            page_end: 该章节对应的 PDF 结束页（可选）

        Returns:
            操作结果描述
        """
        # 检查深度限制
        if parent_id:
            current_depth = self._get_node_depth(parent_id) + 1
            if current_depth > self.max_depth:
                return f"错误: 超出最大层级限制({self.max_depth}层)，无法在 {parent_id} 下创建子节点"

        new_id = self._generate_id(parent_id)
        new_node = SectionNode(
            id=new_id,
            title=title,
            content=content,
            page_start=page_start,
            page_end=page_end,
        )
        self._node_map[new_id] = new_node

        if parent_id is None:
            self.sections.append(new_node)
        else:
            parent = self._node_map.get(parent_id)
            if parent:
                parent.children.append(new_node)
                self._parent_map[new_id] = parent_id
            else:
                return f"错误: 父节点 {parent_id} 不存在"

        page_info = ""
        if page_start is not None or page_end is not None:
            page_info = f" 页码 [{page_start}-{page_end}]"
        return f"成功创建章节 [{new_id}] '{title}'{page_info}"

    def register_section(
        self,
        title: str,
        parent_id: Optional[str] = None,
        page_start: Optional[int] = None,
        page_end: Optional[int] = None,
    ) -> str:
        """
        主 Agent 专用：仅注册章节骨架（不带正文），但要求绑定页码范围。
        正文将由子 Agent 后续生成。
        """
        if page_start is None or page_end is None:
            return (
                "错误: 注册章节必须提供 page_start 和 page_end，"
                "用于后续子 Agent 定位正文页"
            )
        if page_start < 1 or page_end < page_start:
            return f"错误: 非法页码范围 [{page_start}-{page_end}]"
        return self.create_section(
            title=title,
            content="",
            parent_id=parent_id,
            page_start=page_start,
            page_end=page_end,
        )

    def set_section_content(self, section_id: str, content: str) -> str:
        """子 Agent 完成后用于一次性回填章节正文"""
        node = self._node_map.get(section_id)
        if not node:
            return f"错误: 章节 {section_id} 不存在"
        node.content = content or ""
        return f"已回填章节 [{section_id}] 正文({len(node.content)}字)"

    def iter_leaf_sections(self) -> List[SectionNode]:
        """返回所有叶子章节节点（深度优先，按文档顺序）"""
        result: List[SectionNode] = []

        def walk(node: SectionNode):
            if not node.children:
                result.append(node)
                return
            for child in node.children:
                walk(child)

        for section in self.sections:
            walk(section)
        return result

    def count_sections(self) -> int:
        """统计章节总数（含所有层级）"""
        return len(self._node_map)
    
    def update_section(
        self, 
        section_id: str, 
        title: Optional[str] = None, 
        content: Optional[str] = None
    ) -> str:
        """
        更新章节信息
        
        Args:
            section_id: 章节ID
            title: 新标题（可选）
            content: 新内容（可选）
            
        Returns:
            操作结果描述
        """
        node = self._node_map.get(section_id)
        if not node:
            return f"错误: 章节 {section_id} 不存在"
        
        updates = []
        if title is not None:
            node.title = title
            updates.append(f"标题->'{title}'")
        if content is not None:
            node.content = content
            updates.append(f"内容已更新({len(content)}字)")
        
        if updates:
            return f"已更新章节 [{section_id}]: {', '.join(updates)}"
        return f"章节 [{section_id}] 无变更"
    
    def append_content(self, section_id: str, content: str) -> str:
        """
        追加内容到章节
        
        Args:
            section_id: 章节ID
            content: 要追加的内容
            
        Returns:
            操作结果描述
        """
        node = self._node_map.get(section_id)
        if not node:
            return f"错误: 章节 {section_id} 不存在"
        
        if node.content:
            node.content += "\n" + content
        else:
            node.content = content
        
        return f"已向章节 [{section_id}] 追加内容({len(content)}字)"
    
    def get_structure_summary(self) -> str:
        """
        获取当前结构摘要（供Agent查看进度）
        
        Returns:
            结构树形摘要
        """
        def format_node(node: SectionNode, indent: int = 0) -> str:
            prefix = "  " * indent
            content_preview = f"({len(node.content)}字)" if node.content else "(空)"
            page_info = ""
            if node.page_start is not None or node.page_end is not None:
                page_info = f" 页[{node.page_start}-{node.page_end}]"
            result = f"{prefix}- [{node.id}] {node.title}{page_info} {content_preview}\n"
            for child in node.children:
                result += format_node(child, indent + 1)
            return result
        
        summary = f"论文标题: {self.paper_title or '(未设置)'}\n"
        summary += f"最大层级: {self.max_depth}\n"
        summary += f"章节结构:\n"
        
        if not self.sections:
            summary += "  (暂无章节)\n"
        else:
            for section in self.sections:
                summary += format_node(section)
        
        return summary
    
    def get_section_list(self) -> str:
        """获取所有章节ID和标题列表"""
        result = []
        
        def collect(node: SectionNode):
            result.append(f"[{node.id}] {node.title}")
            for child in node.children:
                collect(child)
        
        for section in self.sections:
            collect(section)
        
        return "\n".join(result) if result else "暂无章节"
    
    def to_json(self) -> dict:
        """导出为最终JSON格式"""
        return {
            "uid": self.uid,
            "paper_title": self.paper_title,
            "sections": [section.to_dict() for section in self.sections]
        }
    
    def to_json_string(self, indent: int = 2) -> str:
        """导出为JSON字符串"""
        return json.dumps(self.to_json(), ensure_ascii=False, indent=indent)


def create_tools_for_manager(manager: PaperStructureManager):
    """
    为指定的PaperStructureManager创建LangChain工具集
    
    Args:
        manager: 论文结构管理器实例
        
    Returns:
        工具列表
    """
    
    @tool
    def set_paper_title(title: str) -> str:
        """设置论文的主标题。在开始创建章节之前，应先设置论文标题。
        
        Args:
            title: 论文的主标题
        """
        return manager.set_paper_title(title)
    
    @tool
    def create_section(title: str = "", content: str = "", parent_id: str = "") -> str:
        """创建一个新的章节。title是必须提供的章节标题。
        
        如果不指定parent_id，则创建一级章节。
        如果指定parent_id，则在该父章节下创建子章节。
        
        Args:
            title: 章节标题（必填），例如"1. Introduction"或"研究背景"
            content: 章节的正文内容，可以为空
            parent_id: 父章节的ID，例如"sec1"。如果为空字符串，则创建一级章节
        """
        if not title and content:
            title = content
            content = ""
        if not title:
            return "错误: 必须提供章节标题(title参数)"
        pid = parent_id if parent_id else None
        return manager.create_section(title=title, content=content, parent_id=pid)
    
    @tool
    def update_section(section_id: str, title: str = "", content: str = "") -> str:
        """更新已存在章节的标题或内容。
        
        Args:
            section_id: 要更新的章节ID，例如"sec1"或"sec1.1"
            title: 新的标题，如果为空字符串则不更新标题
            content: 新的内容，如果为空字符串则不更新内容
        """
        t = title if title else None
        c = content if content else None
        return manager.update_section(section_id=section_id, title=t, content=c)
    
    @tool
    def append_content(section_id: str, content: str) -> str:
        """向已存在的章节追加内容。适合分批添加较长的正文。
        
        Args:
            section_id: 章节ID，例如"sec1"或"sec1.1"
            content: 要追加的内容
        """
        return manager.append_content(section_id=section_id, content=content)
    
    @tool
    def get_structure_summary() -> str:
        """获取当前论文的结构摘要。可以用来查看已创建的章节层次和进度。"""
        return manager.get_structure_summary()
    
    @tool
    def get_section_list() -> str:
        """获取所有已创建章节的ID和标题列表。用于快速查看现有章节。"""
        return manager.get_section_list()
    
    @tool
    def finish_structuring() -> str:
        """完成结构化操作，返回最终的JSON结果。在所有章节都创建完成后调用此工具。"""
        return f"结构化完成！\n{manager.get_structure_summary()}"
    
    return [
        set_paper_title,
        create_section,
        update_section,
        append_content,
        get_structure_summary,
        get_section_list,
        finish_structuring
    ]


def create_outline_tools_for_manager(manager: PaperStructureManager):
    """
    主 Agent 专用工具集：只负责构建骨架，必须为每个章节绑定 PDF 页码范围。
    正文由后续子 Agent 生成，主 Agent 不应填写 content。

    Args:
        manager: 论文结构管理器实例

    Returns:
        outline 工具列表
    """

    @tool
    def set_paper_title(title: str) -> str:
        """设置论文/文档的主标题。在注册章节之前应先调用此工具。

        Args:
            title: 论文的主标题
        """
        return manager.set_paper_title(title)

    @tool
    def register_section(
        title: str,
        page_start: int,
        page_end: int,
        parent_id: str = "",
    ) -> str:
        """注册一个章节骨架，必须同时提供该章节在 PDF 中的起止页码。

        - 只用来构建目录结构，不写正文。正文将由专门的子 Agent 处理。
        - 一级章节请把 parent_id 留空。
        - 二级章节请把 parent_id 设为其一级章节 ID（如 "sec1"）。
        - 三级章节请把 parent_id 设为其二级章节 ID（如 "sec1.2"）。
        - page_start / page_end 必须为 1-based PDF 页码，且 page_start <= page_end。
        - 如果某一级章节本身有自己的引言/小结之外的子章节，请仍然给它一个完整的页码范围（覆盖所有子章节）。
          子 Agent 会用叶子章节自己的页码范围去抽取正文。

        Args:
            title: 章节标题，例如 "1. Introduction" 或 "研究背景"
            page_start: 该章节起始页码（1-based）
            page_end: 该章节结束页码（含）
            parent_id: 父章节 ID。一级章节留空字符串
        """
        if not title or not title.strip():
            return "错误: 必须提供章节标题(title参数)"
        pid = parent_id if parent_id else None
        return manager.register_section(
            title=title.strip(),
            parent_id=pid,
            page_start=page_start,
            page_end=page_end,
        )

    @tool
    def get_structure_summary() -> str:
        """获取当前已构建的论文骨架。可用于检查进度，避免重复或遗漏章节。"""
        return manager.get_structure_summary()

    @tool
    def get_section_list() -> str:
        """列出所有已注册章节的 ID 与标题。"""
        return manager.get_section_list()

    @tool
    def finish_outline() -> str:
        """完成骨架构建。所有章节都已注册且绑定页码后调用此工具结束本轮。"""
        return f"骨架构建完成。\n{manager.get_structure_summary()}"

    return [
        set_paper_title,
        register_section,
        get_structure_summary,
        get_section_list,
        finish_outline,
    ]


# 测试代码
if __name__ == "__main__":
    # 创建管理器
    manager = PaperStructureManager(uid="test_user", max_depth=3)
    
    # 模拟操作
    print(manager.set_paper_title("基于深度学习的图像识别研究"))
    print(manager.create_section("引言", "本文研究..."))
    print(manager.create_section("研究背景", parent_id="sec1"))
    print(manager.create_section("研究意义", parent_id="sec1"))
    print(manager.create_section("相关工作", "前人研究..."))
    print(manager.create_section("传统方法", parent_id="sec2"))
    print(manager.create_section("深度学习方法", parent_id="sec2"))
    
    # 测试深度限制
    print(manager.create_section("CNN", parent_id="sec2.2"))
    print(manager.create_section("ResNet细节", parent_id="sec2.2.1"))  # 应该被拒绝
    
    print("\n" + "="*50)
    print(manager.get_structure_summary())
    print("\n" + "="*50)
    print(manager.to_json_string())
