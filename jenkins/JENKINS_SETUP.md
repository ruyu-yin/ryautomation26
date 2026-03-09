# Jenkins 配置指南

## 一、系统级配置

### 1. 配置 Python

**系统管理** → **全局工具配置** → **Python**

```
名称：Python3
Python 安装器：Install from python.org
版本：3.9.0（或你需要的版本）
```

### 2. 配置 Git

**系统管理** → **全局工具配置** → **Git**

```
名称：Default Git
Git 安装器：Install from git-scm.com
```

### 3. 配置 Allure（可选）

**系统管理** → **全局工具配置** → **Allure Commandline**

```
名称：Allure
Allure 安装器：Install from GitHub
版本：Latest
```

---

## 二、凭证配置

**系统管理** → **凭证管理** → **全局凭证** → **添加凭证**

### GitHub 凭证（SSH 方式）
```
种类：SSH Username with private key
ID: github-ssh
用户名：git
Private Key: 直接输入（粘贴你的私钥）
```

### GitHub 凭证（HTTPS 方式）
```
种类：Username with password
ID: github-token
用户名：你的 GitHub 用户名
密码：Personal Access Token
```

### 邮件凭证
```
种类：Username with password
ID: email-password
用户名：your_email@example.com
密码：邮箱密码或授权码
```

---

## 三、创建 Pipeline 任务

### 方法 A：使用 Jenkinsfile（推荐）

1. **新建任务** → 输入名称 → 选择 **Pipeline**
2. 配置：
   ```
   源码管理：Git
   Repository URL: https://github.com/用户名/test-automation-platform.git
   凭证：github-token
   
   Pipeline：
   Definition: Pipeline script from SCM
   Script Path: jenkins/Jenkinsfile
   ```
3. **保存** → **立即构建**

### 方法 B：直接配置 Pipeline

1. **新建任务** → 选择 **Pipeline**
2. Pipeline 配置：
   ```
   Definition: Pipeline script
   ```
3. 粘贴 `jenkins/pipeline-direct.groovy` 内容
4. **保存** → **立即构建**

---

## 四、配置 HTML 报告发布

在 Pipeline 任务配置中，**构建后操作** → **Publish HTML reports**：

```
HTML directory to archive: reports/html
Index page[s]: latest.html
Report title: 自动化测试报告
Keep past HTML reports: ✅ 勾选
Escape special characters: ❌ 不勾选
```

---

## 五、配置 Allure 报告（可选）

在 Pipeline 任务配置中，**构建后操作** → **Allure Report**：

```
Path: reports/allure-results
Report build policy: Always
```

---

## 六、配置邮件通知

### 系统级邮件配置

**系统管理** → **系统设置** → **E-mail Notification**

```
SMTP 服务器：smtp.example.com
端口：587
使用 SSL：✅
用户名：your_email@example.com
密码：邮箱密码

测试配置：发送测试邮件验证
```

### 项目中邮件通知

编辑 `config/email_config.yaml`，确保配置正确。

---

## 七、运行测试

### 手动触发
- 点击任务 → **立即构建**
- 可选择参数（测试类型、是否通知等）

### 定时触发

在 Pipeline 中添加：
```groovy
triggers {
    // 每天 9:00 和 18:00 执行
    cron('0 9,18 * * *')
    
    // 或每小时执行
    // cron('0 * * * *')
}
```

### Webhook 触发（GitHub）

1. GitHub 仓库 → Settings → Webhooks → Add webhook
2. Payload URL: `http://你的jenkins.com/github-webhook/`
3. Content type: `application/json`
4. 选择触发事件：Push events

---

## 八、查看结果

### 测试报告
- 任务页面 → **自动化测试报告**（HTML Publisher）
- 任务页面 → **Allure Report**（如果配置了）

### 构建历史
- 任务页面 → **构建历史**
- 点击构建编号查看控制台输出

### 趋势分析
- 数据库查询：`sqlite3 database/test_results.db "SELECT * FROM test_runs ORDER BY created_at DESC;"`

---

## 九、常见问题

### 1. Python 命令找不到
```groovy
// 在 Pipeline 中使用绝对路径
sh '/usr/bin/python3 --version'
```

### 2. 权限问题
```bash
# Jenkins 用户需要有执行权限
sudo chown -R jenkins:jenkins /path/to/workspace
```

### 3. 报告无法显示
- 检查 `reports/html` 目录是否存在
- 检查 `latest.html` 文件是否生成
- 查看 Jenkins 系统日志

### 4. Git 拉取失败
- 检查凭证配置
- 检查仓库 URL 是否正确
- 检查 Jenkins 服务器网络

### 5. 测试超时
```groovy
// 在 Pipeline 中添加超时
options {
    timeout(time: 30, unit: 'MINUTES')
}
```

---

## 十、最佳实践

1. **使用 Jenkinsfile** - 版本控制你的构建流程
2. **参数化构建** - 灵活选择测试类型
3. **归档报告** - 保留历史报告便于对比
4. **清理工作空间** - 定期清理避免磁盘占用
5. **通知集成** - 失败时及时通知团队
6. **并行执行** - API 和 App 测试可并行运行

---

## 快速检查清单

- [ ] Jenkins 已安装必要插件
- [ ] Python 工具已配置
- [ ] Git 凭证已配置
- [ ] Pipeline 任务已创建
- [ ] HTML 报告发布已配置
- [ ] 邮件通知已配置（如需要）
- [ ] 第一次构建成功

---

配置完成后，你的 Jenkins 应该可以：
✅ 自动拉取代码
✅ 安装依赖
✅ 执行测试
✅ 生成报告
✅ 发送通知（失败时）
✅ 保存历史数据
