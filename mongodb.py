import time
import pymongo
from bson import ObjectId
from pymongo import MongoClient
from models import ResearchPaper, PaperSection, Prompt_Template
import json
from typing import Optional
from typing import List, Dict, Any
import os
from datetime import datetime


class PaperDatabase:
    def __init__(self, db_name="research_papers", collection_name: str = "papers"):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client[db_name]
        self.collection=   self.db[collection_name]
        self.papers = self.db['papers']
        self.users = self.db['users']
        self.prompts = self.db['prompts']

    def query_papers_by_uid(self,
            uid: int,
            db_connection_string: str = "mongodb://localhost:27017/",
            db_name: str = "research_papers",
            collection_name: str = "papers",
            output_dir: str = "output"
    ) -> Dict[str, Any]:
        """
        根据UID从MongoDB查询论文，并导出为JSON文件

        Args:
            uid: 要查询的论文UID
            db_connection_string: MongoDB连接字符串
            db_name: 数据库名称
            collection_name: 集合名称
            output_dir: 输出JSON文件的目录

        Returns:
            包含处理结果的字典
        """
        result = {
            "success": False,
            "message": "",
            "matched_count": 0,
            "output_files": []
        }

        try:
            # 连接MongoDB
            client = pymongo.MongoClient(db_connection_string)
            db = client[db_name]
            collection = db[collection_name]

            # 查询论文，排除 _id 字段
            query = {"uid": uid}
            projection = {"_id": 0}  # 排除 _id 字段
            papers = list(collection.find(query, projection))
            print("uid",uid)
            # 检查结果
            if not papers:
                result["message"] = f"未找到UID为 {uid} 的论文"
                return result

            # 创建输出目录（如果不存在）
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 处理查询结果
            result["matched_count"] = len(papers)

            result["papers"] = papers
            # if len(papers) == 1:
            #     # 单篇论文，直接输出
            #     result
            # else:
            #     # 多篇论文，按索引输出
            #     for i, paper in enumerate(papers):
            #         json.dump(paper, ensure_ascii=False, indent=4)

            result["success"] = True
            return result

        except Exception as e:
            result["message"] = f"查询过程中发生错误: {str(e)}"
            return result
        finally:
            # 关闭数据库连接
            if 'client' in locals():
                client.close()

    def get_paper(self, user_id: str, paper_id: str) -> Optional[ResearchPaper]:
        doc = self.papers.find_one({"paper_id": paper_id, "author": user_id})
        if doc:
            sections = {
                name: PaperSection(**data)
                for name, data in doc.get('sections', {}).items()
            }
            return ResearchPaper(
                paper_id=doc['paper_id'],
                title=doc.get('title', 'Untitled'),
                author=doc['author'],
                sections=sections,
                current_section=doc.get('current_section')
            )
        return None

    def save_paper(self, paper_data):
        uid = paper_data.get("uid")
        print("uid save ",uid)
        print(paper_data)
        paper_title = paper_data.get("paper_title")
        if uid is None:
            raise ValueError("JSON 文件中缺少 uid 字段，无法写入数据库")
        try:
            self.collection.update_one(
             {"uid": uid, "paper_title": paper_title},
             {"$set": paper_data},
             upsert=True
            )

            return str(uid)

        except Exception as e:
            print(f"导入过程中发生错误: {e}")
            return None

        finally:
            if 'client' in locals():
                self.client.close()

    def verify_user(self,username,password):
        doc = self.users.find_one({"username": username})
        print(doc)
        if doc:
            info = dict()
            import bcrypt
            # 数据库中存储的加密后的密码
            stored_hash = doc['password_hash']
            # 用户登录时输入的密码
            user_input_password = password
            # 验证密码
            if bcrypt.checkpw(user_input_password.encode('utf-8'), stored_hash):
                info["verify"] = True
                info["user_info"] = doc
                return info
            else:
                info["verify"] = False
                return info
        else:
            # print(doc)
            info = dict()
            info["verify"] = False
            return info

    def change_password(self, username, old_password, new_password):
        """修改用户密码"""
        import bcrypt
        
        # 首先验证旧密码
        doc = self.users.find_one({"username": username})
        if not doc:
            return {"success": False, "message": "用户不存在"}
        
        # 验证旧密码
        stored_hash = doc['password_hash']
        if not bcrypt.checkpw(old_password.encode('utf-8'), stored_hash):
            return {"success": False, "message": "旧密码错误"}
        
        # 生成新密码的哈希值
        new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        # 更新密码
        result = self.users.update_one(
            {"username": username},
            {"$set": {"password_hash": new_password_hash}}
        )
        
        if result.modified_count > 0:
            return {"success": True, "message": "密码修改成功"}
        else:
            return {"success": False, "message": "密码修改失败"}

    def get_prompt(self, ppt_id: str) -> Optional[Prompt_Template]:
        prompt = self.prompts.find_one({"ppt_id": ppt_id})
        if prompt:
            return Prompt_Template(
                ppt_id=prompt['ppt_id'],
                prompt_json=prompt['prompt_json'],
            )
        return None

    def delete_paper_by_title_and_uid(self, title, uid):
        print("title",title,"uid",uid)
        result = self.collection.delete_one({"paper_title": title, "uid": uid})
        return result.deleted_count > 0

    def save_prompt(self, prompt: Prompt_Template):
        try:
            self.prompts.update_one(
                {'ppt_id': prompt.ppt_id},
                {'$set': {
                    'ppt_id': prompt.ppt_id,
                    'prompt_json': prompt.prompt_json,
                }},
                upsert=True
            )
            return True
        except:
            return False

#日志数据库
#计划记录
#1.LLM生成内容：包含promot模板，知识库内容，源内容，前文引用内容，生成内容
#2.LLM修改内容：生成内容，修改意见，修改结果
#3.用户评价内容：LLM生成内容id，用户评价，用户评分
#总而言是，该数据记录ai生成（包含全部输入和输出），和用户评价
class LogDatabase:
    def __init__(self, db_name="research_papers", collection_name="logs"):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def save_generate_log(self, log: dict):
        result = self.collection.insert_one(log)
        return str(result.inserted_id)

    def save_modify_log(self, log: dict):
        result = self.collection.insert_one(log)
        return str(result.inserted_id)
    
    def save_rating_log(self, log: dict):
        result = self.collection.insert_one(log)
        return str(result.inserted_id)

class UserDatabase:
    def __init__(self, db_name="research_papers", collection_name="users"):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def get_user_by_name(self, username: str):
        return self.collection.find_one({"username": username})

    def get_user_by_id(self, uid: str):
        return self.collection.find_one({"_id": ObjectId(uid)})

# Prompt收藏夹和模板管理数据库
class PromptFolderDatabase:
    def __init__(self, db_name="research_papers"):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client[db_name]
        self.folders = self.db['prompt_folders']
        self.user_prompts = self.db['user_prompts']
    
    # ============ 收藏夹操作 ============
    
    def create_folder(self, user_id: str, folder_name: str, description: Optional[str] = None) -> Optional[str]:
        """创建收藏夹"""
        try:
            folder_doc = {
                "user_id": user_id,
                "folder_name": folder_name,
                "description": description,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            result = self.folders.insert_one(folder_doc)
            return str(result.inserted_id)
        except Exception as e:
            print(f"创建收藏夹失败: {e}")
            return None
    
    def get_user_folders(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的所有收藏夹"""
        try:
            folders = list(self.folders.find({"user_id": user_id}).sort("created_at", -1))
            
            # 为每个收藏夹计算prompt数量
            for folder in folders:
                folder['id'] = str(folder['_id'])
                del folder['_id']
                # 统计该收藏夹下的prompt数量
                prompt_count = self.user_prompts.count_documents({"folder_id": folder['id']})
                folder['prompt_count'] = prompt_count
            
            return folders
        except Exception as e:
            print(f"获取收藏夹列表失败: {e}")
            return []
    
    def get_folder_by_id(self, folder_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取收藏夹"""
        try:
            folder = self.folders.find_one({"_id": ObjectId(folder_id)})
            if folder:
                folder['id'] = str(folder['_id'])
                del folder['_id']
                # 统计prompt数量
                prompt_count = self.user_prompts.count_documents({"folder_id": folder['id']})
                folder['prompt_count'] = prompt_count
            return folder
        except Exception as e:
            print(f"获取收藏夹失败: {e}")
            return None
    
    def update_folder(self, folder_id: str, user_id: str, folder_name: Optional[str] = None, 
                     description: Optional[str] = None) -> bool:
        """更新收藏夹"""
        try:
            update_data = {"updated_at": datetime.now()}
            if folder_name is not None:
                update_data["folder_name"] = folder_name
            if description is not None:
                update_data["description"] = description
            
            result = self.folders.update_one(
                {"_id": ObjectId(folder_id), "user_id": user_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"更新收藏夹失败: {e}")
            return False
    
    def delete_folder(self, folder_id: str, user_id: str) -> bool:
        """删除收藏夹（同时删除其下的所有prompts）"""
        try:
            # 先删除该收藏夹下的所有prompts
            self.user_prompts.delete_many({"folder_id": folder_id, "user_id": user_id})
            
            # 删除收藏夹
            result = self.folders.delete_one({"_id": ObjectId(folder_id), "user_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"删除收藏夹失败: {e}")
            return False
    
    # ============ Prompt操作 ============
    
    def create_prompt(self, user_id: str, folder_id: str, prompt_name: str, 
                     prompt_content: str, description: Optional[str] = None, 
                     tags: Optional[List[str]] = None) -> Optional[str]:
        """创建Prompt"""
        try:
            prompt_doc = {
                "user_id": user_id,
                "folder_id": folder_id,
                "prompt_name": prompt_name,
                "prompt_content": prompt_content,
                "description": description,
                "tags": tags if tags else [],
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            result = self.user_prompts.insert_one(prompt_doc)
            return str(result.inserted_id)
        except Exception as e:
            print(f"创建Prompt失败: {e}")
            return None
    
    def get_prompts_by_folder(self, folder_id: str, user_id: str) -> List[Dict[str, Any]]:
        """获取指定收藏夹下的所有prompts"""
        try:
            prompts = list(self.user_prompts.find({
                "folder_id": folder_id,
                "user_id": user_id
            }).sort("created_at", -1))
            
            for prompt in prompts:
                prompt['id'] = str(prompt['_id'])
                del prompt['_id']
            
            return prompts
        except Exception as e:
            print(f"获取Prompt列表失败: {e}")
            return []
    
    def get_prompt_by_id(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取Prompt"""
        try:
            prompt = self.user_prompts.find_one({"_id": ObjectId(prompt_id)})
            if prompt:
                prompt['id'] = str(prompt['_id'])
                del prompt['_id']
            return prompt
        except Exception as e:
            print(f"获取Prompt失败: {e}")
            return None
    
    def update_prompt(self, prompt_id: str, user_id: str, folder_id: Optional[str] = None,
                     prompt_name: Optional[str] = None, prompt_content: Optional[str] = None,
                     description: Optional[str] = None, tags: Optional[List[str]] = None) -> bool:
        """更新Prompt"""
        try:
            update_data = {"updated_at": datetime.now()}
            if folder_id is not None:
                update_data["folder_id"] = folder_id
            if prompt_name is not None:
                update_data["prompt_name"] = prompt_name
            if prompt_content is not None:
                update_data["prompt_content"] = prompt_content
            if description is not None:
                update_data["description"] = description
            if tags is not None:
                update_data["tags"] = tags
            
            result = self.user_prompts.update_one(
                {"_id": ObjectId(prompt_id), "user_id": user_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"更新Prompt失败: {e}")
            return False
    
    def delete_prompt(self, prompt_id: str, user_id: str) -> bool:
        """删除Prompt"""
        try:
            result = self.user_prompts.delete_one({
                "_id": ObjectId(prompt_id),
                "user_id": user_id
            })
            return result.deleted_count > 0
        except Exception as e:
            print(f"删除Prompt失败: {e}")
            return False
    
    def search_prompts(self, user_id: str, keyword: str) -> List[Dict[str, Any]]:
        """搜索Prompts（按名称和描述）"""
        try:
            # 使用正则表达式进行模糊搜索
            regex_pattern = {"$regex": keyword, "$options": "i"}
            prompts = list(self.user_prompts.find({
                "user_id": user_id,
                "$or": [
                    {"prompt_name": regex_pattern},
                    {"description": regex_pattern},
                    {"tags": regex_pattern}
                ]
            }).sort("created_at", -1))
            
            for prompt in prompts:
                prompt['id'] = str(prompt['_id'])
                del prompt['_id']
            
            return prompts
        except Exception as e:
            print(f"搜索Prompt失败: {e}")
            return []

if __name__ == '__main__':
    paperDatabase = PaperDatabase()
    info = paperDatabase.verify_user("sxs", "123456")
    print(info)