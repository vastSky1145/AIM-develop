"""论文管理 API CRUD 测试。"""

from __future__ import annotations

import unittest

import requests

from system_tests.config import BASE_URL, TEST_USERNAME
from system_tests.utils import (
    api_url,
    assert_response_success,
    auth_headers,
    login_and_get_token,
    unique_name,
)


class PapersApiTests(unittest.TestCase):
    """论文 create / list / get / update / delete 全链路。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.base_url = BASE_URL
        cls.token = login_and_get_token(base_url=cls.base_url)
        cls.headers = auth_headers(cls.token)

    def setUp(self) -> None:
        self.paper_title = unique_name("test_paper")

    def tearDown(self) -> None:
        requests.delete(
            api_url("/api/papers/delete", self.base_url),
            headers=self.headers,
            json={"paper_title": self.paper_title, "uid": TEST_USERNAME},
            timeout=30,
        )

    def _create_paper(self, sections: list | None = None) -> dict:
        payload = {
            "paper_title": self.paper_title,
            "uid": TEST_USERNAME,
            "sections": sections
            or [
                {
                    "id": "sec-1",
                    "title": "Introduction",
                    "content": "initial content",
                    "children": [],
                }
            ],
        }
        response = requests.post(
            api_url("/api/papers/create", self.base_url),
            headers=self.headers,
            json=payload,
            timeout=30,
        )
        return assert_response_success(response)

    def test_papers_crud_flow(self) -> None:
        create_payload = self._create_paper()
        self.assertEqual(create_payload["data"]["paper_title"], self.paper_title)

        list_response = requests.get(
            api_url("/api/papers/list", self.base_url),
            headers=self.headers,
            timeout=30,
        )
        list_payload = assert_response_success(list_response)
        titles = [item.get("paper_title") for item in list_payload.get("data", [])]
        self.assertIn(self.paper_title, titles)

        get_response = requests.get(
            api_url(f"/api/papers/get/{self.paper_title}", self.base_url),
            headers=self.headers,
            timeout=30,
        )
        get_payload = assert_response_success(get_response)
        self.assertEqual(get_payload["data"]["paper_title"], self.paper_title)

        update_response = requests.put(
            api_url("/api/papers/update", self.base_url),
            headers=self.headers,
            json={
                "paper_title": self.paper_title,
                "uid": TEST_USERNAME,
                "sections": [
                    {
                        "id": "sec-1",
                        "title": "Introduction",
                        "content": "updated content",
                        "children": [],
                    }
                ],
            },
            timeout=30,
        )
        update_payload = assert_response_success(update_response)
        self.assertEqual(
            update_payload["data"]["sections"][0]["content"],
            "updated content",
        )

        delete_response = requests.delete(
            api_url("/api/papers/delete", self.base_url),
            headers=self.headers,
            json={"paper_title": self.paper_title, "uid": TEST_USERNAME},
            timeout=30,
        )
        assert_response_success(delete_response)

        list_after = requests.get(
            api_url("/api/papers/list", self.base_url),
            headers=self.headers,
            timeout=30,
        )
        list_after_payload = assert_response_success(list_after)
        titles_after = [item.get("paper_title") for item in list_after_payload.get("data", [])]
        self.assertNotIn(self.paper_title, titles_after)


if __name__ == "__main__":
    unittest.main()
