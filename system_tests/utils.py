"""system_tests 公共工具函数。"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

import requests

from system_tests.config import BASE_URL, TEST_PASSWORD, TEST_USERNAME


def unique_name(prefix: str) -> str:
    """生成带前缀的唯一名称，避免测试数据冲突。"""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def login_and_get_token(
    username: str = TEST_USERNAME,
    password: str = TEST_PASSWORD,
    base_url: str = BASE_URL,
) -> str:
    """调用登录接口并返回 JWT。"""
    response = requests.post(
        f"{base_url}/api/auth/login",
        json={"username": username, "password": password},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("success"):
        raise AssertionError(f"登录失败: {payload.get('message')}")
    token = payload.get("data", {}).get("token")
    if not token:
        raise AssertionError("登录响应中缺少 token")
    return token


def auth_headers(token: str) -> Dict[str, str]:
    """构造带 Bearer Token 的请求头。"""
    return {"Authorization": f"Bearer {token}"}


def api_url(path: str, base_url: str = BASE_URL) -> str:
    """拼接 API 完整 URL。"""
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base_url}{path}"


def assert_response_success(
    response: requests.Response,
    *,
    expected_status: int = 200,
) -> Dict[str, Any]:
    """断言 HTTP 状态码与 success 字段。"""
    if response.status_code != expected_status:
        raise AssertionError(
            f"期望状态码 {expected_status}，实际 {response.status_code}，响应: {response.text}"
        )
    payload = response.json()
    if expected_status == 200 and not payload.get("success", False):
        raise AssertionError(f"接口返回 success=False: {payload.get('message')}")
    return payload


def get_json_or_empty(response: requests.Response) -> Dict[str, Any]:
    """安全解析 JSON 响应。"""
    try:
        return response.json()
    except ValueError:
        return {}
