"""用户 Prompt 收藏夹与 Prompt API 测试。"""

from __future__ import annotations

import os
import unittest

import requests

from system_tests.config import BASE_URL
from system_tests.utils import (
    api_url,
    assert_response_success,
    auth_headers,
    login_and_get_token,
    unique_name,
)


class UserPromptsApiTests(unittest.TestCase):
    """收藏夹与 Prompt CRUD、版本历史。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.base_url = BASE_URL
        cls.token = login_and_get_token(base_url=cls.base_url)
        cls.headers = auth_headers(cls.token)
        cls.second_username = os.getenv("SYSTEM_TEST_SECOND_USERNAME")
        cls.second_password = os.getenv("SYSTEM_TEST_SECOND_PASSWORD")
        cls.second_token = None
        if cls.second_username and cls.second_password:
            try:
                cls.second_token = login_and_get_token(
                    username=cls.second_username,
                    password=cls.second_password,
                    base_url=cls.base_url,
                )
            except Exception:
                cls.second_token = None

    def setUp(self) -> None:
        self.folder_name = unique_name("test_folder")
        self.prompt_name = unique_name("test_prompt")
        self.folder_id = None
        self.prompt_id = None

    def tearDown(self) -> None:
        if self.prompt_id:
            requests.delete(
                api_url(f"/api/user-prompts/delete/{self.prompt_id}", self.base_url),
                headers=self.headers,
                timeout=30,
            )
        if self.folder_id:
            requests.delete(
                api_url(f"/api/user-prompts/folders/{self.folder_id}", self.base_url),
                headers=self.headers,
                timeout=30,
            )

    def _create_folder(self) -> str:
        response = requests.post(
            api_url("/api/user-prompts/folders", self.base_url),
            headers=self.headers,
            json={"folder_name": self.folder_name, "description": "system test"},
            timeout=30,
        )
        payload = assert_response_success(response)
        folder_id = payload["data"]["id"]
        self.folder_id = folder_id
        return folder_id

    def test_folder_and_prompt_crud_with_versions(self) -> None:
        folder_id = self._create_folder()

        list_response = requests.get(
            api_url("/api/user-prompts/folders", self.base_url),
            headers=self.headers,
            timeout=30,
        )
        list_payload = assert_response_success(list_response)
        folder_ids = [item["id"] for item in list_payload["data"]]
        self.assertIn(folder_id, folder_ids)

        update_folder = requests.put(
            api_url(f"/api/user-prompts/folders/{folder_id}", self.base_url),
            headers=self.headers,
            json={"folder_name": f"{self.folder_name}_updated"},
            timeout=30,
        )
        assert_response_success(update_folder)

        create_prompt = requests.post(
            api_url("/api/user-prompts/create", self.base_url),
            headers=self.headers,
            json={
                "folder_id": folder_id,
                "prompt_name": self.prompt_name,
                "prompt_content": "prompt content v1",
                "description": "desc",
                "tags": ["system-test"],
            },
            timeout=30,
        )
        create_payload = assert_response_success(create_prompt)
        prompt_id = create_payload["data"]["id"]
        self.prompt_id = prompt_id

        list_prompts = requests.get(
            api_url("/api/user-prompts/list", self.base_url),
            headers=self.headers,
            params={"folder_id": folder_id},
            timeout=30,
        )
        list_prompt_payload = assert_response_success(list_prompts)
        prompt_ids = [item["id"] for item in list_prompt_payload["data"]]
        self.assertIn(prompt_id, prompt_ids)

        update_prompt = requests.put(
            api_url(f"/api/user-prompts/update/{prompt_id}", self.base_url),
            headers=self.headers,
            json={
                "prompt_content": "prompt content v2",
                "change_description": "system test update",
            },
            timeout=30,
        )
        assert_response_success(update_prompt)

        versions_response = requests.get(
            api_url(f"/api/user-prompts/versions/{prompt_id}", self.base_url),
            headers=self.headers,
            timeout=30,
        )
        versions_payload = assert_response_success(versions_response)
        self.assertGreaterEqual(len(versions_payload["data"]), 2)

        search_response = requests.get(
            api_url("/api/user-prompts/search", self.base_url),
            headers=self.headers,
            params={"keyword": self.prompt_name},
            timeout=30,
        )
        search_payload = assert_response_success(search_response)
        self.assertTrue(any(item["id"] == prompt_id for item in search_payload["data"]))

        delete_prompt = requests.delete(
            api_url(f"/api/user-prompts/delete/{prompt_id}", self.base_url),
            headers=self.headers,
            timeout=30,
        )
        assert_response_success(delete_prompt)
        self.prompt_id = None

        delete_folder = requests.delete(
            api_url(f"/api/user-prompts/folders/{folder_id}", self.base_url),
            headers=self.headers,
            timeout=30,
        )
        assert_response_success(delete_folder)
        self.folder_id = None

    @unittest.skipUnless(
        os.getenv("SYSTEM_TEST_SECOND_USERNAME") and os.getenv("SYSTEM_TEST_SECOND_PASSWORD"),
        "未配置第二测试账户，跳过跨用户权限校验",
    )
    def test_cross_user_folder_access_forbidden(self) -> None:
        folder_id = self._create_folder()
        second_headers = auth_headers(self.second_token)

        response = requests.get(
            api_url("/api/user-prompts/list", self.base_url),
            headers=second_headers,
            params={"folder_id": folder_id},
            timeout=30,
        )
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
