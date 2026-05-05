"""
PDF 层次化结构提取 - 多 Agent 协同实现

架构：
    1. OutlineAgent（主 Agent）：扫描全文，构建论文骨架（标题 + 层级 + 每个章节
       对应的 PDF 页码范围），不填写正文。
    2. SectionContentAgent（子 Agent）：每个叶子章节一个，仅基于自己负责的页码
       范围生成精炼的章节正文。可并行执行。
    3. PDFStructurePipeline：协调主 Agent 与子 Agent，最终输出完整的层次化 JSON。

设计目标：
    - 降低单轮上下文压力（主 agent 只看压缩后的目录信号，子 agent 只看自己的页）
    - 调大 max_tokens，避免输出截断
    - 在主 agent 输出不达标时主动重试，不再依赖 try/except 兜底
    - 保持对外 JSON 结构兼容（id/title/content/children）
"""

import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from utils.pdf_structure_tools import (
    PaperStructureManager,
    SectionNode,
    create_outline_tools_for_manager,
)


# ========== 配置 ==========
DEFAULT_API_KEY = os.getenv("MY_API_KEY", "sk-sZi4nNPwuQhqBNonGrHL0yATSQKHOi88AJiiGFQfdG5xoD1l")
DEFAULT_BASE_URL = os.getenv("MY_API_BASE", "https://api.chat.csu.edu.cn/v1")
DEFAULT_MODEL = os.getenv("MY_MODEL", "DeepSeek-V4-Flash")

# 主 Agent 单页文本上限（用于"压缩"输入，避免一次塞 25k 字符）
DEFAULT_OUTLINE_PAGE_CHAR_LIMIT = 1500*8
# 子 Agent 单次输入文本上限（每个叶子章节）
DEFAULT_SECTION_CHAR_LIMIT = 12000*8
# 主 Agent 输出 token 上限（调大，避免章节较多时输出截断）
DEFAULT_OUTLINE_MAX_TOKENS = 8192*8
# 子 Agent 输出 token 上限
DEFAULT_SECTION_MAX_TOKENS = 4096*8
# 子 Agent 并行度
DEFAULT_MAX_PARALLEL_SECTIONS = 4


@dataclass
class PageContent:
    """PDF 单页内容"""
    page_num: int
    text: str


# ============================================================
# 工具函数：把页面"压缩"成主 agent 友好的目录信号文本
# ============================================================

# 看起来像章节编号的行：1.、1.1、1.1.1、一、(一)、第一章、I/II/III、A./a) 等
_HEADING_PATTERNS = [
    re.compile(r"^\s*\d+(?:\.\d+){0,4}\.?\s+\S"),
    re.compile(r"^\s*第[一二三四五六七八九十百\d]+[章节部分篇]\s*"),
    re.compile(r"^\s*[一二三四五六七八九十]+[、.\s]"),
    re.compile(r"^\s*\([一二三四五六七八九十\d]+\)"),
    re.compile(r"^\s*[IVXLCDM]+\.\s+\S"),
    re.compile(r"^\s*[A-Za-z][\.\)]\s+\S"),
    re.compile(r"^\s*Outl\s*i\s*ne", re.IGNORECASE),
    re.compile(r"^\s*(Abstract|Introduction|Background|Related\s+Work|Method(?:ology)?|"
               r"Design|Approach|Evaluation|Experiment|Result|Discussion|Conclusion|"
               r"References|Appendix)\b", re.IGNORECASE),
]


def _looks_like_heading(line: str) -> bool:
    s = line.strip()
    if not s or len(s) > 120:
        return False
    return any(p.match(s) for p in _HEADING_PATTERNS)


def _compress_page_for_outline(text: str, char_limit: int) -> str:
    """
    把单页文本压缩成"目录信号"友好的版本：
      - 总是保留页面前若干字（捕获标题/小标题区域）
      - 额外保留所有疑似标题行
    """
    if not text:
        return ""
    head = text[:char_limit]
    if len(text) <= char_limit:
        return head
    extra_headings: List[str] = []
    for line in text.splitlines():
        if _looks_like_heading(line):
            stripped = line.strip()
            if stripped and stripped not in head:
                extra_headings.append(stripped)
    if extra_headings:
        return head + "\n[...]\n" + "\n".join(extra_headings[:40])
    return head


def _build_outline_input(pages: List[PageContent], paper_title: str, page_char_limit: int) -> str:
    """构建主 Agent 的输入：每页压缩后拼接"""
    lines: List[str] = []
    if paper_title:
        lines.append(f"## 文档标题（已知）: {paper_title}")
        lines.append("")
    lines.append(f"## 文档共 {len(pages)} 页。以下按页给出压缩后的目录信号文本：")
    lines.append("")
    for page in pages:
        compressed = _compress_page_for_outline(page.text, page_char_limit)
        lines.append(f"=== 第 {page.page_num} 页 ===")
        lines.append(compressed)
        lines.append("")
    lines.append("---")
    lines.append("请只调用工具构建章节骨架，不要把正文写进 content。每个章节都必须指定 page_start / page_end。")
    return "\n".join(lines)


def _slice_pages_text(pages: List[PageContent], page_start: int, page_end: int, char_limit: int) -> str:
    """根据页码范围拼接原始正文，并做长度上限裁剪"""
    if page_start is None or page_end is None:
        return ""
    selected: List[str] = []
    for page in pages:
        if page_start <= page.page_num <= page_end:
            selected.append(f"=== 第 {page.page_num} 页 ===\n{page.text}")
    raw = "\n\n".join(selected)
    if len(raw) > char_limit:
        head_len = int(char_limit * 0.7)
        tail_len = char_limit - head_len - 20
        raw = raw[:head_len] + "\n...[此处省略]...\n" + raw[-tail_len:]
    return raw


# ============================================================
# 主 Agent：构建骨架
# ============================================================

class OutlineAgent:
    """主 Agent：负责扫描全文并构建论文骨架（章节 + 页码范围），不填正文。"""

    def __init__(
        self,
        manager: PaperStructureManager,
        api_key: str = DEFAULT_API_KEY,
        base_url: str = DEFAULT_BASE_URL,
        model_name: str = DEFAULT_MODEL,
        temperature: float = 0.2,
        max_tokens: int = DEFAULT_OUTLINE_MAX_TOKENS,
        verbose: bool = True,
    ):
        self.manager = manager
        self.verbose = verbose
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self.tools = create_outline_tools_for_manager(manager)
        self.executor = self._create_executor()

    def _create_executor(self) -> AgentExecutor:
        max_depth = self.manager.max_depth
        system_prompt = f"""你是一个专业的文档结构化助手。你只负责构建论文/文档的层次化「目录骨架」。\
正文撰写由其他子 Agent 完成，你不需要也不应该把正文写进 content 字段。

你得到的是直接从 PDF 中按页提取的文本，可能包含页眉页脚、乱码或宣传词（如"厚德载物"、"Outl i ne"）。
请忽略噪声，专注于识别章节结构。

## 工作流程
1. 先通读全部页面（已经按页给你），重点关注前几页的「目录页」与每页开头的标题。
2. 调用 `set_paper_title` 设置论文主标题。
3. 依次调用 `register_section` 创建章节，每次必须提供：
   - title：章节标题
   - page_start / page_end：该章节对应的 PDF 页码范围（1-based，含端点）
   - parent_id：父章节 ID；一级章节留空
4. 二级章节的 page 区间应落在其一级章节的 page 区间内；三级以此类推。
5. 创建完所有章节后，调用 `finish_outline` 结束。

## 重要规则
- 最大允许层级深度为 {max_depth}。如果文档实际目录更深，截断到 {max_depth} 层。
- 章节 ID 由系统自动生成，你只需要正确设置 parent_id。
- 不要为同一个章节调用多次 register_section。
- 不要使用 create_section / append_content 之类的工具——你没有这些工具。
- **绝对不要**把正文塞进 content 字段，那是子 Agent 的工作。
- 如果某些页是封面、空白页、致谢页等无章节意义的页，可以不为它们注册章节。

## 章节编号识别参考
- 一级：1、2、3 / 一、二、三 / 第一章 / I、II、III / Abstract、Introduction
- 二级：1.1、1.2 / (一)(二) / 1)、2)
- 三级：1.1.1 / a、b、c / ①②③

请严格使用工具调用（function calling）的方式输出，不要直接写自然语言答案，也不要输出 <function_calls> 这类伪 XML。"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=self.verbose,
            max_iterations=80,
            handle_parsing_errors=True,
        )

    def build_outline(self, pages: List[PageContent], paper_title: str, page_char_limit: int) -> None:
        """运行主 Agent 构建骨架（直接修改 self.manager）"""
        input_text = _build_outline_input(pages, paper_title, page_char_limit)
        if self.verbose:
            print(f"[OutlineAgent] 输入约 {len(input_text)} 字符（已压缩）")
        try:
            self.executor.invoke({"input": input_text})
        except Exception as e:
            print(f"[OutlineAgent] 执行异常: {e}")


# ============================================================
# 子 Agent：单章节正文生成（不使用 tool calling，更稳定）
# ============================================================

class SectionContentAgent:
    """
    子 Agent：基于一个叶子章节对应的 PDF 文本片段，输出该章节的精炼正文。

    特意不使用 tool calling 协议，避免与不稳定的网关产生格式分歧；
    直接 chat completion，要求模型输出纯正文。
    """

    SYSTEM_PROMPT = (
        "你是一个学术文档整理助手。给你一段从 PDF 中提取的章节原文（可能含有乱码、"
        "页眉页脚、表格碎片或图片标注），请整理成该章节的「干净正文」。\n\n"
        "要求：\n"
        "1. 只输出该章节的正文段落，**不要**重复章节标题，**不要**输出小标题编号。\n"
        "2. 保留原文的事实、数据、公式与图表引用名（如 Fig.1、Table 2）。\n"
        "3. 删除明显的页眉页脚、页码、版权信息、学校/作者信息、广告语、乱码字符。\n"
        "4. 不要凭空添加原文中没有的结论或数据。\n"
        "5. 用与原文一致的语言（英文原文输出英文，中文原文输出中文）。\n"
        "6. 如果该片段没有任何有效正文（例如只是目录页），输出空字符串。\n"
        "7. 直接输出正文，不要加任何前后缀解释。"
    )

    def __init__(
        self,
        api_key: str = DEFAULT_API_KEY,
        base_url: str = DEFAULT_BASE_URL,
        model_name: str = DEFAULT_MODEL,
        temperature: float = 0.2,
        max_tokens: int = DEFAULT_SECTION_MAX_TOKENS,
        verbose: bool = True,
    ):
        self.verbose = verbose
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def generate(self, section_title: str, section_text: str) -> str:
        if not section_text or not section_text.strip():
            return ""
        user_prompt = (
            f"章节标题：{section_title}\n\n"
            f"该章节对应的原文片段如下（仅供整理，不要重复标题）：\n"
            f"-----BEGIN-----\n{section_text}\n-----END-----"
        )
        try:
            resp = self.llm.invoke([
                ("system", self.SYSTEM_PROMPT),
                ("human", user_prompt),
            ])
            content = getattr(resp, "content", "") or ""
            return content.strip()
        except Exception as e:
            if self.verbose:
                print(f"[SectionContentAgent] 章节 '{section_title}' 生成失败: {e}")
            return ""


# ============================================================
# Pipeline：协调主 Agent + 子 Agent
# ============================================================

class PDFStructurePipeline:
    """两阶段 PDF 结构化解析流水线"""

    def __init__(
        self,
        uid: str = "default",
        max_depth: int = 3,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        outline_max_tokens: int = DEFAULT_OUTLINE_MAX_TOKENS,
        section_max_tokens: int = DEFAULT_SECTION_MAX_TOKENS,
        outline_page_char_limit: int = DEFAULT_OUTLINE_PAGE_CHAR_LIMIT,
        section_char_limit: int = DEFAULT_SECTION_CHAR_LIMIT,
        max_parallel_sections: int = DEFAULT_MAX_PARALLEL_SECTIONS,
        outline_max_retries: int = 2,
        verbose: bool = True,
    ):
        self.uid = uid
        self.max_depth = max_depth
        self.api_key = api_key or DEFAULT_API_KEY
        self.base_url = base_url or DEFAULT_BASE_URL
        self.model_name = model_name or DEFAULT_MODEL
        self.outline_max_tokens = outline_max_tokens
        self.section_max_tokens = section_max_tokens
        self.outline_page_char_limit = outline_page_char_limit
        self.section_char_limit = section_char_limit
        self.max_parallel_sections = max(1, max_parallel_sections)
        self.outline_max_retries = max(1, outline_max_retries)
        self.verbose = verbose

        self.manager = PaperStructureManager(uid=uid, max_depth=max_depth)
        self.section_agent = SectionContentAgent(
            api_key=self.api_key,
            base_url=self.base_url,
            model_name=self.model_name,
            max_tokens=self.section_max_tokens,
            verbose=verbose,
        )

    # ---------- Phase 1: 主 Agent 构建骨架（带健康检查 + 重试） ----------
    def _run_outline_phase(self, pages: List[PageContent], paper_title: str) -> None:
        for attempt in range(1, self.outline_max_retries + 1):
            if self.verbose:
                print(f"[Pipeline] 主 Agent 尝试 {attempt}/{self.outline_max_retries}")
            self.manager = PaperStructureManager(uid=self.uid, max_depth=self.max_depth)
            outline_agent = OutlineAgent(
                manager=self.manager,
                api_key=self.api_key,
                base_url=self.base_url,
                model_name=self.model_name,
                max_tokens=self.outline_max_tokens,
                verbose=self.verbose,
            )
            outline_agent.build_outline(
                pages=pages,
                paper_title=paper_title,
                page_char_limit=self.outline_page_char_limit,
            )
            if self._outline_is_healthy():
                if self.verbose:
                    print("[Pipeline] 主 Agent 输出健康，进入子 Agent 阶段")
                    print(self.manager.get_structure_summary())
                return
            if self.verbose:
                print(f"[Pipeline] 主 Agent 输出不达标（章节数={self.manager.count_sections()}），重试")

        if self.verbose:
            print("[Pipeline] 主 Agent 多次重试仍不达标，回退到规则式骨架")
        self._fallback_outline_from_pages(pages, paper_title)

    def _outline_is_healthy(self) -> bool:
        """简单健康检查：至少 2 个章节，且每个叶子都绑定了页码"""
        if self.manager.count_sections() < 2:
            return False
        for leaf in self.manager.iter_leaf_sections():
            if leaf.page_start is None or leaf.page_end is None:
                return False
        return True

    def _fallback_outline_from_pages(self, pages: List[PageContent], paper_title: str) -> None:
        """主 Agent 实在不可用时的兜底骨架：每 N 页一个章节"""
        self.manager = PaperStructureManager(uid=self.uid, max_depth=self.max_depth)
        if paper_title:
            self.manager.set_paper_title(paper_title)
        chunk_size = max(1, len(pages) // 5) if pages else 1
        idx = 1
        for start in range(0, len(pages), chunk_size):
            end = min(start + chunk_size - 1, len(pages) - 1)
            self.manager.register_section(
                title=f"Section {idx}",
                parent_id=None,
                page_start=pages[start].page_num,
                page_end=pages[end].page_num,
            )
            idx += 1

    # ---------- Phase 2: 子 Agent 并行回填正文 ----------
    def _run_section_phase(self, pages: List[PageContent]) -> None:
        leaves: List[SectionNode] = self.manager.iter_leaf_sections()
        if self.verbose:
            print(f"[Pipeline] 共 {len(leaves)} 个叶子章节，子 Agent 并行度 {self.max_parallel_sections}")

        def work(leaf: SectionNode) -> Dict[str, Any]:
            section_text = _slice_pages_text(
                pages=pages,
                page_start=leaf.page_start,
                page_end=leaf.page_end,
                char_limit=self.section_char_limit,
            )
            content = self.section_agent.generate(leaf.title, section_text)
            return {"id": leaf.id, "title": leaf.title, "content": content}

        if self.max_parallel_sections == 1:
            results = [work(leaf) for leaf in leaves]
        else:
            results = []
            with ThreadPoolExecutor(max_workers=self.max_parallel_sections) as pool:
                future_map = {pool.submit(work, leaf): leaf for leaf in leaves}
                for fut in as_completed(future_map):
                    leaf = future_map[fut]
                    try:
                        results.append(fut.result())
                    except Exception as e:
                        if self.verbose:
                            print(f"[Pipeline] 章节 [{leaf.id}] '{leaf.title}' 子 Agent 异常: {e}")
                        results.append({"id": leaf.id, "title": leaf.title, "content": ""})

        for r in results:
            self.manager.set_section_content(r["id"], r["content"])
            if self.verbose:
                print(f"[Pipeline] 已回填 [{r['id']}] '{r['title']}' "
                      f"({len(r['content'])} 字)")

    # ---------- 对外入口 ----------
    def process_pages(self, pages: List[PageContent], paper_title: str = "") -> dict:
        if self.verbose:
            print(f"[Pipeline] 开始处理：{len(pages)} 页，最大层级 {self.max_depth}")
        self._run_outline_phase(pages, paper_title)
        self._run_section_phase(pages)
        if self.verbose:
            print("[Pipeline] 处理完成")
            print(self.manager.get_structure_summary())
        return self.manager.to_json()


# ============================================================
# 向后兼容 API
# ============================================================

class PDFStructureAgent:
    """
    向后兼容包装：旧接口仍可使用，但内部实际调用新的多 Agent 流水线。
    """

    def __init__(
        self,
        uid: str = "default",
        max_depth: int = 3,
        api_key: str = DEFAULT_API_KEY,
        base_url: str = DEFAULT_BASE_URL,
        model_name: str = DEFAULT_MODEL,
        temperature: float = 0.3,  # noqa: ARG002 — 兼容旧签名，未在 pipeline 中按字段使用
        verbose: bool = True,
        outline_max_tokens: int = DEFAULT_OUTLINE_MAX_TOKENS,
        section_max_tokens: int = DEFAULT_SECTION_MAX_TOKENS,
        max_parallel_sections: int = DEFAULT_MAX_PARALLEL_SECTIONS,
    ):
        self.uid = uid
        self.max_depth = max_depth
        self.verbose = verbose
        self.pipeline = PDFStructurePipeline(
            uid=uid,
            max_depth=max_depth,
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            outline_max_tokens=outline_max_tokens,
            section_max_tokens=section_max_tokens,
            max_parallel_sections=max_parallel_sections,
            verbose=verbose,
        )

    @property
    def manager(self) -> PaperStructureManager:
        return self.pipeline.manager

    def process_pages(self, pages: List[PageContent], paper_title: str = "") -> dict:
        return self.pipeline.process_pages(pages, paper_title=paper_title)

    def reset(self):
        self.pipeline.manager = PaperStructureManager(uid=self.uid, max_depth=self.max_depth)


def create_pdf_structure_agent(
    uid: str = "default",
    max_depth: int = 3,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model_name: Optional[str] = None,
    verbose: bool = True,
    outline_max_tokens: int = DEFAULT_OUTLINE_MAX_TOKENS,
    section_max_tokens: int = DEFAULT_SECTION_MAX_TOKENS,
    max_parallel_sections: int = DEFAULT_MAX_PARALLEL_SECTIONS,
) -> PDFStructureAgent:
    """便捷构造函数，保持旧调用方式不变"""
    return PDFStructureAgent(
        uid=uid,
        max_depth=max_depth,
        api_key=api_key or DEFAULT_API_KEY,
        base_url=base_url or DEFAULT_BASE_URL,
        model_name=model_name or DEFAULT_MODEL,
        verbose=verbose,
        outline_max_tokens=outline_max_tokens,
        section_max_tokens=section_max_tokens,
        max_parallel_sections=max_parallel_sections,
    )


# 测试代码
if __name__ == "__main__":
    test_pages = [
        PageContent(
            page_num=1,
            text="""中南大学
作者：张三
指导教师：李四

基于深度学习的图像识别技术研究

2024年6月""",
        ),
        PageContent(
            page_num=2,
            text="""1 引言

1.1 研究背景
随着人工智能技术的快速发展，深度学习在图像识别领域取得了突破性进展。
本研究旨在探索更高效的图像识别算法。

1.2 研究意义
图像识别技术在医疗诊断、自动驾驶等领域有广泛应用价值。""",
        ),
        PageContent(
            page_num=3,
            text="""2 相关工作

2.1 传统图像识别方法
早期的图像识别主要依赖手工设计的特征提取器，如SIFT、HOG等。
这些方法在简单场景下表现良好，但泛化能力有限。

2.2 深度学习方法
2.2.1 卷积神经网络
CNN的出现彻底改变了图像识别领域。

2.2.2 残差网络
ResNet通过引入跳跃连接解决了深层网络的训练问题。""",
        ),
        PageContent(
            page_num=4,
            text="""3 研究方法

本文提出了一种新的网络架构，结合了注意力机制和多尺度特征融合。

3.1 网络架构
我们的网络由编码器和解码器两部分组成。

3.2 损失函数
采用交叉熵损失与正则化项的组合。""",
        ),
    ]

    agent = create_pdf_structure_agent(uid="test_user", max_depth=3, verbose=True)
    result = agent.process_pages(test_pages)

    import json
    print("\n" + "=" * 60)
    print("最终结果:")
    print("=" * 60)
    print(json.dumps(result, ensure_ascii=False, indent=2))
