from langchain_openai import ChatOpenAI#, OpenAI
import os
import requests
from langchain_community.chat_models import QianfanChatEndpoint
from openai import OpenAI
# 配置 API 密钥
API_KEY = "your_api_key"
SECRET_KEY = "your_secret_key"

# 初始化客户端
client = requests.Session()
client.auth = (API_KEY, SECRET_KEY)
#llm=ChatOpenAI(
 #   base_url="http://openrouter.ai/api/v1",
  #  api_key = os.getenv("OPENAI_API_KEY"),
  #  model="google/gemini-2.0-flash-001",
#)

# 此处是原来所用的api
# llm1 = ChatOpenAI(
#     base_url="https:://qianfan.baidubce.com/v3",#"https://api.deepseek.com/v3",  # DeepSeek的base_url
#     api_key="bce-v3/ALTAK-mHWwdNXMc1KofFHdXNRHt/35c9ebdc73932203d877f631def118b45cbaf631", #"sk-byurrpvmvjaebikpmhkrwrxgqfxniaujbhvnyyadouxecanz",  # DeepSeek平台的API Key
#     #model="gpt-4o",  # 或者 "deepseek-coder"，根据你要用的模型选
#     temperature=0.2
# )
# llm = QianfanChatEndpoint(
#     qianfan_ak="uAF3mfERnVPtlEdj5ad3LfI2",#"https://api.deepseek.com/v3",  # DeepSeek的base_url
#     qianfan_sk="2s6Cetnpzah9JFnbmUdNEaBvOpZvQbzm", #"sk-byurrpvmvjaebikpmhkrwrxgqfxniaujbhvnyyadouxecanz",  # DeepSeek平台的API Key
# )
# #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
#
# llm = OpenAI(
#   base_url="https://openrouter.ai/api/v1",
#   # model="deepseek/deepseek-r1-0528:free",
#   api_key="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",
# )
#
# llm = OpenAI(
#     api_key="AIzaSyC3lJr1v8cf4ZjQ2C0_47RoE6Ny60JKqVE",
#     base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
# )

# 此处是中南大学api

# sk-sZi4nNPwuQhqBNonGrHL0yATSQKHOi88AJiiGFQfdG5xoD1l
# https://api.chat.csu.edu.cn/v1

# llm1 = ChatOpenAI(
#     base_url="https://api.chat.csu.edu.cn/v1",#"https://api.deepseek.com/v3",  # DeepSeek的base_url
#     api_key="sk-sZi4nNPwuQhqBNonGrHL0yATSQKHOi88AJiiGFQfdG5xoD1l", #"sk-byurrpvmvjaebikpmhkrwrxgqfxniaujbhvnyyadouxecanz",  # DeepSeek平台的API Key
#     #model="gpt-4o",  # 或者 "deepseek-coder"，根据你要用的模型选
#     temperature=0.2
# )
# llm = QianfanChatEndpoint(
#     qianfan_ak="uAF3mfERnVPtlEdj5ad3LfI2",#"https://api.deepseek.com/v3",  # DeepSeek的base_url
#     qianfan_sk="2s6Cetnpzah9JFnbmUdNEaBvOpZvQbzm", #"sk-byurrpvmvjaebikpmhkrwrxgqfxniaujbhvnyyadouxecanz",  # DeepSeek平台的API Key
# )
# #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
#
# llm = OpenAI(
#   base_url="https://openrouter.ai/api/v1",
#   # model="deepseek/deepseek-r1-0528:free",
#   api_key="sk-sZi4nNPwuQhqBNonGrHL0yATSQKHOi88AJiiGFQfdG5xoD1l",
# )

# llm = OpenAI(
#     api_key="AIzaSyC3lJr1v8cf4ZjQ2C0_47RoE6Ny60JKqVE",
#     base_url="sk-sZi4nNPwuQhqBNonGrHL0yATSQKHOi88AJiiGFQfdG5xoD1l"
# )

llm = OpenAI(
    api_key="sk-sZi4nNPwuQhqBNonGrHL0yATSQKHOi88AJiiGFQfdG5xoD1l",
    base_url="https://api.chat.csu.edu.cn/v1"
)

#completion = llm.chat.completions.create(
  #  model="gemini-2.5-flash-preview-05-20",
   # reasoning_effort="low",
   # messages=[
     #   {"role": "system", "content": "You are a helpful assistant."},
      #  {
     #       "role": "user",
     #       "content": "你是一个研究视频传输的专家，是一个美国教授。 请将下述已有内容\\nWe collected the CDF curves for the download times of frames and chunks. As shown in Fig.1, 90% of frames are downloaded within 0.091 seconds, while 90% of chunks take over 1.626 seconds. Chunk-level sampling obscures bandwidth fluctuations within a chunk, as seen in the circled sample points in Fig.2, where abrupt changes occur.\\n\\ncontent{![019710e5-c2e3-7484-9e40-a1bf644ecd6c_4_306_570_786_425_0.jpg](images/019710e5-c2e3-7484-9e40-a1bf644ecd6c_4_306_570_786_425_0.jpg)\\n\\nFig. 1: CDF of download time comparison for frames and chunks.\\n\\n![019710e5-c2e3-7484-9e40-a1bf644ecd6c_4_1378_570_780_458_0.jpg](images/019710e5-c2e3-7484-9e40-a1bf644ecd6c_4_1378_570_780_458_0.jpg)\\n\\nFig. 2: Download time comparison between frame-level and chunk-level.}We collected the CDF curves for the download times of frames and chunks. As shown in Fig.1, 90% of frames are downloaded within 0.091 seconds, while 90% of chunks take over 1.626 seconds. Chunk-level sampling obscures bandwidth fluctuations within a chunk, as seen in the circled sample points in Fig.2, where abrupt changes occur.\\n\\ncontent{![019710e5-c2e3-7484-9e40-a1bf644ecd6c_4_306_570_786_425_0.jpg](images/019710e5-c2e3-7484-9e40-a1bf644ecd6c_4_306_570_786_425_0.jpg)\\n\\nFig. 1: CDF of download time comparison for frames and chunks.\\n\\n![019710e5-c2e3-7484-9e40-a1bf644ecd6c_4_1378_570_780_458_0.jpg](images/019710e5-c2e3-7484-9e40-a1bf644ecd6c_4_1378_570_780_458_0.jpg)\\n\\nFig. 2: Download time comparison between frame-level and chunk-level.}\\n\\ncontent{![019710e5-c2e3-7484-9e40-a1bf644ecd6c_4_306_570_786_425_0.jpg](images/019710e5-c2e3-7484-9e40-a1bf644ecd6c_4_306_570_786_425_0.jpg)\\n\\nFig. 1: CDF of download time comparison for frames and chunks.\\n\\n![019710e5-c2e3-7484-9e40-a1bf644ecd6c_4_1378_570_780_458_0.jpg](images/019710e5-c2e3-7484-9e40-a1bf644ecd6c_4_1378_570_780_458_0.jpg)\\n\\nFig. 2: Download time comparison between frame-level and chunk-level.}\\n补全为完整的段落.\\n要求保持子目录组织结构不变。\\n补全段落时以下面的知识库位参考资料\\n。\\n写作逻辑要和以下章节的逻辑内容呼应\\n。\\n补全段落时要求生成的内容是对已有内容的补充，不改变已有内容的目录结构，可以适当对已有内容的句子扩充，但要保证句子之间逻辑结构和原来一致，扩充内容不要超过1句。知识库中的知识只能作为参考，总结归纳其中语义相关的知识作为参照，而不是直接引用。知识库中出现的图表，若已有内容中没有，则认为该知识不相关，不能作为参考。生成内容和知识库中的原句不可以一样。 latex公式不要编译。要求英文撰写。凝练成逻辑严密的一段话。不要目录结构，不要出现目录编号。生成的文字中要包括已有内容里对图或者表的引用。要求语言风格比较学术化。"
     #   }
   # ]
#)
#text_output = completion.choices[0].message
#print("output", text_output.content)
# AIzaSyC3lJr1v8cf4ZjQ2C0_47RoE6Ny60JKqVE
#llm1 = ChatOpenAI(
 #   base_url="https:://qianfan.baidubce.com/v3",#"https://api.deepseek.com/v3",  # DeepSeek的base_url
 #   api_key="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", #"sk-byurrpvmvjaebikpmhkrwrxgqfxniaujbhvnyyadouxecanz",  # DeepSeek平台的API Key
  #  #model="gpt-4o",  # 或者 "deepseek-coder"，根据你要用的模型选
  #  temperature=0.2
#)
#llm = ChatOpenAI(
  #  #base_url="http://openrouter.ai/api/v1",
  #  api_key="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",
  #  model="gpt-4o",
    #temperature=0.2
#)