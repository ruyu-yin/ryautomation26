# 自动化测试平台

## 项目概述

基于 pytest 的自动化测试平台，支持 API 测试和 Android App 测试，集成 Jenkins CI/CD，提供多维度报告和通知功能。

## 功能特性

- ✅ **双测试类型支持**：API 测试 + Android App 测试 (Appium)
- ✅ **智能通知**：飞书 + 邮件，严格模式（失败即通知）
- ✅ **多维度报告**：HTML + Markdown + JSON + Allure
- ✅ **数据持久化**：SQLite 存储测试结果，支持趋势分析
- ✅ **Jenkins 集成**：CI/CD 流水线支持
- ✅ **测试统计**：通过率、执行时间、失败分析

## 项目结构

```
test-automation-platform/
├── config/
│   ├── config.yaml          # 主配置文件
│   ├── email_config.yaml    # 邮件配置
│   └── feishu_config.yaml   # 飞书配置
├── src/
│   ├── run_tests.py         # 测试执行入口
│   ├── test_runner.py       # 测试运行器
│   └── utils/
│       ├── report_analyzer.py   # 报告分析
│       ├── notification.py      # 通知模块（飞书 + 邮件）
│       ├── report_generator.py  # 报告生成（HTML/Markdown）
│       └── db_manager.py        # 数据库管理
├── tests/
│   ├── api/                 # API 测试用例
│   │   ├── __init__.py
│   │   └── test_api.py
│   └── app/                 # Android App 测试用例
│   │   ├── __init__.py
│   │   └── test_app.py
├── reports/
│   ├── html/                # HTML 报告
│   ├── markdown/            # Markdown 报告
│   ├── allure-results/      # Allure 原始数据
│   └── pytest-report.json   # JSON 报告
├── database/
│   └── test_results.db      # SQLite 数据库
├── jenkins/
│   └── Jenkinsfile          # Jenkins 流水线配置
├── requirements.txt
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

编辑 `config/config.yaml` 和通知配置文件。

### 3. 运行测试

```bash
# 运行所有测试
python src/run_tests.py

# 仅运行 API 测试
python src/run_tests.py --type api

# 仅运行 App 测试
python src/run_tests.py --type app
```

### 4. Jenkins 集成

```bash
# 在 Jenkins 中配置
# 构建步骤：Execute shell
python src/run_tests.py --ci-mode
```

## 报告查看

- **HTML 报告**：`reports/html/report.html`
- **Markdown 报告**：`reports/markdown/report.md`
- **Allure 报告**：`allure serve reports/allure-results`

## 数据库查询

```bash
# 查看最近测试结果
sqlite3 database/test_results.db "SELECT * FROM test_runs ORDER BY created_at DESC LIMIT 10;"
```

## 通知配置

### 飞书机器人
1. 创建飞书群机器人
2. 获取 Webhook URL
3. 配置到 `config/feishu_config.yaml`

### 邮件通知
1. 配置 SMTP 服务器
2. 配置收件人列表
3. 配置到 `config/email_config.yaml`

---

## 版本

v1.0.0 - 初始版本

## 许可证

MIT
