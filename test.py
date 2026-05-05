import queue
import time
from concurrent.futures import ThreadPoolExecutor
import os
import shutil
import subprocess
import tempfile
import threading
from tkinter import scrolledtext, filedialog, messagebox
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from collections import defaultdict
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
#from database import PaperDatabase
from filter import filter_paper_content

from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_community.document_transformers import LongContextReorder
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import CharacterTextSplitter

class EnhancedKnowledgeBaseApp:
    def __init__(self, root):
        # ... (保留原有初始化代码)

        self.root = root
        self.root.title("增强版知识库系统")
        self.root.geometry("900x700")

        # 初始化向量数据库组件
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vectorstore = Chroma(persist_directory="./chroma_db",
                                  embedding_function=self.embeddings)
        self.text_splitter = CharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=1
        )

        # 顶部控制面板
        self.control_frame = tk.Frame(root)
        self.control_frame.pack(fill=tk.X, padx=20, pady=5)

        # PDF上传按钮
        self.upload_btn = tk.Button(self.control_frame, text="上传PDF",
                                    command=self.upload_pdf)
        self.upload_btn.pack(side=tk.LEFT, padx=5)

        # 查看知识库按钮
        self.view_kb_btn = tk.Button(self.control_frame, text="查看知识库",
                                     command=self.view_knowledge_base)
        self.view_kb_btn.pack(side=tk.LEFT, padx=5)

        # 搜索框
        self.search_frame = tk.LabelFrame(root, text="知识检索", padx=10, pady=10)
        self.search_frame.pack(fill=tk.X, padx=20, pady=5)

        self.input_entry = tk.Entry(self.search_frame, width=60)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input_entry.bind("<Return>", self.on_enter_pressed)

        tk.Button(self.search_frame, text="搜索", command=self.search_knowledge).pack(side=tk.RIGHT)

        # 结果显示区（使用Notebook实现多标签）
        self.notebook = tk.ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        # 检索结果标签
        self.search_tab = tk.Frame(self.notebook)
        self.search_text = scrolledtext.ScrolledText(self.search_tab, wrap=tk.WORD)
        self.search_text.pack(fill=tk.BOTH, expand=True)
        self.notebook.add(self.search_tab, text="检索结果")

        # 知识库内容标签
        self.kb_tab = tk.Frame(self.notebook)
        self.kb_text = scrolledtext.ScrolledText(self.kb_tab, wrap=tk.WORD)
        self.kb_text.pack(fill=tk.BOTH, expand=True)
        self.notebook.add(self.kb_tab, text="知识库内容")

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(root, textvariable=self.status_var,
                                   relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 添加删除按钮
        self.delete_btn = tk.Button(self.control_frame, text="删除内容",
                                    command=self.delete_knowledge)
        self.delete_btn.pack(side=tk.LEFT, padx=5)

        self.update_status("系统就绪 | 可上传PDF或进行知识检索")
        self.progress_queue = queue.Queue()
        self.processing = False
        self.timeout = 240  # 40秒超时
        self.executor = ThreadPoolExecutor(max_workers=1)

    def show_pdf_processing_result(self, result):
        """显示PDF处理结果"""
        self.status_bar.config(text="就绪", foreground="green")

        # 创建新窗口显示结果
        result_window = tk.Toplevel(self.root)
        result_window.title("PDF处理结果")
        result_window.geometry("800x600")

        # 使用Notebook显示多标签结果
        notebook = ttk.Notebook(result_window)
        notebook.pack(fill=tk.BOTH, expand=True)

        # 基本信息标签
        info_frame = ttk.Frame(notebook)
        notebook.add(info_frame, text="基本信息")

        ttk.Label(info_frame, text=f"文件名: {result['filename']}", font=('Arial', 11)).pack(anchor='w', pady=5)

        # 内容标签
        content_frame = ttk.Frame(notebook)
        notebook.add(content_frame, text="提取内容")

        content_text = tk.Text(content_frame, wrap="word")
        scroll_y = ttk.Scrollbar(content_frame, command=content_text.yview)
        content_text.config(yscrollcommand=scroll_y.set)

        content_text.insert("1.0", result.get('content', '无内容'))
        content_text.config(state="disabled")

        content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # PDF信息标签
        if 'info' in result:
            info_frame = ttk.Frame(notebook)
            notebook.add(info_frame, text="PDF信息")

            info_text = tk.Text(info_frame, wrap="word")
            scroll_y = ttk.Scrollbar(info_frame, command=info_text.yview)
            info_text.config(yscrollcommand=scroll_y.set)

            info_text.insert("1.0", result['info'])
            info_text.config(state="disabled")

            info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # 错误信息标签
        if result['status'] == 'error':
            error_frame = ttk.Frame(notebook)
            notebook.add(error_frame, text="错误信息")

            ttk.Label(error_frame, text=result.get('message', '未知错误'), foreground="red").pack()

    def on_enter_pressed(self, event):
        """回车键触发搜索"""
        self.search_knowledge()


    def process_pdf_with_terminal(self, pdf_path, output_dir):
            """
            调用终端指令处理PDF文件
            """

            print("./Output/"+Path(pdf_path).name)
           # txt_path = os.path.join(output_dir, "extracted.txt")
            app_key="sk-bzllfk7oftj7tv4he6rc7bfdz92iqtn0"
            cmd = f"doc2x -k {app_key} --graphrag {pdf_path}"
            subprocess.run(cmd, shell=True, check=True)
            cc = Path(pdf_path).name.rstrip('pdf')
            co = Path(cc).name.rstrip('.')
            print("ok"+"./Output/" + co+ "/" + co + ".txt")
            # 读取处理结果

            with open("./Output/" + co + "/" + co + ".txt", 'r', encoding='utf-8') as f:
                content = f.read()
           ## with open(info_path, 'r', encoding='utf-8') as f:
             ##   info = f.read()

            return {
                'filename': os.path.basename(pdf_path),
                'content': content[:1000] + "...",  # 只显示前1000字符
               # 'info': info,
                'status': 'success'
            }
    def upload_pdf(self):
        """PDF上传入口函数"""
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not file_path:
            return

        # 文件名检查
        filename = Path(file_path).name
        if ' ' in filename:
            messagebox.showerror("文件名错误", "文件名中不允许包含空格！\n当前文件名: '{}'".format(filename))
            return

        # 检查是否已存在
        if self._check_source_exists(file_path):
            messagebox.showwarning("警告", f"文件已存在:\n{file_path}")
            return

        # 初始化处理状态
        self.processing = True
        self.process_start_time = time.time()
        self.upload_btn.config(state=tk.DISABLED)

        # 创建进度窗口
        self._create_progress_window()

        # 启动处理线程
        self.executor.submit(self._process_pdf_in_thread, file_path)

        # 启动进度监控
        self.root.after(100, self._update_progress_from_queue)

    def _create_progress_window(self):
        """创建进度显示窗口"""
        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title("PDF处理进度")
        self.progress_window.geometry("400x180")
        self.progress_window.protocol("WM_DELETE_WINDOW", self._cancel_processing)

        # 进度组件
        self.progress_label = tk.Label(self.progress_window, text="准备开始处理...")
        self.progress_label.pack(pady=5)

        self.progress_bar = ttk.Progressbar(
            self.progress_window, orient=tk.HORIZONTAL,
            length=300, mode='determinate'
        )
        self.progress_bar.pack(pady=5)

        self.time_label = tk.Label(self.progress_window, text="已用时间: 0秒")
        self.time_label.pack()

        self.detail_label = tk.Label(self.progress_window, text="", wraplength=380)
        self.detail_label.pack(pady=5)

        tk.Button(
            self.progress_window, text="取消",
            command=self._cancel_processing
        ).pack(pady=5)

    def _process_pdf_in_thread(self, file_path):
        """在独立线程中处理PDF"""
        try:
            # 步骤1: 准备临时目录 (10%)
            filename=Path(file_path).name
            self._update_progress(10, "创建临时工作目录...")#用于更新进度条
            temp_dir = tempfile.mkdtemp()
            temp_pdf_path = os.path.join(temp_dir, "uploaded.pdf")
            shutil.copy(file_path, temp_pdf_path)

            # 步骤2: 调用doc2x处理 (30%)
            self._update_progress(30, "调用doc2x解析PDF内容...")
            result = self._process_with_doc2x(file_path)

            # 步骤3: 过滤内容 (60%)
            self._update_progress(60, "过滤文本内容...")
            self.show_pdf_processing_result(result)
            cc = Path(file_path).name.rstrip('pdf')
            co = Path(cc).name.rstrip('.')#得到文件名（不含路径和后缀）
            print("out" + "./Output/" + co + "/" + co + ".txt")
            print("son" + Path(file_path).name.rstrip('.pdf') + ".txt")
            print("stam:" + Path(file_path).stem)
            try:
                # 读取文件内容
                with open("./Output/" + co + "/" + co + ".txt", 'r', encoding='utf-8') as file:
                    content = file.read()
                    print(f"\n===== 文件: {filename} =====\n")
                    print(content)
                pure_content = filter_paper_content(content)
                print("dell", pure_content)
                with open(co + ".txt", 'w', encoding='utf-8') as f:
                    f.write(pure_content)
                self._update_progress(80, "保存处理结果...")
                loader = TextLoader(co + ".txt", encoding="UTF-8")
                documents = loader.load()
                print("文件", documents)
                # 分割文本
                # text_splitter = CharacterTextSplitter(chunk_size=1500, chunk_overlap=1)
                # 传统方法分割文本
                #==============================================================================
                # docs = self.text_splitter.split_documents(documents)
                #==============================================================================
                # ai分割文本
                #==============================================================================
                from utils.textspliter_LLM import ThinkingModelTextSplitter
                splitter = ThinkingModelTextSplitter(model_client=None, model_name="DeepSeek-V4-Flash")
                docs = splitter.split_documents(documents)
                #==============================================================================
                print("docs", docs)
                self._update_progress(90, "添加到知识库...")
                self.vectorstore.add_documents(docs)

                # 完成 (100%)
                self._update_progress(100, "处理完成!")
                self.progress_queue.put(('success', file_path, result))
            except UnicodeDecodeError:
                try:
                    # 如果utf-8失败，尝试gbk编码
                    with open(file_path, 'r', encoding='gbk') as file:
                        content = file.read()
                        print(f"\n===== 文件: {filename} (GBK编码) =====\n")

                except Exception as e:
                    print(f"无法读取文件 {filename}: {e}")
            messagebox.showinfo("成功", f"PDF内容已添加到知识库:\n{file_path}")
            self.update_status(f"PDF处理完成: {file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"处理PDF失败:\n{str(e)}")
            self.update_status(f"错误 | {str(e)}")


    def _process_with_doc2x(self, pdf_path):
        """使用doc2x处理PDF（带模拟进度）"""
        # 模拟处理过程
        progress = 3
        self._update_progress(
               progress,
               f"解析PDF中... ({3}/10)"
             )
        print("./Output/" + Path(pdf_path).name)
        # txt_path = os.path.join(output_dir, "extracted.txt")
        app_key = "sk-bzllfk7oftj7tv4he6rc7bfdz92iqtn0"
        cmd = f"doc2x -k {app_key} --graphrag {pdf_path}"
        subprocess.run(cmd, shell=True, check=True)
        cc = Path(pdf_path).name.rstrip('pdf')
        co = Path(cc).name.rstrip('.')
        print("ok" + "./Output/" + co + "/" + co + ".txt")
        # 读取处理结果

        with open("./Output/" + co + "/" + co + ".txt", 'r', encoding='utf-8') as f:
            content = f.read()


        if not self.processing:
            raise Exception("处理被取消")

           # progress = 30 + i * 5  # 30-80% 之间
            #self._update_progress(
             #   progress,
            #    f"解析PDF中... ({i}/10)"
           # )
           # time.sleep(1)  # 模拟处理耗时

        # 模拟返回结果
        return {
            'filename': Path(pdf_path).name,
            'content': content[:1000] + "...",
            'status': 'success'
        }

    def _update_progress(self, value, message):
        """更新进度信息（线程安全）"""
        self.progress_queue.put(('progress', value, message))

    def _update_progress_from_queue(self):
        """从队列获取更新并刷新UI"""
        try:
            while True:
                msg = self.progress_queue.get_nowait()

                if msg[0] == 'progress':
                    _, value, message = msg
                    self.progress_bar['value'] = value
                    self.progress_label.config(text=message)

                    # 更新耗时显示
                    elapsed = int(time.time() - self.process_start_time)
                    self.time_label.config(text=f"已用时间: {elapsed}秒")

                    # 详细状态
                    self.detail_label.config(text=f"进度: {value}% - {message}")
                    self.update_status(message)

                elif msg[0] == 'success':
                    _, file_path, result = msg
                    self._on_processing_success(file_path, result)
                    break

                elif msg[0] == 'error':
                    _, error_msg = msg
                    self._on_processing_error(error_msg)
                    break

        except queue.Empty:
            # 检查超时
            if time.time() - self.process_start_time > self.timeout:
                self._on_processing_timeout()
            else:
                self.root.after(100, self._update_progress_from_queue)

    def _on_processing_success(self, file_path, result):
        """处理成功回调"""
        if hasattr(self, 'progress_window'):
            self.progress_window.destroy()

        self.upload_btn.config(state=tk.NORMAL)
        self.show_pdf_processing_result(result)
        messagebox.showinfo("成功", f"PDF处理完成: {Path(file_path).name}")
        self.update_status("就绪")

    def _on_processing_error(self, error_msg):
        """处理错误回调"""
        if hasattr(self, 'progress_window'):
            self.progress_window.destroy()

        self.upload_btn.config(state=tk.NORMAL)
        messagebox.showerror("处理错误", error_msg)
        self.update_status(f"错误: {error_msg}")

    def _on_processing_timeout(self):
        """处理超时回调"""
        self.processing = False
        if hasattr(self, 'progress_window'):
            self.progress_window.destroy()

        self.upload_btn.config(state=tk.NORMAL)
        messagebox.showerror("超时", f"处理超过{self.timeout}秒，已自动取消")
        self.update_status("处理超时")

    def _cancel_processing(self):
        """用户取消处理"""
        self.processing = False
        if hasattr(self, 'progress_window'):
            self.progress_window.destroy()

        self.upload_btn.config(state=tk.NORMAL)
        self.update_status("用户取消处理")

    def _cancel_processing(self):
        """取消处理操作"""
        self.processing = False
        if hasattr(self, 'progress_window'):
            self.progress_window.destroy()
        self.upload_btn.config(state=tk.NORMAL)
        self.update_status("用户取消处理")

    def _check_source_exists(self, file_path):
        """检查source是否已存在"""
        try:
            collection = self.vectorstore._collection
            existing = collection.get(where={"source": file_path}, limit=1)
            return len(existing['ids']) > 0
        except Exception as e:
            print(f"检查source出错: {str(e)}")
            return False

    def view_knowledge_base(self):
        """查看知识库内容（按source分组）"""
        try:
            self.update_status("正在加载知识库内容...")

            # 获取所有文档
            all_docs = self.vectorstore.get()['metadatas']

            # 按source分组
            source_dict = defaultdict(list)
            for doc in all_docs:
                if 'source' in doc:
                    source_dict[doc['source']].append(doc)

            # 清空并显示内容
            self.kb_text.delete(1.0, tk.END)

            if not source_dict:
                self.kb_text.insert(tk.END, "知识库为空\n")
                return

            for source, docs in source_dict.items():
                self.kb_text.insert(tk.END, f"=== 来源: {source} ===\n")
                self.kb_text.insert(tk.END, f"文档块数量: {len(docs)}\n")
                self.kb_text.insert(tk.END, "=" * 50 + "\n\n")

            self.notebook.select(self.kb_tab)  # 自动切换到知识库标签
            self.update_status(f"知识库加载完成 | 共 {len(source_dict)} 个来源")

        except Exception as e:
            self.kb_text.delete(1.0, tk.END)
            self.kb_text.insert(tk.END, f"加载知识库出错: {str(e)}\n")
            self.update_status(f"错误 | {str(e)}")

    def search_knowledge(self, query_text=None):
        """执行知识检索"""
        #query = self.input_entry.get().strip()
        query = query_text if query_text else self.input_entry.get().strip()
        if not query:
            self.update_status("错误 | 请输入查询内容")
            return

        try:
            self.update_status(f"搜索中 | 查询: {query}")

            # 执行相似度搜索
            docs = self.vectorstore.similarity_search(query, k=6)

            # 显示结果
            self.search_text.delete(1.0, tk.END)

            if not docs:
                self.search_text.insert(tk.END, "未找到相关结果\n")
            else:
                for i, doc in enumerate(docs, 1):
                    self.search_text.insert(tk.END, f"结果 {i}:\n")
                    self.search_text.insert(tk.END, f"内容: {doc.page_content}\n")
                    self.search_text.insert(tk.END, f"来源: {doc.metadata.get('source', '未知')}\n")
                    self.search_text.insert(tk.END, "-" * 50 + "\n")

            self.notebook.select(self.search_tab)  # 自动切换到结果标签
            self.update_status(f"完成 | 找到 {len(docs)} 个结果 | 查询: {query}")
            return docs
        except Exception as e:
            self.search_text.delete(1.0, tk.END)
            self.search_text.insert(tk.END, f"检索出错: {str(e)}\n")
            self.update_status(f"错误 | {str(e)}")
            return []
    def delete_knowledge(self):
        """删除知识库内容"""
        # 创建删除对话框
        delete_window = tk.Toplevel(self.root)
        delete_window.title("删除知识库内容")
        delete_window.geometry("500x300")

        # 获取所有来源
        sources = self._get_all_sources()

        # 删除选项框架
        option_frame = tk.LabelFrame(delete_window, text="删除选项", padx=10, pady=10)
        option_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 单选按钮变量
        delete_option = tk.IntVar(value=1)

        # 删除选项
        tk.Radiobutton(option_frame, text="按来源删除", variable=delete_option, value=1).pack(anchor=tk.W)
        tk.Radiobutton(option_frame, text="清空整个知识库", variable=delete_option, value=2).pack(anchor=tk.W)

        # 来源选择下拉菜单
        source_label = tk.Label(option_frame, text="选择来源:")
        source_label.pack(anchor=tk.W, pady=(10, 0))

        source_var = tk.StringVar()
        source_dropdown = ttk.Combobox(option_frame, textvariable=source_var, values=sources)
        source_dropdown.pack(fill=tk.X, pady=5)
        if sources:
            source_dropdown.current(0)

        # 确认按钮
        def execute_delete():
            if delete_option.get() == 1:  # 按来源删除
                source = source_var.get()
                if not source:
                    messagebox.showerror("错误", "请选择来源")
                    return
                self._delete_by_source(source)
            else:  # 清空知识库
                self._clear_knowledge_base()
            delete_window.destroy()

        tk.Button(delete_window, text="确认删除", command=execute_delete).pack(pady=10)

        # 取消按钮
        tk.Button(delete_window, text="取消", command=delete_window.destroy).pack()

    def _get_all_sources(self):
        """获取所有来源列表"""
        all_docs = self.vectorstore.get()['metadatas']
        sources = list(set(doc.get('source') for doc in all_docs if 'source' in doc))
        return sorted(sources) if sources else []

    def _delete_by_source(self, source):
        """按来源删除文档"""
        try:
            # 获取所有匹配的文档ID
            collection = self.vectorstore._collection
            result = collection.get(where={"source": source})

            if not result['ids']:
                messagebox.showwarning("警告", f"未找到来源为 '{source}' 的文档")
                return

            # 执行删除
            collection.delete(ids=result['ids'])
            # 删除相关文件资源
            deleted_files = []
            cc = Path(source).name.rstrip('pdf')
            co = Path(cc).name.rstrip('.')
            output_dir = "./Output/"+co
            print("delete_dir",output_dir)
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
                deleted_files.append(output_dir)


            print("source",source)
            # 2. 删除同级目录的.txt文件
            txt_file = source
            if os.path.exists(txt_file):
                os.remove(txt_file)
                deleted_files.append(txt_file)

            msg = f"已删除来源 '{source}' 的 {len(result['ids'])} 个文档块"
            if deleted_files:
                msg += f"\n同时删除了相关文件:\n" + "\n".join(deleted_files)


            messagebox.showinfo("成功", )
            self.update_status(f"已删除来源: {source}")

        except Exception as e:
            messagebox.showerror("错误", f"删除失败: {str(e)}")
            self.update_status(f"删除错误 | {str(e)}")

    def _clear_knowledge_base(self):
        """清空整个知识库"""
        try:
            if not messagebox.askyesno("确认", "确定要清空整个知识库吗？此操作不可恢复！"):
                return

            # 重置向量数据库
            collection = self.vectorstore._collection
            collection.delete(where={})  # 删除所有文档

            # 重置界面显示
            self.kb_text.delete(1.0, tk.END)
            self.search_text.delete(1.0, tk.END)

            messagebox.showinfo("成功", "知识库已清空")
            self.update_status("知识库已重置")

        except Exception as e:
            messagebox.showerror("错误", f"清空失败: {str(e)}")
            self.update_status(f"清空错误 | {str(e)}")

    def update_status(self, message):
        """更新状态栏"""
        self.status_var.set(message)
        self.root.update()


if __name__ == "__main__":
    root = tk.Tk()
    app = EnhancedKnowledgeBaseApp(root)
    root.mainloop()