import os

import chromadb
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# 初始化客户端和集合
# client = chromadb.PersistentClient(path="./my_chroma_db")
# 打印所有集合
# collections = client.list_collections()

# embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
# vectorstore = Chroma(persist_directory="../chroma_db",
#                      embedding_function=embeddings)

# docs = vectorstore.similarity_search("本科", k=6)
# print(docs)
# for i, doc in enumerate(docs):
#     print(f"{i+1}. {doc.page_content}")
client = chromadb.PersistentClient(path="../chroma_db")
collection = client.get_collection("langchain")
all_data = collection.get()
print("IDs:", all_data['ids'])
print("Documents:", all_data['documents'])
for doc in all_data['documents']:
    print("----------------------------------------------------------")
    print(doc)
print("Metadatas:", all_data['metadatas'])
for meta in all_data['metadatas']:
    print(meta)
# collection = client.get_or_create_collection(name="fruits_knowledge")

# # 准备数据并添加到集合
# # 使用 `upsert` 方法，如果ID已存在则会更新数据，避免重复添加报错 :cite[2]
# collection.upsert(
#     documents=[
#         "菠萝原产于南美洲，是热带水果",
#         "橙子富含维生素C，有助于增强免疫力",
#         "苹果是温带水果，品种繁多",
#         "香蕉是草本植物，生长在热带地区"
#     ],
#     ids=["pineapple", "orange", "apple", "banana"]
# )

# # 进行查询
# question = "请介绍一些热带水果"
# search_results = collection.query(
#     query_texts=[question],
#     n_results=2
# )

# # 展示结果
# print(f"你的问题: {question}")
# print("以下是相关的信息：")
# for i, doc in enumerate(search_results['documents'][0]):
#     print(f"{i+1}. {doc}")