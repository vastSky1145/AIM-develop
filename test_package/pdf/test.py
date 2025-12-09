# def parse_pdf(file_path, user_id="default_user"):
#     """
#     解析PDF文件并返回JSON格式字符串
    
#     解析流程:
#     1. 使用 pdfplumber 提取 PDF 纯文本内容
#     2. PDF内容需包含层级标题格式，parse_mmd_to_json 会根据以下格式解析层级结构:
#        - 1级: "## 1 标题" 或 "Chapter 1 标题"  (如: ## 1 Introduction)
#        - 2级: "1.1 标题" 或 "* 1.1 标题"       (如: 2.1 Background)
#        - 3级: "1.1.1 标题"                     (如: 2.1.1 Details)
#        - 4级: "1.1.1.1 标题"                   (如: 2.2.1.1 Subsection)
#        - 5级: "(1) 标题"                       (如: (1) Item one)
#     3. 返回 JSON 格式的字符串
    
#     Args:
#         file_path: PDF文件路径
#         user_id: 用户ID，默认为 "default_user"
        
#     Returns:
#         str: JSON格式的字符串，包含 paper_title, uid, sections 等字段
#     """
    # 使用 pdfplumber 提取 PDF 文本内容
    # text_content = ""
    # with pdfplumber.open(file_path) as pdf:
    #     for page in pdf.pages:
    #         page_text = page.extract_text()
    #         if page_text:
    #             text_content += page_text + "\n"
    #
    # print(f"成功从PDF提取文本，共 {len(text_content)} 字符")
    #
    # # 使用 parse_mmd_to_json 解析文本内容为结构化数据
    # result = parse_mmd_to_json(text_content, user_id)
    #
    # # 返回 JSON 格式的字符串
    # json_str = json.dumps(result, indent=2, ensure_ascii=False)
    # print(f"解析完成，返回JSON类型: {type(json_str)}")
    #
    # return json_str

    # with pdfplumber.open(file_path) as pdf:
    #     total_pages = len(pdf.pages)
    #     all_text = []
    #     for i, page in enumerate(pdf.pages, start=1):
    #         text = page.extract_text()
    #         all_text.append({
    #             "page": i,
    #             "text": text if text else ""
    #         })
    #     print(all_text)
    #     return all_text