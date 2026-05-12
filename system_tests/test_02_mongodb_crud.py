"""MongoDB 直连 CRUD 测试（使用隔离集合）。"""

from __future__ import annotations

import unittest
from datetime import datetime

import bcrypt
from pymongo import MongoClient

from system_tests.config import MONGO_DB, MONGO_URL, TEST_COLLECTION_PREFIX
from system_tests.utils import unique_name


class MongoDbCrudTests(unittest.TestCase):
    """对 MongoDB 各业务集合执行增删改查。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
        cls.client.admin.command("ping")
        cls.db = cls.client[MONGO_DB]
        cls.collections = {
            "users": f"{TEST_COLLECTION_PREFIX}users",
            "papers": f"{TEST_COLLECTION_PREFIX}papers",
            "prompts": f"{TEST_COLLECTION_PREFIX}prompts",
            "prompt_folders": f"{TEST_COLLECTION_PREFIX}prompt_folders",
            "user_prompts": f"{TEST_COLLECTION_PREFIX}user_prompts",
            "prompt_versions": f"{TEST_COLLECTION_PREFIX}prompt_versions",
        }

    @classmethod
    def tearDownClass(cls) -> None:
        for name in cls.collections.values():
            cls.db.drop_collection(name)
        cls.client.close()

    def setUp(self) -> None:
        self.username = unique_name("st_user")
        self.paper_title = unique_name("st_paper")
        self.ppt_id = unique_name("st_ppt")
        self.folder_name = unique_name("st_folder")
        self.prompt_name = unique_name("st_prompt")

    def tearDown(self) -> None:
        for name in self.collections.values():
            self.db[name].delete_many({})

    def test_users_crud(self) -> None:
        coll = self.db[self.collections["users"]]
        password_hash = bcrypt.hashpw(b"123456", bcrypt.gensalt())
        coll.insert_one({"username": self.username, "password_hash": password_hash})

        doc = coll.find_one({"username": self.username})
        self.assertIsNotNone(doc)

        new_hash = bcrypt.hashpw(b"654321", bcrypt.gensalt())
        coll.update_one({"username": self.username}, {"$set": {"password_hash": new_hash}})
        updated = coll.find_one({"username": self.username})
        self.assertNotEqual(updated["password_hash"], password_hash)

        result = coll.delete_one({"username": self.username})
        self.assertEqual(result.deleted_count, 1)
        self.assertIsNone(coll.find_one({"username": self.username}))

    def test_papers_crud(self) -> None:
        coll = self.db[self.collections["papers"]]
        uid = unique_name("uid")
        coll.insert_one(
            {
                "uid": uid,
                "paper_title": self.paper_title,
                "sections": [],
            }
        )

        found = coll.find_one({"uid": uid, "paper_title": self.paper_title})
        self.assertIsNotNone(found)

        coll.update_one(
            {"uid": uid, "paper_title": self.paper_title},
            {"$set": {"sections": [{"id": "1", "title": "Introduction", "content": "test"}]}},
        )
        updated = coll.find_one({"uid": uid, "paper_title": self.paper_title})
        self.assertEqual(len(updated["sections"]), 1)

        result = coll.delete_one({"paper_title": self.paper_title, "uid": uid})
        self.assertEqual(result.deleted_count, 1)

    def test_prompts_crud(self) -> None:
        coll = self.db[self.collections["prompts"]]
        coll.update_one(
            {"ppt_id": self.ppt_id},
            {"$set": {"ppt_id": self.ppt_id, "prompt_json": "template-a"}},
            upsert=True,
        )

        doc = coll.find_one({"ppt_id": self.ppt_id})
        self.assertEqual(doc["prompt_json"], "template-a")

        coll.update_one({"ppt_id": self.ppt_id}, {"$set": {"prompt_json": "template-b"}})
        updated = coll.find_one({"ppt_id": self.ppt_id})
        self.assertEqual(updated["prompt_json"], "template-b")

        result = coll.delete_one({"ppt_id": self.ppt_id})
        self.assertEqual(result.deleted_count, 1)

    def test_prompt_folders_crud(self) -> None:
        coll = self.db[self.collections["prompt_folders"]]
        now = datetime.now()
        inserted = coll.insert_one(
            {
                "user_id": self.username,
                "folder_name": self.folder_name,
                "description": "desc",
                "created_at": now,
                "updated_at": now,
            }
        )
        folder_id = inserted.inserted_id

        doc = coll.find_one({"_id": folder_id})
        self.assertEqual(doc["folder_name"], self.folder_name)

        coll.update_one(
            {"_id": folder_id},
            {"$set": {"folder_name": f"{self.folder_name}_updated", "updated_at": datetime.now()}},
        )
        updated = coll.find_one({"_id": folder_id})
        self.assertTrue(updated["folder_name"].endswith("_updated"))

        result = coll.delete_one({"_id": folder_id})
        self.assertEqual(result.deleted_count, 1)

    def test_user_prompts_crud(self) -> None:
        folders = self.db[self.collections["prompt_folders"]]
        prompts = self.db[self.collections["user_prompts"]]
        now = datetime.now()

        folder_oid = folders.insert_one(
            {
                "user_id": self.username,
                "folder_name": self.folder_name,
                "created_at": now,
                "updated_at": now,
            }
        ).inserted_id
        folder_id = str(folder_oid)

        prompt_id = prompts.insert_one(
            {
                "user_id": self.username,
                "folder_id": folder_id,
                "prompt_name": self.prompt_name,
                "prompt_content": "content-v1",
                "tags": [],
                "current_version": 1,
                "created_at": now,
                "updated_at": now,
            }
        ).inserted_id

        doc = prompts.find_one({"_id": prompt_id})
        self.assertEqual(doc["prompt_content"], "content-v1")

        prompts.update_one(
            {"_id": prompt_id},
            {"$set": {"prompt_content": "content-v2", "current_version": 2, "updated_at": datetime.now()}},
        )
        updated = prompts.find_one({"_id": prompt_id})
        self.assertEqual(updated["current_version"], 2)

        result = prompts.delete_one({"_id": prompt_id})
        self.assertEqual(result.deleted_count, 1)
        folders.delete_one({"_id": folder_oid})

    def test_prompt_versions_crud(self) -> None:
        versions = self.db[self.collections["prompt_versions"]]
        prompt_id = unique_name("prompt")
        now = datetime.now()

        versions.insert_one(
            {
                "prompt_id": prompt_id,
                "version": 1,
                "user_id": self.username,
                "folder_id": unique_name("folder"),
                "prompt_name": self.prompt_name,
                "prompt_content": "v1",
                "description": None,
                "tags": [],
                "change_description": "init",
                "created_at": now,
            }
        )
        versions.insert_one(
            {
                "prompt_id": prompt_id,
                "version": 2,
                "user_id": self.username,
                "folder_id": unique_name("folder"),
                "prompt_name": self.prompt_name,
                "prompt_content": "v2",
                "description": None,
                "tags": [],
                "change_description": "update",
                "created_at": now,
            }
        )

        items = list(versions.find({"prompt_id": prompt_id}).sort("version", 1))
        self.assertEqual(len(items), 2)
        self.assertEqual(items[-1]["prompt_content"], "v2")

        result = versions.delete_many({"prompt_id": prompt_id})
        self.assertEqual(result.deleted_count, 2)


if __name__ == "__main__":
    unittest.main()
