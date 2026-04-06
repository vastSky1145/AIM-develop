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
        parent_id: Optional[str] = None
    ) -> str:
        """
        创建新章节
        
        Args:
            title: 章节标题
            content: 章节内容
            parent_id: 父节点ID，None表示一级章节
            
        Returns:
            操作结果描述
        """
        # 检查深度限制
        if parent_id:
            current_depth = self._get_node_depth(parent_id) + 1
            if current_depth > self.max_depth:
                return f"错误: 超出最大层级限制({self.max_depth}层)，无法在 {parent_id} 下创建子节点"
        
        new_id = self._generate_id(parent_id)
        new_node = SectionNode(id=new_id, title=title, content=content)
        self._node_map[new_id] = new_node
        
        if parent_id is None:
            # 添加为一级章节
            self.sections.append(new_node)
        else:
            parent = self._node_map.get(parent_id)
            if parent:
                parent.children.append(new_node)
                self._parent_map[new_id] = parent_id
            else:
                return f"错误: 父节点 {parent_id} 不存在"
        
        return f"成功创建章节 [{new_id}] '{title}'"
    
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
            result = f"{prefix}- [{node.id}] {node.title} {content_preview}\n"
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
