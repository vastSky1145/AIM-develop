"""Prompt 模板 API 测试。"""

from __future__ import annotations

import unittest

import requests
from pymongo import MongoClient

from system_tests.config import BASE_URL, MONGO_DB, MONGO_URL
from system_tests.utils import (
    api_url,
    assert_response_success,
    auth_headers,
    login_and_get_token,
    unique_name,
)


class PromptsApiTests(unittest.TestCase):
    """系统 Prompt 模板 get / save 正确性。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.base_url = BASE_URL
        cls.token = login_and_get_token(base_url=cls.base_url)
        cls.headers = auth_headers(cls.token)
        cls.mongo = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
        cls.prompts = cls.mongo[MONGO_DB]["prompts"]

    @classmethod
    def tearDownClass(cls) -> None:
        cls.mongo.close()

    def setUp(self) -> None:
        self.ppt_id = unique_name("st_ppt")

    def tearDown(self) -> None:
        self.prompts.delete_one({"ppt_id": self.ppt_id})

    def test_get_default_template_when_missing(self) -> None:
        response = requests.get(
            api_url(f"/api/prompts/get/{self.ppt_id}", self.base_url),
            headers=self.headers,
            timeout=30,
        )
        payload = assert_response_success(response)
        self.assertEqual(payload["data"]["ppt_id"], self.ppt_id)
        self.assertTrue(payload["data"]["prompt_json"])

    def test_save_and_get_prompt_template(self) -> None:
        template = f"system test template {unique_name('tpl')}"
        save_response = requests.post(
            api_url("/api/prompts/save", self.base_url),
            headers=self.headers,
            json={"ppt_id": self.ppt_id, "prompt_json": template},
            timeout=30,
        )
        assert_response_success(save_response)

        get_response = requests.get(
            api_url(f"/api/prompts/get/{self.ppt_id}", self.base_url),
            headers=self.headers,
            timeout=30,
        )
        payload = assert_response_success(get_response)
        self.assertEqual(payload["data"]["prompt_json"], template)


if __name__ == "__main__":
    unittest.main()
