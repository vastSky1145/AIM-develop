"""知识库管理类 API 测试（不含语义检索质量）。"""

from __future__ import annotations

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


class KnowledgeApiTests(unittest.TestCase):
    """知识库 sources / delete 与鉴权校验。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.base_url = BASE_URL
        cls.token = login_and_get_token(base_url=cls.base_url)
        cls.headers = auth_headers(cls.token)

    def test_sources_requires_auth(self) -> None:
        response = requests.get(
            api_url("/api/knowledge/sources", self.base_url),
            timeout=30,
        )
        self.assertIn(response.status_code, (401, 403))

    def test_sources_with_valid_token(self) -> None:
        response = requests.get(
            api_url("/api/knowledge/sources", self.base_url),
            headers=self.headers,
            timeout=30,
        )
        payload = assert_response_success(response)
        self.assertIsInstance(payload.get("data"), list)
        for item in payload["data"]:
            self.assertIn("source", item)
            self.assertIn("doc_count", item)

    def test_delete_nonexistent_source(self) -> None:
        response = requests.delete(
            api_url("/api/knowledge/delete", self.base_url),
            headers=self.headers,
            json={"source": unique_name("missing_source") + ".pdf"},
            timeout=30,
        )
        self.assertIn(response.status_code, (404, 500))


if __name__ == "__main__":
    unittest.main()
