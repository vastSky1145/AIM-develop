from docling.document_converter import DocumentConverter

# 初始化转换器
converter = DocumentConverter()

# 指定文件路径（也可以是 URL）
# source = "/home/ght/aim-develop/AIM-develop/test_package/pdf/test.pdf"
source = "/home/ght/aim-develop/AIM-develop/test_package/pdf/“AI+大数据”在论文写作指导课程教学中的价值_陈利.pdf"

# 执行转换
result = converter.convert(source)

# 导出为 Markdown
print(result.document.export_to_markdown())mj