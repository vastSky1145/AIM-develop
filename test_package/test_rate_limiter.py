"""
utils/rate_limiter.py 的单元测试

验证以包为粒度的速率限制逻辑：
- 同一包内请求超限时抛出 HTTP 429
- 不同包之间的限速互不干扰
- 不同用户之间的计数互相独立
- 滑动时间窗口过期后计数自动重置
"""
import asyncio
import sys
import os

# 确保可以找到项目根目录下的模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import HTTPException
from utils.rate_limiter import PackageRateLimiter


def run(coro):
    """在当前线程中运行协程（兼容 Python 3.9 之前的版本）。"""
    return asyncio.get_event_loop().run_until_complete(coro)


# ──────────────────────────────────────────────
# 测试 1：在限额内的请求应全部通过
# ──────────────────────────────────────────────
def test_within_limit():
    limiter = PackageRateLimiter()
    for _ in range(5):
        run(limiter.check_rate_limit("user1", "ai_assistant", max_requests=5, window_seconds=60))
    print("test_within_limit PASSED")


# ──────────────────────────────────────────────
# 测试 2：超出限额时应抛出 HTTP 429
# ──────────────────────────────────────────────
def test_exceeds_limit():
    limiter = PackageRateLimiter()
    for _ in range(3):
        run(limiter.check_rate_limit("user1", "ai_assistant", max_requests=3, window_seconds=60))
    try:
        run(limiter.check_rate_limit("user1", "ai_assistant", max_requests=3, window_seconds=60))
        assert False, "应该抛出 HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 429
        assert "retry_after" in exc.detail
        assert exc.detail["package"] == "ai_assistant"
    print("test_exceeds_limit PASSED")


# ──────────────────────────────────────────────
# 测试 3：不同包的限速相互独立
# ──────────────────────────────────────────────
def test_different_packages_are_independent():
    limiter = PackageRateLimiter()
    # 将 "ai_assistant" 包打满
    for _ in range(3):
        run(limiter.check_rate_limit("user1", "ai_assistant", max_requests=3, window_seconds=60))
    # "knowledge" 包的计数不受影响，应能正常通过
    run(limiter.check_rate_limit("user1", "knowledge", max_requests=3, window_seconds=60))
    print("test_different_packages_are_independent PASSED")


# ──────────────────────────────────────────────
# 测试 4：不同用户的计数相互独立
# ──────────────────────────────────────────────
def test_different_users_are_independent():
    limiter = PackageRateLimiter()
    # 将 user1 打满
    for _ in range(3):
        run(limiter.check_rate_limit("user1", "papers", max_requests=3, window_seconds=60))
    # user2 的计数不受影响
    run(limiter.check_rate_limit("user2", "papers", max_requests=3, window_seconds=60))
    print("test_different_users_are_independent PASSED")


# ──────────────────────────────────────────────
# 测试 5：滑动窗口过期后计数重置
# ──────────────────────────────────────────────
def test_window_expiry_resets_count():
    import datetime

    limiter = PackageRateLimiter()

    # 手动向日志中写入一条"很久以前"的时间戳，模拟窗口外记录
    key = ("user1", "prompts")
    old_ts = datetime.datetime.now() - datetime.timedelta(seconds=120)
    limiter._request_log[key].append(old_ts)

    # 此时窗口（60 秒）内记录数为 0，一条新请求应通过
    run(limiter.check_rate_limit("user1", "prompts", max_requests=1, window_seconds=60))
    print("test_window_expiry_resets_count PASSED")


# ──────────────────────────────────────────────
# 测试 6：429 响应包含 Retry-After 头部信息
# ──────────────────────────────────────────────
def test_retry_after_header():
    limiter = PackageRateLimiter()
    for _ in range(2):
        run(limiter.check_rate_limit("user1", "auth", max_requests=2, window_seconds=60))
    try:
        run(limiter.check_rate_limit("user1", "auth", max_requests=2, window_seconds=60))
        assert False, "应该抛出 HTTPException"
    except HTTPException as exc:
        assert "Retry-After" in exc.headers
        assert int(exc.headers["Retry-After"]) > 0
    print("test_retry_after_header PASSED")


if __name__ == "__main__":
    test_within_limit()
    test_exceeds_limit()
    test_different_packages_are_independent()
    test_different_users_are_independent()
    test_window_expiry_resets_count()
    test_retry_after_header()
    print("\n所有速率限制测试通过 ✓")
