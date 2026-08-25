import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from AI import llm
import json
from mongodb import PaperDatabase
from models import ResearchPaper, ResearchPaperManager
from ppt_to_json import ppt_to_json
from test import EnhancedKnowledgeBaseApp
import threading
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import os
os.environ["TRANSFORMERS_NO_TF"] = "1"
import tkinter.font as tkfont

class PaperAssistantApp:
    def __init__(self, root, user_id):
        self.root = root
        self.root.title("学术论文助手")
        self.root.geometry("1200x800")
        self.user_id = user_id
        # 初始化数据库和状态
        self.db = PaperDatabase()
        self.current_paper = ResearchPaper(paper_id="default", title="New Paper", author="user1")
        self.current_mode = None  # writing/editing
        self.current_controller = None
        self.paper = ResearchPaperManager()
        # 主界面布局
        # self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.embeddings = HuggingFaceEmbeddings(model_name="/home/ght/ai_models/paraphrase-multilingual-MiniLM-L12-v2")
        self.vectorstore = Chroma(persist_directory="./chroma_db",
                                 embedding_function=self.embeddings)
        self.setup_ui()
        self.update_paper_list(user_id)
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(size=12)

        text_font = tkfont.Font(family="Arial", size=12)
        self.root.option_add("*TLabel.Font", text_font)
        self.root.option_add("*Text.Font", text_font)
        self.root.option_add("*TButton.Font", text_font)
        self.root.option_add("*TCombobox.Font", text_font)
        # self.load_paper_data()

    def setup_ui(self):
        # 三栏布局
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)

        # A区 (20%)
        self.setup_A_area()

        # B区 (60%)
        self.setup_B_area()

        # C区 (20%)
        self.setup_C_area()

        # 状态栏
        self.status_bar = ttk.Label(self.root, text="就绪", foreground="green")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    """A区"""

    def setup_A_area(self):
        # 创建 Frame 并直接添加到 PanedWindow（无需 pack）
        self.A_pane = ttk.PanedWindow(self.main_paned, orient=tk.VERTICAL)
        self.main_paned.add(self.A_pane, weight=1)
        self.content_frame = ttk.Frame(self.A_pane)

        # 创建 Text 控件并填充 Frame
        self.content_textA = tk.Text(self.content_frame, wrap="word",font=("Arial", 12))
        self.content_textA.pack(expand=True, fill=tk.BOTH)  # 关键：让文本区域填满 Frame

        # 设置字体样式
        self.content_textA.tag_configure("heading", font=('Arial', 12, 'bold'))
        self.content_textA.tag_configure("title", font=('Arial', 12, 'bold'))

        # 插入标题文本
        self.content_textA.insert(tk.END, f"用户{self.user_id}已有的论文\n", "heading")
        self.content_textA.insert(tk.END, "\n")  # 空行，模拟 pady=15 的间距

        # 插入 Title 文本
        self.content_textA.insert(tk.END, "Title:\n", "title")

        scroll_y = ttk.Scrollbar(self.content_frame, command=self.content_textA.yview)
        self.content_textA.config(yscrollcommand=scroll_y.set)
        self.content_textA.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # 添加按钮到 content_frame，并确保它们在文本框下方
        self.button_frame = ttk.Frame(self.A_pane)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        self.button_delete = tk.Button(self.button_frame, text="删除论文", width=15, command=self.on_delete_paper)
        self.button_delete.pack(side=tk.TOP, expand=True)


        self.button_submit = tk.Button(self.button_frame, text="提交知识", width=15, command=self.on_upload_knowledage)# command=self.on_upload_ppt)
        self.button_submit.pack(side=tk.TOP, expand=True)

        self.button_upload = tk.Button(self.button_frame, text="上传PPT", width=15,
                                       command=self.on_upload_ppt_filedialog)
        self.button_upload.pack(side=tk.TOP, expand=True)

        self.button_save = tk.Button(self.button_frame, text="保存论文", width=15,
                                       command=self.on_save_paper)
        self.button_save.pack(side=tk.TOP, expand=True)

        self.content_textA.bind("<Button-1>", self.on_text_click)
        # 新增：记录提交按钮插入文本的起始位置

        # 将 content_frame 添加到 A_pane
        self.A_pane.add(self.content_frame, weight=9)
        self.A_pane.add(self.button_frame, weight=1)

        def disable_drag(event):
            return "break"

        self.A_pane.bind("<ButtonPress-1>", disable_drag)
        self.A_pane.bind("<B1-Motion>", disable_drag)

    def on_delete_paper(self):
        try:
            # 获取当前选中的行
            index = self.content_textA.index(tk.INSERT)
            line_number = index.split('.')[0]
            line_text = self.content_textA.get(f"{line_number}.0", f"{line_number}.end").strip()

            if not line_text or not line_text.startswith("第"):
                messagebox.showwarning("提示", "请点击选择要删除的论文标题行")
                return

            # 提取论文标题
            if ": " in line_text:
                selected_title = line_text.split(": ", 1)[1]
            else:
                messagebox.showwarning("提示", "未识别的标题格式")
                return

            # 确认是否删除
            confirm = messagebox.askyesno("确认删除", f"是否确定删除论文：\n\n{selected_title}")
            if not confirm:
                return

            # 调用数据库删除
            delete_success = self.db.delete_paper_by_title_and_uid(selected_title, self.user_id)
            if delete_success:
                messagebox.showinfo("删除成功", f"论文《{selected_title}》已删除")
                self.update_paper_list(self.user_id)
            else:
                messagebox.showerror("删除失败", "未能从数据库中删除该论文")

        except Exception as e:
            messagebox.showerror("错误", f"删除时发生错误：\n{str(e)}")

    def on_upload_ppt(self):
        # 调用一个函数返回几个字符串
        strings = self.get_strings_from_ppt()
        # 找到 Title: 之后的位置
        title_index = self.content_textA.search("Title:", "1.0", tk.END)
        if title_index:
            insert_index = f"{title_index}+1l"  # 在 Title: 下一行插入
            for string in strings:
                # 确保 insert_index 是有效的
                if insert_index:
                    self.content_textA.insert(insert_index, string + "\n")
                    # 更新 insert_index 到下一行
                    insert_index = f"{insert_index}+1l"
                else:
                    # 如果 insert_index 无效，则停止插入
                    break
        else:
            # 如果找不到 "Title:"，则插入到文本框的末尾
            self.content_textA.insert(tk.END, "\n".join(strings) + "\n")
    def on_upload_knowledage(self):
        kb_window = tk.Toplevel(self.root)
        kb_window.title("增强版知识库系统")
        kb_window.geometry("900x700")
        EnhancedKnowledgeBaseApp(kb_window)
        #self.open_knowledge_base_window()


    def on_upload_ppt_filedialog(self):
        self.papers = []
        # 打开文件选择对话框，只允许选择PPT文件
        #file_path = filedialog.askopenfilename(filetypes=[("PPT Files", "*.ppt;*.pptx")])
        #if file_path:
            # 在这里可以添加上传文件到服务器或其他处理逻辑
           # print(f"Selected file: {file_path}")
        #else:
            #return
        # strings = f"上传文件:{file_path}"
        # self.content_textA.insert(tk.END, strings + "\n")
        # ppt处理流程

        #json_content = ppt_to_json(file_path,self.user_id)
       # with open("./sxs_json.json", "r", encoding="utf-8") as f:
        #    json_content = json.load(f)
       # self.papers.append(json_content)
        #json_content = json.loads(open("./sxs_json.json", "r", encoding="utf-8"))
        #if json_content:
         #   tip = "解析成功"
        #else:
         #   tip = "解析失败"
        #print(tip)

        file_path = filedialog.askopenfilename(filetypes=[("PPT Files", "*.ppt;*.pptx")])
        if file_path:
            # 在这里可以添加上传文件到服务器或其他处理逻辑
            print(f"Selected file: {file_path}")
        strings = f"上传文件:{file_path}"
        self.content_textA.insert(tk.END, strings + "\n")
        # ppt处理流程
        json_content = json.loads(ppt_to_json(file_path,"sxs"))
        if json_content:
            messagebox.showerror("进程", "解析成功")
        else:
            messagebox.showerror("进程", "解析失败")
        self.db.save_paper(json_content)
        self.papers.append(json_content)
        #self.content_textA.insert(tk.END, tip + "\n")
        # self.content_textA.insert(tk.END, tip + "\n")
        # # 连接 MongoDB
        #client = MongoClient("mongodb://localhost:27017/")
       # db = client["research_papers"]
        #collection = db["papers"]
        # 插入MongoDB数据库
        #insertJson(collection,json_content)
        # 获取所有论文的title,类型为列表
       # titles = get_doc_by_ID(collection, uid)
        print(type(json_content))
        print(json_content['paper_title'])
        titles = json_content['paper_title']
        #titles=list(titles)
        print(titles)
        # 展示在A区
        # 清除之前的内容,但是保留用户信息与Title字样
        
        #self.content_textA.delete('1.0', tk.END)
        # 插入标题文本
        #self.content_textA.insert(tk.END, f"用户{self.user_id}已有的论文\n", "heading")
       # self.content_textA.insert(tk.END, "\n")  # 空行，模拟 pady=15 的间距
        # 插入 Title 文本
       # self.content_textA.insert(tk.END, "Title:\n", "title")
        # 更新的内容
        #for i, title in enumerate(titles, start=1):
        title_str = f"第{1}篇: {titles}"
        self.content_textA.insert(tk.END, title_str + "\n")

    def on_save_paper(self):
        from datetime import datetime
        import os
        import re
        # 如果没有当前论文标题，使用默认值
        if not hasattr(self, 'now_paper_title'):
            self.now_paper_title = "未命名论文"
        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        illegal_chars = r'[\/:*?"<>|\x00-\x1f]'
        title = re.sub(illegal_chars, '_', self.now_paper_title)
        filename = f"{title}_{timestamp}.json"
        # 创建JSON第一级
        paper_data = {
            "paper_title": self.now_paper_title,
            "uid": getattr(self, 'now_uid', self.user_id),  # 使用当前uid或默认用户ID
            "sections": []
        }
        
        # 递归遍历树形结构并构建章节
        def build_sections(parent, parent_id=""):
            sections = []
            children = self.tree.get_children(parent)

            for i, child in enumerate(children, start=1):
                # 生成节点ID (如: "ppt1", "ppt1.1", "ppt1.2.1"等)
                node_id = f"{parent_id}.{i}" if parent_id else f"ppt{i}"
                
                # 获取节点内容
                node_text = self.tree.item(child, "text")
                node_values = self.tree.item(child, "values")
                content = node_values[0] if node_values else ""

                # 构建当前节点
                section = {
                    "title": node_text,
                    "content": content,
                    "children": build_sections(child, node_id),
                    "id": node_id
                }
                sections.append(section)
            
            return sections

        # 从根节点开始构建
        paper_data["sections"] = build_sections('')
        
        # 保存到文件
        try:
            # 创建保存目录(如果不存在)
            os.makedirs("saved_papers", exist_ok=True)
            filepath = os.path.join("saved_papers", filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(paper_data, f, ensure_ascii=False, indent=4)
            
            messagebox.showinfo("保存成功", f"论文已保存为:\n{filepath}")
        except Exception as e:
            messagebox.showerror("保存失败", f"保存时出错:\n{str(e)}")
        

    def get_strings_from_ppt(self):
        # 这里模拟返回几个字符串，实际应用中需要实现从PPT中提取内容
        return ["String 1", "String 2", "String 3"]

    def on_text_click(self, event):
        # 获取点击位置的行和列
        click_index = self.content_textA.index(f"@{event.x},{event.y}")
        print("cc",click_index)
        # 获取点击位置所在行的文本

        line_text = self.content_textA.get(f"{click_index.split('.')[0]}.0", f"{click_index.split('.')[0]}.end")
        # 增加判断逻辑
        line_title = line_text.strip().split(": ", 1)[-1]
        #valid_strings = ["String 1", "String 2", "String 3"]
        #if line_text.strip() in valid_strings:
        if(len(line_text) == 0):
            return
        print(f"你点击了: {line_text}")

        # 获取标题
        for paper in self.papers:
            # with open("./sxs_json.json", "r", encoding="utf-8") as f:
            #     paper = json.load(f)
            if (paper["paper_title"] not in line_text):
                continue
            self.now_paper_title = paper["paper_title"]
            self.now_uid = paper["uid"]
            break
        else:
            print("没有找到对应的标题")
            # 这里可以调用你想要的函数
        self.load_paper_to_B(line_text)

    def open_knowledge_base_window(self):
        """弹出一个新的增强知识库窗口并保存引用"""
        kb_window = tk.Toplevel(self.root)
        kb_window.title("增强版知识库系统")
        kb_window.geometry("1200x600")
        self.kb_app = EnhancedKnowledgeBaseApp(kb_window)

    def load_paper_to_B(self, text):
        # 这里可以实现你想要的功能，例如弹出消息框显示点击的文本
        # messagebox.showinfo("点击信息", f"你点击的文本是: {text}")
        if(len(self.papers) == 0):
            return 
        print("text",text)
        for paper in self.papers:
            # with open("./sxs_json.json", "r", encoding="utf-8") as f:
            #     paper = json.load(f)
            if (paper["paper_title"] not in text):
                continue
            sections = paper["sections"]
            # 清空B区的treeView
            self.tree.delete(*self.tree.get_children())
            # 加载当前paper的Tree
            """
            def load_section(parent_item,section):
                Abstract = self.tree.insert(parent_item, 'end', text=section["title"],values=(section["content"],))
                if(len(section["children"]) == 0):
                    return 
                for section in section["children"]:
                    load_section(Abstract,section)
            for section in sections:
                load_section("",section)
            """
            def load_section(parent_item, section, prefix="ppt", index=1):
                current_id = f"{prefix}.{index}" if prefix != "" else f"ppt{index}"
                # 将 id 存入 values 的第二个元素中（第一个通常是 content）
                tree_item = self.tree.insert(
                    parent_item,
                    'end',
                    text=section["title"],
                    values=(section["content"], current_id)
                )
                for i, child in enumerate(section.get("children", []), start=1):
                    load_section(tree_item, child, prefix=current_id, index=i)

            for i, section in enumerate(sections, start=1):
                load_section("", section, prefix="", index=i)

        self.update_C_area()

    """保存编辑的修改"""

    def save_changes(self):
        selected = self.outline_tree.selection()
        if selected:
            section_name = self.outline_tree.item(selected[0], "text").split(". ")[1].lower()
            content = self.show_text.get("1.0", tk.END).strip()
            self.paper.update_section(section_name, content, "edited")
        messagebox.showinfo("保存成功", "内容已暂存")
        

    """切换编辑锁定状态"""

    def toggle_edit_lock(self):
        if self.show_text.cget("state") == "normal":
            self.show_text.config(state="disabled")
        else:
            self.show_text.config(state="normal")

    """B区"""

    def setup_B_area(self):
        self.work_paned = ttk.PanedWindow(self.main_paned, orient=tk.VERTICAL)
        self.main_paned.add(self.work_paned, weight=3)

        # 上部：内容显示区
        self.content_frame = ttk.Frame(self.work_paned)

        # 创建树窗口
        self.tree = ttk.Treeview(self.content_frame, selectmode="extended")
        style = ttk.Style()
        style.configure("Treeview", font=("Arial", 15))  # 设置树的字体
        style.configure("Treeview.Heading", font=("Arial", 13, "bold"))  # 表头字体
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 创建根节点
        self.Abstract = self.tree.insert('', 'end', text="Abstract")
        self.Introduction = self.tree.insert('', 'end', text="Introduction")
        self.Background = self.tree.insert('', 'end', text="Background")
        self.Method = self.tree.insert('', 'end', text="Method")
        self.Experiment = self.tree.insert('', 'end', text="Experiment")
        self.Conclusion = self.tree.insert('', 'end', text="Conclusion")

        # 为每个根节点创建子树
        self.create_subtree(self.tree, self.Abstract)
        self.create_subtree(self.tree, self.Introduction)
        self.create_subtree(self.tree, self.Background)
        self.create_subtree(self.tree, self.Method)
        self.create_subtree(self.tree, self.Experiment)
        self.create_subtree(self.tree, self.Conclusion)

        self.work_paned.add(self.content_frame, weight=7)

        # 绑定选择事件
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        # 绑定右键事件
        self.tree.bind("<Button-3>", self.on_right_click_B)
    def on_right_click_B(self, event):
        # 获取点击的项
        item = self.tree.identify_row(event.y)  # 获取鼠标位置的项
        if item:  # 如果点击在项上
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="编辑", command=self.edit_selected_item)
            menu.add_command(label="展开", command=lambda: self.expand_all_children(item))
            # self.tree.selection_set(item)  # 选中该项
            menu.post(event.x_root, event.y_root)  # 显示菜单

    def expand_all_children(self, item):
        self.tree.item(item, open=True)
        for child in self.tree.get_children(item):
            self.expand_all_children(child)

    def create_subtree(self, Tree, Parent):
        parent_text = self.tree.item(Parent)['text']  # 获取父节点的显示文本
        self.child1 = self.tree.insert(Parent, "end", text=f"{parent_text}1")
        self.child2 = self.tree.insert(Parent, "end", text=f"{parent_text}2")

        style = ttk.Style()
        style.layout('Treeview.Item', [('Treeitem.padding', {
            'sticky': 'nswe',
            'children': [('Treeitem.text', {'sticky': 'nswe'})]
        })])

    def _run_llm(self,prompt,text_widget2):
        try:
            """
            completion = llm.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "<YOUR_SITE_URL>",  # Optional. Site URL for rankings on openrouter.ai.
                    "X-Title": "<YOUR_SITE_NAME>",  # Optional. Site title for rankings on openrouter.ai.
                },
                extra_body={},
                model="deepseek/deepseek-r1-0528:free",
                messages=[
                    {
                        "role": "user",
                        "content": {prompt}
                    }
                ]
            )
            """
            completion = llm.chat.completions.create(
                # model="gemini-2.5-flash-preview-05-20",
                # model="deepseek-v3",
                model="QwQ-32B",
                reasoning_effort="low",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {
                        "role": "user",
                        "content": f"{prompt}"
                    }
                ]
            )

            # text_output = llm.invoke(full_prompt)
            text_output = completion.choices[0].message.content#choices[0].message.content

            print("output", text_output)
            text_widget2.delete('1.0', tk.END)
            text_widget2.insert(tk.END, text_output)
        # self.root.after(0, update_ui)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("生成失败", f"调用模型出错：\n{str(e)}"))

    def _run_llm_in_background(self, prompt_template, existing_text, kb_content, text_widget2, section_text):
        #import tkinter as tk

        #try:
            # 检查 prompt 模板中是否包含两个 $$
            if prompt_template.count('$$') < 2:
                self.root.after(0, lambda: messagebox.showerror("模板错误", "Prompt 模板中必须包含两个 $$ 作为占位符"))
                return

            # 构造最终 prompt

            if prompt_template.count('$$') == 2:
                full_prompt = prompt_template.replace('$$', existing_text, 1)
                full_prompt = full_prompt.replace('$$', kb_content, 1)
            elif prompt_template.count('$$') > 2:
                full_prompt = prompt_template.replace('$$', existing_text, 1)
                full_prompt = full_prompt.replace('$$', kb_content, 1)
                full_prompt = full_prompt.replace('$$', section_text, 1)

            if not full_prompt.strip():
                self.root.after(0, lambda: messagebox.showerror("错误", "生成的 Prompt 内容为空"))
                return
            print("prompt:", full_prompt)

            # 调用大模型

            completion = llm.chat.completions.create(
                # extra_headers={
                #     "HTTP-Referer": "<YOUR_SITE_URL>",  # Optional. Site URL for rankings on openrouter.ai.
                #     "X-Title": "<YOUR_SITE_NAME>",  # Optional. Site title for rankings on openrouter.ai.
                # },
                extra_body={"chat_template_kwargs": {"thinking": True}},
                # model="deepseek/deepseek-r1-0528:free",
                model="deepseek-v3",
                messages=[
                    {"role": "system", "content": "你是一个有问必答的AI助手。"},
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                max_tokens = 1024,
                temperature = 0.7,
                stream = False,
            )
            # text_output = llm.invoke(full_prompt)
           # text_output = completion.choices[0].message.content
            text_output = completion.choices[0].message.content


            #completion = llm.chat.completions.create(
             #   model="gemini-2.5-flash-preview-05-20",
              #  reasoning_effort="low",
              #  messages=[
               #     {"role": "system", "content": "You are a helpful assistant."},
               #     {
                #        "role": "user",
                #        "content": f"{full_prompt}"
                #    }
                #]
            #)

            # text_output = llm.invoke(full_prompt)
            #text_output = completion.choices[0].message.content
            #print("output",text_output)
            # 更新 UI 内容必须在主线程中执行
            #def update_ui():
            text_widget2.delete('1.0', tk.END)
            text_widget2.insert(tk.END, text_output)
            #self.root.after(0, update_ui)

       # except Exception as e:
            #self.root.after(0, lambda: messagebox.showerror("生成失败", f"调用模型出错：\n{str(e)}"))


    def open_reference_selector(self):
        if not hasattr(self, "papers") or not self.papers:
            messagebox.showerror("错误", "请先上传并解析PPT")
            return

        paper = self.papers[0]  # 当前论文
        section_list = []

        def flatten_sections(sections):
            for sec in sections:
                section_list.append((sec["id"], sec["title"]))
                if sec.get("children"):
                    flatten_sections(sec["children"])

        flatten_sections(paper["sections"])

        selector_win = tk.Toplevel(self.root)
        selector_win.title("选择目录范围")
        selector_win.geometry("500x300")

        ttk.Label(selector_win, text="起始目录:").pack(anchor='w', padx=10, pady=5)
        start_var = tk.StringVar()
        start_combo = ttk.Combobox(selector_win, textvariable=start_var,
                                   values=[f"{sid} - {title}" for sid, title in section_list])
        start_combo.pack(fill='x', padx=10)

        ttk.Label(selector_win, text="结束目录:").pack(anchor='w', padx=10, pady=5)
        end_var = tk.StringVar()
        end_combo = ttk.Combobox(selector_win, textvariable=end_var,
                                 values=[f"{sid} - {title}" for sid, title in section_list])
        end_combo.pack(fill='x', padx=10)

        result_text = tk.Text(selector_win, height=10, wrap='word',font=("Arial", 12))
        result_text.pack(fill='both', expand=True, padx=10, pady=10)

        def on_extract():
            try:
                start_id = start_var.get().split(" - ")[0]
                end_id = end_var.get().split(" - ")[0]
                ref_text = self.extract_reference_text(start_id, end_id, paper["sections"])
                result_text.delete('1.0', tk.END)
                result_text.insert(tk.END, ref_text)
            except Exception as e:
                messagebox.showerror("提取失败", str(e))

        extract_btn = ttk.Button(selector_win, text="提取参考文字", command=on_extract)
        extract_btn.pack(pady=5)

    def extract_reference_text(self, start_id: str, end_id: str, sections: list) -> str:
        collected = []
        found_start = False

        def dfs(section):
            nonlocal found_start
            sid = section.get("id", "")
            if sid == start_id:
                found_start = True
            if found_start:
                collected.append(section)
            if sid == end_id:
                return True
            for child in section.get("children", []):
                if dfs(child):
                    return True
            return False

        for sec in sections:
            if dfs(sec):
                break

        reference_text = ""
        for sec in collected:
            reference_text += f"{sec['title']}\n"
            reference_text += f"{sec['content']}\n\n"

        return reference_text.strip()

    def edit_item_B(self,item):
        if not item:
            return
        print("selected item:", item)
        # 创建编辑弹窗
        edit_window = tk.Toplevel(self.root)
        edit_window.title("编辑内容")
        edit_window.geometry("1600x800")#"500x400"
        # 创建编辑区域


        main_frame = ttk.Frame(edit_window)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Label(left_frame, text="已有内容", font=("Arial", 10, "bold")).pack(anchor="w")
        text1 = tk.Text(left_frame, height=10, width=50, wrap='word',font=("Arial", 12))
        text = "title = "+self.tree.item(item)['text']

        #print("text",text)
        if self.tree.item(item)['values'] and self.tree.item(item)['values'][0]:
            print("已有内容",self.tree.item(item)['values'] )
            text += "\n\ncontent{" + self.tree.item(item)['values'][0] + '}'
            #text += self.tree.item(item)['values'][0]
            print("text",text)
        #text = self.generate_text_from_tree(self.tree, item)
        text1.insert(tk.END, text)
        text1.pack(fill=tk.BOTH, expand=True)

        ttk.Label(left_frame, text="生成内容", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 0))
        text2 = tk.Text(left_frame, height=15, width=50, wrap='word',font=("Arial", 12))
        text2.pack(fill=tk.BOTH, expand=True)

        # === 中间知识库 + 目录复选框 ===
        knowledge_frame = ttk.Frame(main_frame)
        knowledge_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- 起始/结束目录选择 ---
        ref_select_frame = ttk.LabelFrame(knowledge_frame, text="目录范围选择（提取参考内容）", padding=5)
        ref_select_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        start_var = tk.StringVar(master=edit_window)
        end_var = tk.StringVar(master=edit_window)

        ttk.Label(ref_select_frame, text="起始目录:").grid(row=0, column=0, sticky="w")
        start_combo = ttk.Combobox(ref_select_frame, textvariable=start_var, width=30)
        start_combo.grid(row=0, column=1, sticky="ew", padx=5)

        ttk.Label(ref_select_frame, text="结束目录:").grid(row=1, column=0, sticky="w")
        end_combo = ttk.Combobox(ref_select_frame, textvariable=end_var, width=30)
        end_combo.grid(row=1, column=1, sticky="ew", padx=5)
        sec_text = tk.Text( knowledge_frame, height=15, width=50, wrap='word',font=("Arial", 12))
        sec_text.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        def on_extract_reference():
            if not hasattr(self, "papers") or not self.papers:
                messagebox.showerror("错误", "未找到已加载论文")
                return
            try:
                paper = self.papers[0]
                start_id = start_var.get().split(" - ")[0]
                end_id = end_var.get().split(" - ")[0]
                ref_text = self.extract_reference_text(start_id, end_id, paper["sections"])
                sec_text.delete("1.0", tk.END)
                sec_text.insert(tk.END, ref_text)
            except Exception as e:
                messagebox.showerror("提取失败", str(e))
        extract_btn = ttk.Button(ref_select_frame, text="提取参考文字", command=lambda: on_extract_reference())
        extract_btn.grid(row=2, column=0, columnspan=2, pady=5)

        # --- 知识库标题 ---
        kb_label = ttk.Label(knowledge_frame, text="知识库内容", font=("Arial", 10, "bold"))
        kb_label.pack(anchor="w")

        kb_text = tk.Text(knowledge_frame, height=15, width=40, wrap="word",font=("Arial", 12))
        kb_text.pack(fill=tk.BOTH, expand=True)

        # 填充目录下拉框（基于 self.papers）
        if hasattr(self, "papers") and self.papers:
            paper = self.papers[0]
            section_list = []

            def flatten_sections(sections):
                for sec in sections:
                    sid, title = sec.get("id", ""), sec.get("title", "")
                    if sid:
                        section_list.append(f"{sid} - {title}")
                    flatten_sections(sec.get("children", []))

            flatten_sections(paper["sections"])
            start_combo["values"] = section_list
            end_combo["values"] = section_list

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        def search_and_display_knowledge():
            if hasattr(self, 'vectorstore'):
                query_result = []
                query = text1.get("1.0", tk.END).strip()
                docs = self.vectorstore.similarity_search(query, k=6)
                if not docs:
                    print("nofind")
                else:
                    for i, doc in enumerate(docs, 1):
                        query_result.append(doc.page_content)
                kb_text.delete("1.0", tk.END)
                if query_result:
                    for i, doc in enumerate(query_result, 1):
                        kb_text.insert(tk.END, "第"+str(i)+"条知识:\n"+doc + "\n\n")
                else:
                    kb_text.insert(tk.END, "未找到相关内容")
            else:
                messagebox.showwarning("提示", "知识库窗口未打开")

        search_btn = ttk.Button(knowledge_frame, text="检索", command=search_and_display_knowledge)
        search_btn.pack(pady=5)

        #if self.tree.item(item)['values'] and self.tree.item(item)['values'][0]:
           #    text += "\n\ncontent{" + self.tree.item(item)['values'][0] + '}'
        #text1.insert(tk.END, text)
        #text1.pack(fill=tk.BOTH, expand=True)
        #item = self.tree.item(item)['values'][0]
        ppt_id = self.tree.item(item)['values'][1] if len(self.tree.item(item)['values']) > 1 else "ppt0"
        print("item",ppt_id)
        #text2 = tk.Text(left_frame, height=15, width=50, wrap='word')
        #text2.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        prompt_label = ttk.Label(right_frame, text="Prompt 模板:已有内容和知识库内容用$$占位", font=("Arial", 10, "bold"))
        prompt_label.pack(anchor="w")

        prompt_text = tk.Text(right_frame, height=25, width=30, wrap='word',font=("Arial", 12))
        get = self.db.get_prompt(ppt_id=ppt_id)
        # print(get)
        if(get):
            prompt_template = get
        else :
            prompt_template = f"你是一个研究视频传输的专家，是一个美国教授。 请将下述已有内容\n$$\n补全为完整的段落.\n要求保持子目录组织结构不变。\n补全段落时以下面的知识库位参考资料\n$$。\n写作逻辑要和以下章节的逻辑内容呼应\n$$。\n补全段落时要求生成的内容是对已有内容的补充，不改变已有内容的目录结构，可以适当对已有内容的句子扩充，但要保证句子之间逻辑结构和原来一致，扩充内容不要超过1句。知识库中的知识只能作为参考，总结归纳其中语义相关的知识作为参照，而不是直接引用。知识库中出现的图表，若已有内容中没有，则认为该知识不相关，不能作为参考。生成内容和知识库中的原句不可以一样。 latex公式不要编译。要求英文撰写。凝练成逻辑严密的一段话。不要目录结构，不要出现目录编号。生成的文字中要包括已有内容里对图或者表的引用。要求语言风格比较学术化。"

        prompt_text.insert(tk.END, prompt_template)
        prompt_text.pack(fill=tk.BOTH, expand=True)


        # 按钮框架
        btn_frame = ttk.Frame(edit_window)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        # 生成、修改、保存按钮
        generate_btn = ttk.Button(btn_frame, text="生成", command=lambda: self.generate_content(text1,text2,prompt_text,kb_text,sec_text))
        modify_btn = ttk.Button(btn_frame, text="修改", command=lambda: self.modify_content(text2))
        save_btn = ttk.Button(btn_frame, text="保存", command=lambda: self.save_tree_content(item, text2))

        generate_btn.pack(side=tk.LEFT, padx=5)
        modify_btn.pack(side=tk.LEFT, padx=5)
        save_btn.pack(side=tk.LEFT, padx=5)


    def edit_selected_item(self):
        selected_item = self.tree.selection()
        if not selected_item:
            return
        item = selected_item[0]
        self.edit_item_B(item)


    def on_tree_select(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return
        item = selected_item[0]
        # 展开/折叠点击的项（可选）
        if self.tree.item(item, "open"):
            self.tree.item(item, open=False)
        else:
            self.tree.item(item, open=True)
        """
        children = self.tree.get_children(item)
        # 检查是否是第二层目录
        # if parent and self.tree.parent(parent):  # 有父节点且父节点也有父节点说明不是第二层
        #     return
        # if not parent:  # 没有父节点说明是根节点
        #     return
        if(children) :
            return 
        self.edit_item_B(item)
        """


    def generate_content(self, text_widget1,text_widget2,prompt_widget,kb_text,section_text):
        text_input = text_widget1.get('1.0', tk.END).strip()

        prompt_template = prompt_widget.get('1.0', tk.END).strip()
        existing_text = text_widget1.get('1.0', tk.END).strip()
        kb_content = kb_text.get('1.0', tk.END).strip()
        section_text = section_text.get('1.0', tk.END).strip()
        threading.Thread(
            target=self._run_llm_in_background,
            args=(prompt_template, existing_text, kb_content, text_widget2,section_text),
            daemon=True
        ).start()
        # 用特殊标记 $$ 作为占位符


    def modify_content(self, text_widget2):
        # 创建弹框
        modify_window = tk.Toplevel(self.root)
        modify_window.title("修改内容")
        modify_window.geometry("400x300")

        # 创建文本框
        modify_text = tk.Text(modify_window, wrap="word", height=10, width=40,font=("Arial", 12))
        modify_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # 创建确定按钮
        def on_confirm():
            # 获取弹框中的文本内容
            modify_content = modify_text.get("1.0", tk.END).strip()
            # 获取 text_widget1 中的内容
            original_content = text_widget2.get("1.0", tk.END).strip()
            # TODO 通过original_content和modify_content调用AI生成修改
            combined_content = "这是已有内容"+ original_content + "\n" + modify_content

            threading.Thread(
                target=self._run_llm,
                args=(combined_content, text_widget2),
                daemon=True
            ).start()
            # 将合并后的内容放入 text_widget2
            text_widget2.delete("1.0", tk.END)
            text_widget2.insert("1.0", combined_content)
            # 关闭弹框
            modify_window.destroy()

        confirm_button = tk.Button(modify_window, text="确定", command=on_confirm)

        confirm_button.pack(pady=10)

    def save_tree_content(self, item, text_widget2):
        # 获取 text_widget2 中的内容
        content = text_widget2.get('1.0', tk.END).strip()
        # 更新 Treeview 中 item 的文本
        self.tree.item(item, text=content)
        # 提示保存成功
        messagebox.showinfo("成功", "内容已保存")
        self.update_C_area()
    """C区大纲面板"""

    def setup_C_area(self):
        self.outline_frame = ttk.Frame(self.main_paned, width=240)
        self.outline_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        self.main_paned.add(self.outline_frame, weight=1)

        self.outline_label = ttk.Label(self.outline_frame, text="论文大纲", font=('Arial', 12, 'bold'))
        self.outline_label.pack(pady=10)

        self.outline_listbox = tk.Listbox(self.outline_frame, activestyle='none', font=("Arial", 16))
        self.outline_listbox.pack(fill=tk.BOTH, expand=True, padx=5)

        # 初始化大纲结构
        self.sections = {
            "1": "Introduction",
            "2": "Background",
            "3": "Methodology",
            "4": "Experiments",
            "5": "Results",
            "6": "Discussion",
            "7": "Conclusion"
        }

        # for sec_num, sec_name in self.sections.items():
        #     # 初始状态未完成，文本包含 ×
        #     self.outline_listbox.insert(tk.END, f"{sec_num}. {sec_name} ×")
        self.update_C_area()
        # self.outline_listbox.bind("<<ListboxSelect>>", self.on_section_selected)

    def update_C_area(self):
        # 清空当前列表内容
        self.outline_listbox.delete(0, tk.END)
        # 获取 self.tree 的第一级节点
        first_level_items = self.tree.get_children()
        print("=========update_C_area==========")
        print(first_level_items)
        # 遍历第一级节点，添加到列表框中
        for item in first_level_items:
            item_text = self.tree.item(item, "text")
            # 初始状态为未完成，标记为 ×
            self.outline_listbox.insert(tk.END, f"x {item_text}")
        # 绑定右键点击事件
        self.outline_listbox.bind("<Button-3>", self.on_right_click_C)

    def on_right_click_C(self, event):
        # 获取点击的项
        index = self.outline_listbox.nearest(event.y)
        if index == -1:
            return
        # 获取点击的项文本
        item_text = self.outline_listbox.get(index)
        # 创建右键菜单
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="编辑", command=lambda: self.edit_item_C(index))
        menu.add_command(label="删除", command=lambda: self.delete_item(index))
        menu.add_command(label="标记", command=lambda: self.toggle_mark(index))
        menu.add_command(label="插入", command=lambda: self.insert_item(index))
        
        # 显示菜单
        menu.post(event.x_root, event.y_root)

    def find_tree_id_by_text(self,tree,target_text,item_id=""):
        current_text = tree.item(item_id,"text")
        if(current_text == target_text):
            return item_id
        for child_id in tree.get_children(item_id):
            result = self.find_tree_id_by_text(tree,target_text,child_id)
            if(result != None):
                return result
        return None
    def generate_text_from_tree(self, tree, item_id="", indent_level=0):
        """
        递归生成树形结构的文本
        """
        text = ""
        # 获取当前节点的文本和值
        item_text = tree.item(item_id, "text")
        item_values = tree.item(item_id, "values")
        # 添加当前节点的文本
        text += "    " * indent_level + item_text + "\n"
        # 如果当前节点有值，添加值内容
        if item_values and item_values[0]:
            text += "    " * indent_level + "content{"+item_values[0] + "}\n"
        # 递归处理子节点
        for child_id in tree.get_children(item_id):
            text += self.generate_text_from_tree(tree, child_id, indent_level + 1)
        return text
    def generate_tree_from_text(self, text, tree, parent_item="",index_in_parent=0):
        """
        根据文本内容生成树结构
        :param text: 输入的文本内容
        :param tree: ttk.Treeview对象
        :param parent_item: 父节点ID，默认为空表示根节点
        """
        # 预处理阶段：解析content块
        protected_text = []
        temp_content = None
        brace_count = 0
        
        for idx,line in enumerate(text.splitlines()):
            # if(idx == 0): continue
            stripped = line.strip()
            if temp_content is None:
                # 不在content块中
                if stripped.startswith("content{") and not stripped.endswith("}"):
                    temp_content = line
                    brace_count = 1  # 已经有一个{
                elif stripped.startswith("content{") and stripped.endswith("}"):
                    protected_text.append(line)
                else:
                    protected_text.append(line)
            else:
                # 正在收集多行content
                temp_content += "\n" + line
                # 计算大括号数量
                brace_count += line.count("{") - line.count("}")
                # 检查是否结束
                if brace_count == 0 and stripped.endswith("}"):
                    protected_text.append(temp_content)
                    temp_content = None
        
        # 处理保护后的文本
        stack = []  # 用于跟踪缩进层级和对应的item
        prev_item = None  # 记录上一个创建的item
        
        for line in protected_text:
            if not line.strip():  # 跳过空行
                continue
                
            # 计算缩进级别
            indent_level = 0
            original_line = line  # 保存原始行用于content检查
            while line.startswith("    "):
                indent_level += 1
                line = line[4:]
                
            # 检查是否是content行
            stripped_line = line.strip()
            if stripped_line.startswith("content{") and stripped_line.endswith("}"):
                if prev_item is not None:
                    # 提取content内容，保留原始换行符
                    content = original_line.strip()[8:-1].strip()
                    # 更新上一个item的values
                    tree.item(prev_item, values=(content,))
                continue
            
            # 创建当前节点
            if(indent_level > 0):
                parent = stack[indent_level-1][1]
                index = "end"
            else:
                parent = parent_item
                index = index_in_parent
            current_item = tree.insert(
                parent=parent,
                index=index,
                text=line.strip(),
                values=()
            )
            
            # 更新堆栈
            if indent_level >= len(stack):
                stack.append((indent_level, current_item))
            else:
                stack[indent_level] = (indent_level, current_item)
            
            # 更新prev_item
            prev_item = current_item


    def edit_item_C(self, index):
        # 获取点击的项文本
        item_text = self.outline_listbox.get(index)
        # 去掉标记字符
        item_text = item_text[2:]
        
        # 创建编辑弹窗
        edit_window = tk.Toplevel(self.root)
        edit_window.title("编辑项")
        edit_window.geometry("600x300")
        
        # 生成树形结构
        item_id = self.find_tree_id_by_text(self.tree,item_text,"")
        text = self.generate_text_from_tree(self.tree,item_id)
        

        # 创建文本框
        edit_text = tk.Text(edit_window, wrap="word", height=5, width=30,font=("Arial", 12))
        edit_text.insert(tk.END, text)
        edit_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # 创建确定按钮
        def on_save():
            new_text = edit_text.get("1.0", tk.END).strip()
            title = new_text.splitlines()[0].strip()
            # 更新列表项
            nonlocal index
            self.outline_listbox.delete(index)
            self.outline_listbox.insert(index, f"√ {title}")
            # 更新tree
            nonlocal item_id
            for child in self.tree.get_children(item_id):
                self.tree.delete(child)
            # 生成新的子树
            parent_id = self.tree.parent(item_id)
            index_in_parent = self.tree.get_children(parent_id).index(item_id)
            self.generate_tree_from_text(new_text, self.tree, parent_id,index_in_parent)
            # 删除原先的子树
            self.tree.delete(item_id)  # 删除该节点
            edit_window.destroy()

        
        confirm_button = tk.Button(edit_window, text="保存", command=on_save)
        confirm_button.pack(pady=5)

    def delete_item(self, index):
        # 获取点击的项文本
        item_text = self.outline_listbox.get(index)
        # 去掉标记字符（× 或 √）和末尾的空格
        item_text = item_text[2:].strip()
        
        # 查找 self.tree 的第一级节点
        first_level_items = self.tree.get_children()
        found = False
        
        for item in first_level_items:
            # 获取节点的文本
            tree_item_text = self.tree.item(item, "text")
            if tree_item_text == item_text:
                # 删除 tree 中的节点及其子树
                self.tree.delete(item)
                # 删除 listbox 中的项
                self.outline_listbox.delete(index)
                found = True
                break
        
        # 如果未找到同名项，弹出提示框
        if not found:
            messagebox.showerror("错误", "错误！大纲与tree不匹配")

    def toggle_mark(self, index):
        # 获取点击的项文本
        item_text = self.outline_listbox.get(index)
        # 切换标记
        if item_text[0:2] == 'x ':
            new_text = "√ " + item_text[2:] 
        else:
            new_text = "x " + item_text[2:]
        # 更新列表项
        self.outline_listbox.delete(index)
        self.outline_listbox.insert(index, new_text)

    def insert_item(self, index):
        self.outline_listbox.insert(index+1, "x 新章节")
        self.insert_item_after_index(index, parent='', text='新章节', values=("",))
    def insert_item_after_index(self, index, parent='', text='', values=("",)):
        # 获取所有parent的子节点
        children = self.tree.get_children(parent)
        # 检查index是否有效
        if index < 0 or index >= len(children):
            raise ValueError("Invalid index")
        # 获取指定index位置的节点ID
        target_item = children[index]

        # 在该节点后面插入新节点
        new_item = self.tree.insert(parent, index+1, text=text, values=values)
        return new_item
        
    def on_section_selected(self, event):
        widget = event.widget
        selected_index = widget.curselection()
        if selected_index:
            self.D_window()

    "D区弹窗"

    def D_window(self):
        # 生成窗口
        new_window = tk.Toplevel(self.root)
        new_window.title("自由编译区")
        new_window.geometry("720x540")

        # 创建一个框架用于放置文本编辑区和滚动条
        text_frame = ttk.Frame(new_window)
        text_frame.pack(fill=tk.BOTH, expand=True)

        # 创建滚动条，父组件设置为 text_frame
        scroll_y = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # 文本编辑区
        self.edit_text = tk.Text(text_frame, wrap='word', yscrollcommand=scroll_y.set,font=("Arial", 12))
        self.edit_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 将滚动条与文本框关联
        scroll_y.config(command=self.edit_text.yview)

        # 创建一个框架用于放置按钮
        button_frame = ttk.Frame(new_window)
        button_frame.pack(fill=tk.X, pady=10)

        # 添加按钮
        button = ttk.Button(button_frame, text="保存")
        button.pack(anchor=tk.CENTER)


    def update_paper_list(self,uid):
        print("开始加载已有论文")
        print("user_id",self.user_id)
        result = self.db.query_papers_by_uid(self.user_id)
        if(result["success"]):
            print("result",result["papers"])
            self.papers = result["papers"]
        else: self.papers=[]
        matched_count = result["matched_count"]
        titles = []
        if result["success"]:
            try:
                for i, paper in enumerate(result["papers"]):
                    print(f"paper['paper_title']:{paper['paper_title']}")
                    titles.append(paper["paper_title"])
            except Exception as e:
                print("error",e)
        # 连接 MongoDB
#        client = MongoClient("mongodb://localhost:27017/")
       # db = client["research_papers"]
       # collection = db["papers"]
        # 获取所有论文的title,类型为列表
      #  titles = get_doc_by_ID(collection, uid)
        # 展示在A区
        # 清除之前的内容,但是保留用户信息与Title字样
        self.content_textA.delete('1.0', tk.END)
        # 插入标题文本
        self.content_textA.insert(tk.END, f"用户{self.user_id}已有的论文\n", "heading")
        self.content_textA.insert(tk.END, "\n")  # 空行，模拟 pady=15 的间距
        # 插入 Title 文本
        self.content_textA.insert(tk.END, "Title:\n", "title")
        # 更新的内容
        for i, title in enumerate(titles, start=1):
            title_str = f"第{i}篇: {title}"
            self.content_textA.insert(tk.END, title_str + "\n")
        print("加载完毕")
      #  for i, title in enumerate(titles, start=1):
        #    title_str = f"第{i}篇: {title}"
        #    self.content_textA.insert(tk.END, title_str + "\n")
        #print("加载完毕")

if __name__ == "__main__":
    root = tk.Tk()
    uid="sxs"
    # uid="12345"
    app = PaperAssistantApp(root, uid)
    app.update_paper_list(uid)
    root.mainloop()