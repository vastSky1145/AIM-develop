"""
以包为粒度的请求速率限制器

基于滑动窗口算法，针对不同路由包（ai_assistant、knowledge、papers、
auth、prompts、user_prompts）实现差异化限速策略。
每个用户在每个包内独立计数，互不影响。
"""
from collections import defaultdict, deque
from datetime import datetime, timedelta
import asyncio
from typing import Callable

from fastapi import Depends, HTTPException


class PackageRateLimiter:
    """
    基于滑动窗口算法的包级别速率限制器。

    以路由包为粒度，对不同包的请求进行差异化速率控制。
    每个（用户, 包名）二元组维护独立的请求时间戳队列。
    """

    def __init__(self) -> None:
        # (user_id, package_name) -> deque[datetime]
        self._request_log: defaultdict[tuple[str, str], deque[datetime]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check_rate_limit(
        self,
        user_id: str,
        package_name: str,
        max_requests: int,
        window_seconds: int,
    ) -> None:
        """
        检查并记录一次请求，超出限制时抛出 HTTP 429 异常。

        Args:
            user_id: 用户或 IP 标识
            package_name: 包名称（如 "ai_assistant"、"knowledge"）
            max_requests: 时间窗口内允许的最大请求次数
            window_seconds: 滑动时间窗口大小（秒）
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=window_seconds)
        key = (user_id, package_name)

        async with self._lock:
            timestamps = self._request_log[key]

            # 清除窗口外的旧记录
            while timestamps and timestamps[0] < window_start:
                timestamps.popleft()

            if len(timestamps) >= max_requests:
                oldest = timestamps[0]
                retry_after = (
                    int(
                        (oldest + timedelta(seconds=window_seconds) - now).total_seconds()
                    )
                    + 1
                )
                raise HTTPException(
                    status_code=429,
                    detail={
                        "message": f"请求过于频繁，请 {retry_after} 秒后重试",
                        "package": package_name,
                        "limit": max_requests,
                        "window_seconds": window_seconds,
                        "retry_after": retry_after,
                    },
                    headers={"Retry-After": str(retry_after)},
                )

            timestamps.append(now)

    def make_dependency(
        self,
        package_name: str,
        max_requests: int,
        window_seconds: int,
        get_user_fn: Callable,
    ) -> Callable:
        """
        为指定包创建可直接用于 ``Depends()`` 的 FastAPI 依赖函数。

        生成的依赖先调用 *get_user_fn* 获取当前登录用户，再以
        ``(user_id, package_name)`` 为键执行速率检查。

        Args:
            package_name: 包名称
            max_requests: 时间窗口内允许的最大请求次数
            window_seconds: 滑动时间窗口大小（秒）
            get_user_fn: 获取当前用户的依赖函数（如 ``get_current_user``）

        Returns:
            可被 ``Depends()`` 使用的异步依赖函数
        """
        _self = self

        async def _dep(current_user: dict = Depends(get_user_fn)) -> dict:
            user_id = current_user.get("uid") or current_user.get("user_id", "anonymous")
            await _self.check_rate_limit(user_id, package_name, max_requests, window_seconds)
            return current_user

        _dep.__name__ = f"rate_limit_{package_name}"
        return _dep


# 全局单例，供各路由模块复用
rate_limiter = PackageRateLimiter()
