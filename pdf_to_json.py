import os
# import comtypes.client
import subprocess
from pathlib import Path
import json
import re
import base64

from dotenv import load_dotenv
from pygments.lexer import default

# 默认输入输出路径(相对)
from txt_to_json2 import parse_mmd_to_json

# default_input_path="E:\workflow\ppt"
# default_output_path="E:\workflow\ppt"
# default_output_dir="E:\workflow\Output"
default_output_path=os.path.join(os.path.dirname(__file__), "workflow", "pdf")
default_input_path=os.path.join(os.path.dirname(__file__), "workflow", "pdf")
default_output_dir=os.path.join(os.path.dirname(__file__), "workflow", "Output")
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def pdf_to_json(filepath, user_id, output_path=default_output_path):
    load_dotenv(verbose=True)
    # 传入的filepath直接就是PDF文件的路径
    print(f"上传的PDF文件路径：{filepath}")

    # 提取不带后缀文件名
    filename = Path(filepath).stem
    pdf_path = filepath  # 直接使用传入的文件路径

    # 第二步：pdf to txt
    app_key = "sk-bzllfk7oftj7tv4he6rc7bfdz92iqtn0"
    # app_key = os.getenv("CSU_API_KEY")
    cmd = f"doc2x -k {app_key} -o {default_output_dir} --graphrag {pdf_path}"
    subprocess.run(cmd, shell=True, check=True)
    txt_dir = os.path.join(default_output_dir, filename)
    txt_filename = f"{filename}.txt"
    text_path = os.path.join(txt_dir, txt_filename)

    # 第三步：txt to json
    print(f"转化为TXT文件的相对路径：{text_path}")
    # 从路径读文件
    with open(text_path, 'r', encoding='utf-8') as f:
        text_content = f.read()
    """
    将文本内容解析为结构化JSON，保持原有目录结构
    第一行"////////////////////////"之后的内容作为论文标题
    """
   # # 初始化数据结构
  #  result = {
   #     "title": "",
   #     "sections": {}
   # }

    #current_section = None
    #current_subsection = None

   # lines = text_content.split('\n')

    # 提取论文标题（第一段）
   # for line in lines:
      #  if line.startswith("////////////////////////"):
       #     title_line = line.replace("////////////////////////", "").strip()
        #    if title_line:
        #        result["title"] = title_line
         #   break

    # 解析正文内容
    #for line in lines:
       # line = line.strip()
       # if not line:
        #    continue

        # 检测一级标题 (##)
       # if line.startswith("## "):
        #    section_name = line[3:].strip()
          #  result["sections"][section_name] = {
         #       "content": [],
           #     "subsections": {}
          #  }
          #  current_section = section_name
          #  current_subsection = None

        # 检测二级标题 (☐ 或 ])
      #  elif line.startswith("☐ ") or line.startswith("] ") or line.startswith("## ☐ "):
         #   subsection_name = re.sub(r'^(☐ |\] |## ☐ )', '', line).strip()
         #   if current_section:
           #     result["sections"][current_section]["subsections"][subsection_name] = []
           #     current_subsection = subsection_name

        # 检测三级标题 (-)
       # elif line.startswith("- "):
         #   item_content = line[2:].strip()
         #   if current_subsection:
           #     result["sections"][current_section]["subsections"][current_subsection].append(item_content)
          #  elif current_section:
           #     result["sections"][current_section]["content"].append(item_content)

        # 普通内容
       # else:
          #  if current_subsection:
          #      result["sections"][current_section]["subsections"][current_subsection].append(line)
          #  elif current_section:
          #      result["sections"][current_section]["content"].append(line)
          #  else:
                # 不属于任何章节的内容（如开头的汇报信息）
            #    if "title" not in result or line != result["title"]:
            #        if "misc" not in result:
            #            result["misc"] = []
             #       result["misc"].append(line)

    # 清理空内容
   # for section in list(result["sections"].keys()):
        #if not result["sections"][section]["content"] and not result["sections"][section]["subsections"]:
         #   del result["sections"][section]
    result=parse_mmd_to_json(text_content,user_id)
    # 解析并输出JSON
    print("ty",type(result))
    parsed_data = result
    # print("pdata",parsed_data)
    parsed_data_dumps=json.dumps(parsed_data, indent=2, ensure_ascii=False)
    print(type(parsed_data_dumps))
    return parsed_data_dumps

#针对paper的pdf解析，解析出特定格式的json文件
def paper_pdf_to_json(filepath, user_id, output_path=default_output_path):
    load_dotenv(verbose=True)
    # 传入的filepath直接就是PDF文件的路径
    print(f"上传的PDF文件路径：{filepath}")

    # 提取不带后缀文件名
    filename = Path(filepath).stem
    pdf_path = filepath  # 直接使用传入的文件路径

    # 第二步：pdf to txt
    app_key = "sk-bzllfk7oftj7tv4he6rc7bfdz92iqtn0"
    # app_key = os.getenv("CSU_API_KEY")
    cmd = f"doc2x -k {app_key} -o {default_output_dir} --graphrag {pdf_path}"
    subprocess.run(cmd, shell=True, check=True)
    txt_dir = os.path.join(default_output_dir, filename)
    txt_filename = f"{filename}.txt"
    text_path = os.path.join(txt_dir, txt_filename)

    # 第三步：txt to json
    print(f"转化为TXT文件的相对路径：{text_path}")
    # 从路径读文件
    with open(text_path, 'r', encoding='utf-8') as f:
        text_content = f.read()
    """
    将文本内容解析为结构化JSON，保持原有目录结构
    第一行"////////////////////////"之后的内容作为论文标题
    """

    result=parse_mmd_to_json(text_content,user_id)
    # 解析并输出JSON
    print("ty",type(result))
    parsed_data = result
    # print("pdata",parsed_data)
    parsed_data_dumps=json.dumps(parsed_data, indent=2, ensure_ascii=False)
    print(type(parsed_data_dumps))
    return parsed_data_dumps

# if __name__ == '__main__':
#     load_dotenv(verbose=True)
#     # MY_API_KEY = os.getenv("CSU_API_KEY")  # 这里修改为你获取的API-KEY
#     # API_BASE_URL = os.getenv("CSU_BASE_URL")
#     # print("API_BASE_URL",API_BASE_URL)
#     # print("MY_API_KEY",MY_API_KEY)
#     filepath = "C:/Users/29938/Downloads/test.pptx"
#     ppt_to_json(filepath,"sxs")