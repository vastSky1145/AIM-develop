"""system_tests 运行配置。"""

import os

BASE_URL = os.getenv("SYSTEM_TEST_BASE_URL", "http://localhost:8007")
TEST_USERNAME = "ght"
TEST_PASSWORD = "123456"
MONGO_URL = "mongodb://localhost:27017/"
MONGO_DB = "research_papers"

# MongoDB 直连 CRUD 测试使用的隔离集合前缀
TEST_COLLECTION_PREFIX = "system_tests_"

# 汇总报告输出目录（相对 system_tests 包目录）
RESULTS_DIR = "results"
