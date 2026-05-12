# 系统基础功能测试

本目录用于验证 AIM 后端**非核心**基础功能的正确性，便于在学位论文中展示“登录、数据库与业务 CRUD”等支撑能力。AI 生成、知识库语义检索、PDF Agent 解析等核心能力不在本套件范围内。

## 前置条件

1. 后端已启动（默认 `http://localhost:8007`，可通过环境变量 `SYSTEM_TEST_BASE_URL` 覆盖），例如在项目根目录执行 `bash start_backend.sh`。
2. MongoDB 可访问（默认 `mongodb://localhost:27017/`，库名 `research_papers`）。
3. Python 环境已安装项目依赖（`requests`、`pymongo`、`bcrypt` 等，可与后端相同的 `aim-env` 环境运行）。
4. 测试账户可用（默认 `sxs / 123456`，可在 `system_tests/config.py` 修改）。
5. 可选：配置环境变量 `SYSTEM_TEST_SECOND_USERNAME`、`SYSTEM_TEST_SECOND_PASSWORD` 以启用跨用户权限用例。

## 运行方式

在项目根目录 `AIM-develop/` 下执行：

```bash
python -m system_tests.run_all_tests
```

单独运行某一模块：

```bash
python -m unittest system_tests.test_01_auth -v
python -m unittest system_tests.test_02_mongodb_crud -v
```

## 结果输出

- 终端打印每个用例的详细结果与汇总表（模块、用例数、通过、失败、错误、耗时）。
- 完整日志写入 `system_tests/results/run_<时间戳>.log`。

## 测试覆盖矩阵

| 模块 | 脚本 | 覆盖内容 |
| --- | --- | --- |
| 登录与认证 | `test_01_auth.py` | 登录成功/失败、`/me`、修改密码并恢复 |
| MongoDB CRUD | `test_02_mongodb_crud.py` | 隔离集合上的 users / papers / prompts / folders / user_prompts / versions |
| 论文管理 | `test_03_papers_crud.py` | create → list → get → update → delete |
| 知识库管理 | `test_04_knowledge_crud.py` | sources 鉴权与结构、删除不存在来源 |
| Prompt 模板 | `test_05_prompts_crud.py` | 默认模板回退、保存后读取一致 |
| 用户 Prompt | `test_06_user_prompts_crud.py` | 收藏夹与 Prompt CRUD、版本历史、可选跨用户 403 |

## 不在本套件范围内

- `/api/ai/generate`、`/api/ai/modify` 内容质量评估
- `/api/knowledge/search` 召回准确率指标
- `/api/papers/upload-pdf` Agent 解析准确率
- 知识库 PDF 入库的分块与向量质量
