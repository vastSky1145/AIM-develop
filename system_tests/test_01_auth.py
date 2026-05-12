"""登录、当前用户与修改密码接口测试。"""

from __future__ import annotations

import unittest

import requests

from system_tests.config import BASE_URL, TEST_PASSWORD, TEST_USERNAME
from system_tests.utils import (
    api_url,
    assert_response_success,
    auth_headers,
    get_json_or_empty,
    login_and_get_token,
)


class AuthApiTests(unittest.TestCase):
    """认证相关 API 正确性测试。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.base_url = BASE_URL

    def test_login_success(self) -> None:
        response = requests.post(
            api_url("/api/auth/login", self.base_url),
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            timeout=30,
        )
        payload = assert_response_success(response)
        self.assertIn("token", payload["data"])
        self.assertIn("user_info", payload["data"])
        self.assertEqual(payload["data"]["user_info"]["username"], TEST_USERNAME)

    def test_login_wrong_password(self) -> None:
        response = requests.post(
            api_url("/api/auth/login", self.base_url),
            json={"username": TEST_USERNAME, "password": "wrong-password-xyz"},
            timeout=30,
        )
        self.assertEqual(response.status_code, 401)

    def test_get_me_with_valid_token(self) -> None:
        token = login_and_get_token(base_url=self.base_url)
        response = requests.get(
            api_url("/api/papers/list", self.base_url),
            headers=auth_headers(token),
            timeout=30,
        )
        assert_response_success(response)

    def test_get_me_with_invalid_token(self) -> None:
        response = requests.get(
            api_url("/api/auth/me", self.base_url),
            headers=auth_headers("invalid.token.value"),
            timeout=30,
        )
        self.assertIn(response.status_code, (401, 403, 500))

    def test_change_password_then_restore(self) -> None:
        token = login_and_get_token(base_url=self.base_url)
        headers = auth_headers(token)
        temp_password = "654321"

        change_response = requests.post(
            api_url("/api/auth/change-password", self.base_url),
            headers=headers,
            json={
                "old_password": TEST_PASSWORD,
                "new_password": temp_password,
            },
            timeout=30,
        )
        assert_response_success(change_response)

        login_temp = requests.post(
            api_url("/api/auth/login", self.base_url),
            json={"username": TEST_USERNAME, "password": temp_password},
            timeout=30,
        )
        assert_response_success(login_temp)

        restore_token = login_temp.json()["data"]["token"]
        restore_response = requests.post(
            api_url("/api/auth/change-password", self.base_url),
            headers=auth_headers(restore_token),
            json={
                "old_password": temp_password,
                "new_password": TEST_PASSWORD,
            },
            timeout=30,
        )
        assert_response_success(restore_response)

        login_original = requests.post(
            api_url("/api/auth/login", self.base_url),
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            timeout=30,
        )
        payload = get_json_or_empty(login_original)
        self.assertTrue(payload.get("success"))


if __name__ == "__main__":
    unittest.main()
