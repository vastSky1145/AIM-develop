"""
PDF文本提取与预处理

提供PDF文本提取功能，支持过滤页眉页脚等无关内容，
返回结构化的页面内容列表，供Agent处理。
"""

import re
from typing import List, Optional, Set, Callable
from dataclasses import dataclass
import pdfplumber


@dataclass
class PageContent:
    """PDF单页内容"""
    page_num: int  # 页码（从1开始）
    text: str      # 页面文本内容（已过滤）
    # raw_text: str  # 原始文本（未过滤）


class PDFTextExtractor:
    """
    PDF文本提取器
    
    支持：
    - 按页提取文本
    - 过滤页眉页脚
    - 过滤自定义关键词（如学校名、作者信息）
    - 文本清洗和规范化
    """
    
    # 常见需要过滤的页眉页脚模式
    # 暂时认为无需过滤
    # DEFAULT_FILTER_PATTERNS = [
    #     # 页码模式
    #     r'^第?\s*\d+\s*页?$',
    #     r'^\d+\s*/\s*\d+$',  # 1/10 格式
    #     r'^Page\s*\d+',
    #     r'^-\s*\d+\s*-$',
    #
    #     # 常见页眉内容
    #     r'^中南大学.*$',
    #     r'^.*大学$',
    #     r'^.*学院$',
    #     r'^.*课程论文.*$',
    #     r'^.*毕业论文.*$',
    #     r'^.*学位论文.*$',
    #
    #     # 日期格式
    #     r'^\d{4}年\d{1,2}月\d{1,2}日$',
    #     r'^\d{4}-\d{1,2}-\d{1,2}$',
    # ]
    
    def __init__(
        self,
        # filter_patterns: List[str] = None,
        # filter_keywords: Set[str] = None,
        min_line_length: int = 2,
        # custom_filter: Callable[[str], bool] = None
    ):
        """
        初始化提取器
        
        Args:
            filter_patterns: 正则过滤模式列表
            filter_keywords: 需要过滤的关键词集合
            min_line_length: 最小行长度，低于此长度的行可能被过滤
            custom_filter: 自定义过滤函数，返回True表示保留该行
        """
        # self.filter_patterns = [
        #     re.compile(p, re.IGNORECASE)
        #     for p in (filter_patterns or self.DEFAULT_FILTER_PATTERNS)
        # ]
        # self.filter_keywords = filter_keywords or set()
        self.min_line_length = min_line_length
        # self.custom_filter = custom_filter
    
    # def add_filter_pattern(self, pattern: str):
    #     """添加过滤正则模式"""
    #     self.filter_patterns.append(re.compile(pattern, re.IGNORECASE))
    #
    # def add_filter_keyword(self, keyword: str):
    #     """添加过滤关键词"""
    #     self.filter_keywords.add(keyword)
    #
    # def add_filter_keywords(self, keywords: List[str]):
    #     """批量添加过滤关键词"""
    #     self.filter_keywords.update(keywords)
    
    # def _should_filter_line(self, line: str) -> bool:
    #     """
    #     判断一行是否应该被过滤
    #
    #     Args:
    #         line: 待判断的行
    #
    #     Returns:
    #         True表示应该过滤（不保留），False表示保留
    #     """
    #     stripped = line.strip()
    #
    #     # 空行不过滤（保留用于段落分隔）
    #     if not stripped:
    #         return False
    #
    #     # 自定义过滤函数
    #     if self.custom_filter:
    #         if not self.custom_filter(stripped):
    #             return True
    #
    #     # 过短的行（可能是页眉页脚碎片）
    #     if len(stripped) < self.min_line_length:
    #         return True
    #
    #     # 正则模式匹配
    #     for pattern in self.filter_patterns:
    #         if pattern.match(stripped):
    #             return True
    #
    #     # 关键词匹配
    #     for keyword in self.filter_keywords:
    #         if keyword in stripped:
    #             return True
    #
    #     return False
    #
    # def _filter_text(self, text: str) -> str:
    #     """
    #     过滤文本中的无关内容
    #
    #     Args:
    #         text: 原始文本
    #
    #     Returns:
    #         过滤后的文本
    #     """
    #     if not text:
    #         return ""
    #
    #     lines = text.splitlines()
    #     filtered_lines = []
    #
    #     for line in lines:
    #         if not self._should_filter_line(line):
    #             filtered_lines.append(line)
    #
    #     # 合并连续的空行
    #     result_lines = []
    #     prev_empty = False
    #     for line in filtered_lines:
    #         is_empty = not line.strip()
    #         if is_empty:
    #             if not prev_empty:
    #                 result_lines.append(line)
    #             prev_empty = True
    #         else:
    #             result_lines.append(line)
    #             prev_empty = False
    #
    #     return "\n".join(result_lines).strip()
    #
    def extract_pages(self, pdf_path: str) -> List[PageContent]:
        """
        提取PDF所有页面的文本
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            PageContent列表
        """
        pages = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                raw_text = page.extract_text() or ""
                # filtered_text = self._filter_text(raw_text)
                
                pages.append(PageContent(
                    page_num=i,
                    # text=filtered_text,
                    text=raw_text
                    # raw_text=raw_text
                ))
        
        return pages
    
    def extract_text(self, pdf_path: str, join_pages: bool = False) -> str | List[str]:
        """
        提取PDF文本
        
        Args:
            pdf_path: PDF文件路径
            join_pages: 是否合并所有页面
            
        Returns:
            如果join_pages=True，返回合并后的字符串
            否则返回每页文本的列表
        """
        pages = self.extract_pages(pdf_path)
        texts = [p.text for p in pages]
        
        if join_pages:
            return "\n\n".join(texts)
        return texts


def extract_pdf_for_agent(
    pdf_path: str,
    # filter_keywords: List[str] = None,
    additional_patterns: List[str] = None
) -> List[PageContent]:
    """
    为Agent提取PDF内容的便捷函数
    
    Args:
        pdf_path: PDF文件路径
        filter_keywords: 需要过滤的关键词列表（如学校名、作者名）
        additional_patterns: 额外的正则过滤模式
        
    Returns:
        PageContent列表，可直接传给PDFStructureAgent
    """
    extractor = PDFTextExtractor()
    
    # if filter_keywords:
    #     extractor.add_filter_keywords(filter_keywords)
    #
    # if additional_patterns:
    #     for pattern in additional_patterns:
    #         extractor.add_filter_pattern(pattern)
    
    return extractor.extract_pages(pdf_path)


def get_pdf_text_by_page(pdf_file_path: str) -> List[str]:
    """
    按页提取PDF文本（兼容原有接口）
    
    Args:
        pdf_file_path: PDF文件路径
        
    Returns:
        每页文本的列表
    """
    with pdfplumber.open(pdf_file_path) as pdf:
        texts_in_page = []
        for page in pdf.pages:
            texts_in_page.append(page.extract_text() or "")
        return texts_in_page


# 测试代码
if __name__ == "__main__":
    import sys
    
    # 测试PDF路径
    test_path = "C:/Users/29938/Downloads/OSCC.pdf"
    
    # 创建提取器，不自定义过滤
    extractor = PDFTextExtractor()
    # extractor.add_filter_keywords(["中南大学", "作者", "指导教师"])
    
    # 提取并打印
    pages = extractor.extract_pages(test_path)
    
    for page in pages[:13]:  # 只打印前3页
        print(f"\n{'='*50}")
        print(f"第 {page.page_num} 页")
        print(f"{'='*50}")
        print(page.text[:500] if len(page.text) > 500 else page.text)
        print(f"\n[... 共 {len(page.text)} 字符]")
