import os
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable, List, Tuple
import time

from dataclasses import dataclass, field
from typing import Dict, Optional, Any
import time
import threading

from enum import Enum


class ModelProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    LOCAL = "local"


@dataclass
class ModelSession:
    """大模型会话记录数据结构"""
    prompt: str  # 用户输入的原始prompt
    generated_content: str  # 模型生成的内容
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)  # 可存储token用量等附加信息


@dataclass
class LLMManager:
    """大模型连接管理数据结构"""
    url: str  # 模型API端点
    api_key: str  # 加密存储的API密钥
    model_name: str  # 如"gpt-4-turbo","claude-3-opus"
    provider: ModelProvider  # 模型提供商
    user_id: str  # 关联用户ID
    sessions: Dict[str, List[ModelSession]] = field(default_factory=dict)  # {session_id: [会话记录]}

    def add_session(self, section_name: str, prompt: str, generated: str) -> str:
        """记录新的会话交互"""
        session_id = f"{self.user_id}_{section_name}_{int(time.time())}"
        self.sessions[session_id] = [
            ModelSession(prompt=prompt, generated_content=generated)
        ]
        return session_id


@dataclass
class PromptTemplate:
    """动态Prompt模板数据结构"""
    template_id: str  # 唯一模板标识
    section: str  # 所属章节(如"introduction")
    step: int  # 处理步骤序号
    template_text: str  # 实际模板内容
    variables: List[str] = field(default_factory=list)  # 模板中的动态变量名
    description: Optional[str] = None  # 模板用途说明


@dataclass
class PaperSection:
    """论文章节数据结构"""
    content: str
    last_modified: float = field(default_factory=time.time)
    source: str = "user"  # user|ai|pdf
    status: str = "draft"  # draft|final|edited


class ResearchPaperManager:
    """结合全局状态管理的论文模型单例类"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """实现线程安全的单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_paper()
        return cls._instance

    def __init__(self):
        self.current_paper = ResearchPaper(
            paper_id="default",
            title="New Paper",
            author="anonymous"
        )
        self._observers = []
        self._template_cache: Dict[Tuple[str, int], PromptTemplate] = {}  # {(section,step): template}

    def get_template(self, section: str, step: int) -> PromptTemplate:
        """获取指定章节步骤的模板（带缓存机制）"""
        cache_key = (section.lower(), step)
        if cache_key not in self._template_cache:
            # 从数据库加载模板的伪代码
            template_data = "aa"#Database.get_template(section, step)
            self._template_cache[cache_key] = PromptTemplate(**template_data)
        return self._template_cache[cache_key]

    def log_model_interaction(
            self,
            model_name: str,
            section: str,
            prompt: str,
            generated: str,
            provider: ModelProvider
    ) -> str:
        """记录大模型交互日志"""
        if model_name not in self.current_paper.model_sessions:
            self.current_paper.model_sessions[model_name] = LLMManager(
                url=os.getenv(f"{provider.value}_URL"),
                api_key=os.getenv(f"{provider.value}_KEY"),
                model_name=model_name,
                provider=provider,
                user_id=self.current_paper.author
            )
        return self.current_paper.model_sessions[model_name].add_session(
            section_name=section,
            prompt=prompt,
            generated=generated
        )
    def _init_paper(self):
        """初始化论文数据"""
        self.current_paper = ResearchPaper(
            paper_id="default",
            title="New Paper",
            author="anonymous"
        )
        self._observers = []

    @property
    def sections(self) -> Dict[str, PaperSection]:
        """获取所有章节"""
        return self.current_paper.sections

    def update_section(self,
                       section_name: str,
                       content: str,
                       source: str = "user",
                       status: str = "draft") -> None:
        """
        更新章节内容并通知观察者
        """
        with self._lock:
            self.current_paper.sections[section_name.lower()] = PaperSection(
                content=content,
                source=source,
                status=status
            )
            self.current_paper.current_section = section_name
            self._notify_observers(section_name)

    def get_section(self, section_name: str) -> Optional[PaperSection]:
        """获取指定章节"""
        return self.current_paper.sections.get(section_name.lower())

    def register_observer(self, callback: Callable[[str], None]) -> None:
        """注册数据更新观察者"""
        with self._lock:
            self._observers.append(callback)

    def _notify_observers(self, updated_section: str) -> None:
        """通知所有观察者"""
        for callback in self._observers:
            try:
                callback(updated_section)
            except Exception as e:
                print(f"Observer notification failed: {str(e)}")

    def save_to_db(self):
        """保存到数据库"""
        with self._lock:
            # 实现数据库保存逻辑
            pass

    def load_from_db(self, paper_id: str):
        """从数据库加载"""
        with self._lock:
            # 实现数据库加载
            self._notify_observers("all")  # 通知所有章节更新

@dataclass
class ResearchPaper:
    """论文基础数据结构"""
    paper_id: str
    title: str
    author: str
    sections: Dict[str, PaperSection] = field(default_factory=dict)
    current_section: Optional[str] = None
    model_sessions: Dict[str, LLMManager] = field(default_factory=dict)  # {model_name: LLMManager}

@dataclass
class Prompt_Template:
    """Prompt基础数据结构"""
    ppt_id: str
    prompt_json: str

