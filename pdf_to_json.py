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

    # 确保输出目录存在
    if not os.path.exists(default_output_dir):
        os.makedirs(default_output_dir, exist_ok=True)
        print(f"创建输出目录：{default_output_dir}")

    # 提取不带后缀文件名
    filename = Path(filepath).stem
    pdf_path = filepath  # 直接使用传入的文件路径

    # 第二步：pdf to txt
    app_key = "sk-bzllfk7oftj7tv4he6rc7bfdz92iqtn0"
    # app_key = os.getenv("CSU_API_KEY")
    cmd = f"doc2x -k {app_key} -o {default_output_dir} --graphrag {pdf_path}"
    
    # 临时保存当前代理设置
    old_http_proxy = os.environ.get('http_proxy')
    old_https_proxy = os.environ.get('https_proxy')
    old_HTTP_PROXY = os.environ.get('HTTP_PROXY')
    old_HTTPS_PROXY = os.environ.get('HTTPS_PROXY')
    
    try:
        # doc2x 是国内服务，不需要代理，临时取消代理
        os.environ.pop('http_proxy', None)
        os.environ.pop('https_proxy', None)
        os.environ.pop('HTTP_PROXY', None)
        os.environ.pop('HTTPS_PROXY', None)
        
        print(f"执行命令：{cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # 合并 stdout 和 stderr 以便分析
        full_output = (result.stdout or "") + "\n" + (result.stderr or "")
        print(f"doc2x 输出：{full_output}")
        
        # doc2x 即使失败也可能返回退出码 0，需要检查输出内容
        if "Failed to convert" in full_output or "failed to convert" in full_output:
            # 提取错误信息
            error_lines = [line for line in full_output.split('\n') if 'Failed' in line or 'error' in line.lower()]
            error_msg = '\n'.join(error_lines) if error_lines else "PDF 解析失败，请检查文件是否为有效的 PDF"
            raise Exception(f"doc2x 解析失败：{error_msg}")
        
        if result.returncode != 0:
            raise Exception(f"doc2x 命令执行失败，退出码：{result.returncode}")
            
    except subprocess.CalledProcessError as e:
        raise Exception(f"doc2x 命令执行失败：{e.stderr if e.stderr else str(e)}")
    finally:
        # 恢复代理设置
        if old_http_proxy:
            os.environ['http_proxy'] = old_http_proxy
        if old_https_proxy:
            os.environ['https_proxy'] = old_https_proxy
        if old_HTTP_PROXY:
            os.environ['HTTP_PROXY'] = old_HTTP_PROXY
        if old_HTTPS_PROXY:
            os.environ['HTTPS_PROXY'] = old_HTTPS_PROXY
    
    txt_dir = os.path.join(default_output_dir, filename)
    txt_filename = f"{filename}.txt"
    text_path = os.path.join(txt_dir, txt_filename)

    # 第三步：txt to json
    print(f"转化为TXT文件的相对路径：{text_path}")
    
    # 检查文件是否存在
    if not os.path.exists(text_path):
        # 列出输出目录中的内容，帮助调试
        if os.path.exists(txt_dir):
            files_in_dir = os.listdir(txt_dir)
            print(f"目录 {txt_dir} 中的文件：{files_in_dir}")
        else:
            print(f"目录 {txt_dir} 不存在")
            # 列出 Output 目录中的内容
            if os.path.exists(default_output_dir):
                dirs_in_output = os.listdir(default_output_dir)
                print(f"Output 目录中的内容：{dirs_in_output}")
        raise FileNotFoundError(f"doc2x 未能生成预期的文件：{text_path}")
    
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

# if __name__ == '__main__':
#     load_dotenv(verbose=True)
#     # MY_API_KEY = os.getenv("CSU_API_KEY")  # 这里修改为你获取的API-KEY
#     # API_BASE_URL = os.getenv("CSU_BASE_URL")
#     # print("API_BASE_URL",API_BASE_URL)
#     # print("MY_API_KEY",MY_API_KEY)
#     filepath = "C:/Users/29938/Downloads/test.pptx"
#     ppt_to_json(filepath,"sxs")