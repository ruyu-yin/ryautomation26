# 快速开始指南

## 1. 安装依赖

```bash
cd test-automation-platform
pip3 install -r requirements.txt
```

## 2. 配置通知

### 飞书机器人

1. 在飞书群中添加机器人
2. 获取 Webhook URL
3. 编辑 `config/feishu_config.yaml`：

```yaml
webhook_url: "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_ACTUAL_TOKEN"
```

### 邮件通知

编辑 `config/email_config.yaml`：

```yaml
smtp:
  server: "smtp.gmail.com"  # 或你的 SMTP 服务器
  port: 587
  username: "your_email@gmail.com"
  password_env: "EMAIL_PASSWORD"  # 密码从环境变量读取

from:
  email: "your_email@gmail.com"
  name: "自动化测试平台"

to:
  - "team@example.com"
```

设置环境变量：

```bash
export EMAIL_PASSWORD="your_email_password"
```

## 3. 运行测试

### 运行所有测试

```bash
python3 src/run_tests.py
```

### 仅运行 API 测试

```bash
python3 src/run_tests.py --type api
```

### 仅运行 App 测试

```bash
python3 src/run_tests.py --type app
```

## 4. 查看报告

- **HTML 报告**: `reports/html/latest.html`
- **Markdown 报告**: `reports/markdown/latest.md`
- **Allure 报告**: `allure serve reports/allure-results`

## 5. 查看数据库

```bash
sqlite3 database/test_results.db

# 查看最近测试结果
SELECT * FROM test_runs ORDER BY created_at DESC LIMIT 10;

# 查看趋势数据
SELECT date(created_at) as date, AVG(pass_rate) as avg_pass_rate
FROM test_runs
GROUP BY date(created_at)
ORDER BY date DESC;
```

## 6. Jenkins 集成

### 前置要求

1. 安装 Jenkins
2. 安装以下插件：
   - Pipeline
   - HTML Publisher
   - Allure Jenkins Plugin（可选）

### 配置步骤

1. 在 Jenkins 创建新任务（Pipeline 类型）
2. Pipeline 配置选择 "Pipeline script from SCM"
3. 选择你的代码仓库
4. Script Path 填写：`jenkins/Jenkinsfile`

### 或者使用命令行测试 Jenkinsfile

```bash
# 安装 Jenkinsfile Runner（可选）
# 用于本地测试 Jenkinsfile
```

## 7. 自定义测试用例

### API 测试示例

编辑 `tests/api/test_api.py`：

```python
import requests

def test_your_api():
    response = requests.get("https://api.example.com/endpoint")
    assert response.status_code == 200
    assert response.json()['status'] == 'success'
```

### App 测试示例

编辑 `tests/app/test_app.py`：

```python
def test_your_app_feature(driver):
    # 找到元素并点击
    element = driver.find_element(By.ID, "com.your.app:id/button")
    element.click()
    
    # 验证结果
    result = driver.find_element(By.ID, "com.your.app:id/result")
    assert result.text == "Expected Result"
```

## 8. 故障排查

### 测试不执行

```bash
# 检查 pytest 是否安装
pytest --version

# 检查测试文件是否被识别
pytest --collect-only
```

### 通知发送失败

```bash
# 检查配置文件
cat config/feishu_config.yaml
cat config/email_config.yaml

# 测试飞书 Webhook
curl -X POST https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_TOKEN \
  -H "Content-Type: application/json" \
  -d '{"msg_type":"text","content":{"text":"test"}}'
```

### 数据库问题

```bash
# 重置数据库
rm database/test_results.db
python3 src/run_tests.py  # 会自动创建新数据库
```

## 9. 常用命令

```bash
# 运行测试并生成报告
python3 src/run_tests.py

# 查看帮助
python3 src/run_tests.py --help

# 仅收集测试（不执行）
pytest --collect-only

# 运行特定测试
pytest tests/api/test_api.py::TestAPI::test_get_request -v

# 运行并生成 Allure 报告
pytest --alluredir=./reports/allure-results
allure serve reports/allure-results
```

---

## 下一步

- 📖 查看 [README.md](README.md) 了解完整功能
- 🔧 根据实际需求修改配置文件
- 📝 开始编写你的测试用例
- 🚀 配置 Jenkins 实现 CI/CD
