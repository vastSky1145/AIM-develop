"""统一运行 system_tests 下全部基础功能测试并输出汇总。"""

from __future__ import annotations

import io
import sys
import time
import unittest
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from system_tests.config import RESULTS_DIR

MODULE_LABELS = {
    "test_01_auth": "登录与认证",
    "test_02_mongodb_crud": "MongoDB CRUD",
    "test_03_papers_crud": "论文管理 CRUD",
    "test_04_knowledge_crud": "知识库管理 CRUD",
    "test_05_prompts_crud": "Prompt 模板 CRUD",
    "test_06_user_prompts_crud": "用户 Prompt CRUD",
}


class _SummaryTestResult(unittest.TextTestResult):
    """收集每个测试模块的通过/失败/错误统计。"""

    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.module_stats: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"tests": 0, "passed": 0, "failures": 0, "errors": 0}
        )
        self._case_start: Dict[str, float] = {}
        self.module_duration: Dict[str, float] = defaultdict(float)

    def startTest(self, test):
        super().startTest(test)
        module = self._module_key(test)
        self.module_stats[module]["tests"] += 1
        self._case_start[test.id()] = time.perf_counter()

    def addSuccess(self, test):
        super().addSuccess(test)
        module = self._module_key(test)
        self.module_stats[module]["passed"] += 1
        self._record_duration(test)

    def addFailure(self, test, err):
        super().addFailure(test, err)
        module = self._module_key(test)
        self.module_stats[module]["failures"] += 1
        self._record_duration(test)

    def addError(self, test, err):
        super().addError(test, err)
        module = self._module_key(test)
        self.module_stats[module]["errors"] += 1
        self._record_duration(test)

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._record_duration(test)

    def _module_key(self, test) -> str:
        return test.__class__.__module__.split(".")[-1]

    def _record_duration(self, test) -> None:
        started = self._case_start.pop(test.id(), None)
        if started is None:
            return
        module = self._module_key(test)
        self.module_duration[module] += time.perf_counter() - started


def _format_summary(result: _SummaryTestResult) -> str:
    lines: List[str] = [
        "",
        "================ 系统基础功能测试汇总 ================",
        f"{'模块':<22}{'用例数':>6}{'通过':>6}{'失败':>6}{'错误':>6}{'耗时(s)':>10}",
    ]

    totals = {"tests": 0, "passed": 0, "failures": 0, "errors": 0, "duration": 0.0}
    for module in sorted(result.module_stats.keys()):
        stats = result.module_stats[module]
        duration = result.module_duration.get(module, 0.0)
        label = MODULE_LABELS.get(module, module)
        lines.append(
            f"{label:<22}{stats['tests']:>6}{stats['passed']:>6}"
            f"{stats['failures']:>6}{stats['errors']:>6}{duration:>10.2f}"
        )
        totals["tests"] += stats["tests"]
        totals["passed"] += stats["passed"]
        totals["failures"] += stats["failures"]
        totals["errors"] += stats["errors"]
        totals["duration"] += duration

    lines.append(
        f"{'总计':<22}{totals['tests']:>6}{totals['passed']:>6}"
        f"{totals['failures']:>6}{totals['errors']:>6}{totals['duration']:>10.2f}"
    )
    lines.append("======================================================")
    return "\n".join(lines)


def run_all() -> int:
    package_dir = Path(__file__).resolve().parent
    results_dir = package_dir / RESULTS_DIR
    results_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = results_dir / f"run_{timestamp}.log"

    buffer = io.StringIO()
    runner = unittest.TextTestRunner(
        stream=buffer,
        verbosity=2,
        resultclass=_SummaryTestResult,
    )

    suite = unittest.defaultTestLoader.discover(
        start_dir=str(package_dir),
        pattern="test_*.py",
        top_level_dir=str(package_dir.parent),
    )
    result = runner.run(suite)
    summary = _format_summary(result)

    log_content = buffer.getvalue() + summary + "\n"
    log_path.write_text(log_content, encoding="utf-8")

    print(log_content, end="")
    print(f"完整日志已写入: {log_path}")

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_all())
