"""
PDF层次化结构提取 - LangChain Agent实现

使用LangChain ReAct Agent，让LLM通过调用工具函数来构建层次化JSON结构。
Agent会根据PDF文本内容，识别章节标题，并递归地将内容划分到各级章节中。
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import create_tool_calling_agent, AgentExecutor

from utils.pdf_structure_tools import PaperStructureManager, create_tools_for_manager


# ========== 配置 ==========
DEFAULT_API_KEY = os.getenv("MY_API_KEY", "sk-sZi4nNPwuQhqBNonGrHL0yATSQKHOi88AJiiGFQfdG5xoD1l")
DEFAULT_BASE_URL = os.getenv("MY_API_BASE", "https://api.chat.csu.edu.cn/v1")
DEFAULT_MODEL = os.getenv("MY_MODEL", "deepseek-v3")


@dataclass
class PageContent:
    """PDF单页内容"""
    page_num: int  # 页码（从1开始）
    text: str      # 页面文本内容


class PDFStructureAgent:
    """
    PDF结构化提取Agent
    
    使用LangChain Agent递归地将PDF内容转换为层次化JSON结构。
    """
    
    def __init__(
        self,
        uid: str = "default",
        max_depth: int = 3,
        api_key: str = DEFAULT_API_KEY,
        base_url: str = DEFAULT_BASE_URL,
        model_name: str = DEFAULT_MODEL,
        temperature: float = 0.3,
        verbose: bool = True
    ):
        """
        初始化Agent
        
        Args:
            uid: 用户ID，用于JSON中的uid字段
            max_depth: 最大章节层级深度
            api_key: LLM API密钥
            base_url: LLM API地址
            model_name: 模型名称
            temperature: 生成温度，建议较低以保证稳定性
            verbose: 是否打印详细日志
        """
        self.uid = uid
        self.max_depth = max_depth
        self.verbose = verbose
        
        # 初始化LLM
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model_name,
            temperature=temperature,
            max_tokens=4096
        )
        
        # 初始化结构管理器和工具
        self.manager = PaperStructureManager(uid=uid, max_depth=max_depth)
        self.tools = create_tools_for_manager(self.manager)
        
        # 创建Agent
        self.agent_executor = self._create_agent()
    
    def _create_agent(self) -> AgentExecutor:
        """创建LangChain Agent"""
        
        system_prompt = f"""你是一个专业的文档结构化助手。你的任务是将PDF/PPT文档的文本内容转换为层次化的JSON结构。你得到的是直接从文档中提取的文本，中间或许有各种乱码和标语（如厚德载物，或者
【
Outl i ne
Ø 4.Evaluation
Ø 4.1Set up
Ø 5.Conclusions
Interagin自自g S强强upe不不r R息息es o厚厚luti德德on 载载for 物物Personalized
】)        

## 你的工作流程：
在正式工作之前，你或许需要粗略了解一遍全文，了解全文结构
其次，你需要明确文章的目录结构，作者或许会在头几页提供目录

1. **首先**：使用 `set_paper_title` 工具设置论文/文档的主标题
2. **识别一级章节**：根据文本中的章节编号（如"1."、"一、"、"第一章"）或语义分析，识别一级标题，随后一次识别二级，三级标题等等，具体深度需要看传入的参数，这个参数是{self.max_depth}，不过也不能超过文章内目录的最大深度
3. **创建章节**：使用 `create_section` 工具创建章节，注意：
   - 一级章节不需要指定parent_id
   - 二级章节需要指定其父章节的ID（如parent_id="sec1"）
   - 三级章节需要指定二级章节ID（如parent_id="sec1.2"）
4. **填充内容**：将对应的正文内容填入章节的content字段
5. **递归细分**：对于内容较多的章节，识别其中的子标题，创建子章节
6. **检查进度**：使用 `get_structure_summary` 查看当前结构
7. **完成**：所有内容处理完毕后，调用 `finish_structuring` 完成任务

## 重要规则：

- 最大层级深度为 {self.max_depth} 层，超过限制的子章节会被拒绝
- 章节ID由系统自动生成，你只需要关注parent_id
- 如果文本中有明确的章节编号（如1.1、1.2），优先使用它们来判断层级
- 如果没有明确编号，根据语义和逻辑关系判断层级
- 过滤掉页眉、页脚、学校名称、作者信息等与正文无关的内容
- 保持内容的完整性，不要遗漏重要信息

## 常见的章节标识符：

- 一级：1、2、3 或 一、二、三 或 第一章、第二章 或 I、II、III
- 二级：1.1、1.2 或 （一）（二） 或 1)、2)
- 三级：1.1.1、1.1.2 或 a、b、c 或 ①②③

另外，值得注意的是，用户往往会在第一页写标题，第二页写目录，这有助于你识别标题和各个章节，但真实情况也不完全是如此，你需要自己判断。

现在请根据用户提供的文档内容，构建层次化结构。"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # 创建工具调用Agent
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=self.verbose,
            max_iterations=50,  # 允许足够的迭代次数
            handle_parsing_errors=True
        )
    
    def process_pages(self, pages: List[PageContent], paper_title: str = "") -> dict:
        """
        处理PDF页面内容，返回结构化JSON
        
        Args:
            pages: PDF页面内容列表
            paper_title: 可选的论文标题（如已知）
            
        Returns:
            结构化的JSON字典
        """
        # 构建输入文本
        input_text = self._build_input_text(pages, paper_title)
        
        if self.verbose:
            print(f"[Agent] 开始处理，共 {len(pages)} 页")
            print(f"[Agent] 最大层级: {self.max_depth}")
        
        # 执行Agent，支持重试
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                result = self.agent_executor.invoke({"input": input_text})
                
                if self.verbose:
                    print(f"[Agent] 处理完成")
                    print(self.manager.get_structure_summary())
                
                return self.manager.to_json()
                
            except Exception as e:
                print(f"[Agent] 第{attempt}次尝试出错: {e}")
                if attempt < max_retries:
                    print(f"[Agent] 正在重试 ({attempt}/{max_retries})...")
                    self.manager = PaperStructureManager(uid=self.uid, max_depth=self.max_depth)
                    self.tools = create_tools_for_manager(self.manager)
                    self.agent_executor = self._create_agent()
                else:
                    print(f"[Agent] 已达最大重试次数，返回当前结果")
                    return self.manager.to_json()
    
    def _build_input_text(self, pages: List[PageContent], paper_title: str = "") -> str:
        """构建Agent输入文本"""
        lines = []
        
        if paper_title:
            lines.append(f"## 文档标题（已知）: {paper_title}")
            lines.append("")
        
        lines.append("## 文档内容（按页）:")
        lines.append("")
        
        for page in pages:
            lines.append(f"=== 第 {page.page_num} 页 ===")
            lines.append(page.text)
            lines.append("")
        
        lines.append("---")
        lines.append("请根据以上内容，使用提供的工具构建层次化结构。")
        lines.append("注意过滤页眉页脚等无关内容，保留正文和章节结构。")
        
        return "\n".join(lines)
    
    def reset(self):
        """重置Agent状态，用于处理新文档"""
        self.manager = PaperStructureManager(uid=self.uid, max_depth=self.max_depth)
        self.tools = create_tools_for_manager(self.manager)
        self.agent_executor = self._create_agent()


def create_pdf_structure_agent(
    uid: str = "default",
    max_depth: int = 3,
    api_key: str = None,
    base_url: str = None,
    model_name: str = None,
    verbose: bool = True
) -> PDFStructureAgent:
    """
    创建PDF结构化Agent的便捷函数
    
    Args:
        uid: 用户ID
        max_depth: 最大层级深度（默认3层）
        api_key: API密钥（默认从环境变量读取）
        base_url: API地址（默认从环境变量读取）
        model_name: 模型名称（默认从环境变量读取）
        verbose: 是否打印详细日志
        
    Returns:
        PDFStructureAgent实例
    """
    return PDFStructureAgent(
        uid=uid,
        max_depth=max_depth,
        api_key=api_key or DEFAULT_API_KEY,
        base_url=base_url or DEFAULT_BASE_URL,
        model_name=model_name or DEFAULT_MODEL,
        verbose=verbose
    )


# 测试代码
if __name__ == "__main__":
    # 模拟PDF页面内容
    test_pages = [
        PageContent(
            page_num=1,
            text="""中南大学
作者：张三
指导教师：李四

基于深度学习的图像识别技术研究

2024年6月"""
        ),
        PageContent(
            page_num=2,
            text="""1 引言

1.1 研究背景
随着人工智能技术的快速发展，深度学习在图像识别领域取得了突破性进展。
本研究旨在探索更高效的图像识别算法。

1.2 研究意义
图像识别技术在医疗诊断、自动驾驶等领域有广泛应用价值。"""
        ),
        PageContent(
            page_num=3,
            text="""2 相关工作

2.1 传统图像识别方法
早期的图像识别主要依赖手工设计的特征提取器，如SIFT、HOG等。
这些方法在简单场景下表现良好，但泛化能力有限。

2.2 深度学习方法
2.2.1 卷积神经网络
CNN的出现彻底改变了图像识别领域。AlexNet在2012年ImageNet竞赛中的成功
标志着深度学习时代的到来。

2.2.2 残差网络
ResNet通过引入跳跃连接解决了深层网络的训练问题。"""
        ),
        PageContent(
            page_num=4,
            text="""3 研究方法

本文提出了一种新的网络架构，结合了注意力机制和多尺度特征融合。

3.1 网络架构
我们的网络由编码器和解码器两部分组成。

3.2 损失函数
采用交叉熵损失与正则化项的组合。"""
        )
    ]
    
    # 创建Agent并处理
    agent = create_pdf_structure_agent(
        uid="test_user",
        max_depth=3,
        verbose=True
    )
    
    result = agent.process_pages(test_pages)
    
    print("\n" + "="*60)
    print("最终结果:")
    print("="*60)
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))
