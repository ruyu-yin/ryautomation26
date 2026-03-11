# 🚀 在 Jenkins 中运行（快速指南）

## 方式 1：手动配置（推荐，5 分钟）

### 步骤 1：登录 Jenkins

打开浏览器访问：http://localhost:8080

---

### 步骤 2：创建 Pipeline 任务

1. 点击 **新建任务** (New Item)
2. 输入任务名称：`test-automation-platform`
3. 选择 **Pipeline**
4. 点击 **确定** (OK)

---

### 步骤 3：配置 Pipeline

#### 源码管理 (Source Code Management)
```
✅ Git
Repository URL: file:///Users/ruyuxinmac/.openclaw/workspace/test-automation-platform
Branches to build: */main
```

#### Pipeline 配置
```
Definition: Pipeline script from SCM
SCM: Git
Script Path: jenkins/Jenkinsfile
```

#### 保存
点击 **保存** (Save)

---

### 步骤 4：配置 HTML 报告发布

1. 在任务页面，点击 **配置** (Configure)
2. 滚动到 **构建后操作** (Post-build Actions)
3. 选择 **Publish HTML reports**
4. 填写：
   ```
   HTML directory to archive: reports/html
   Index page[s]: latest.html
   Report title: 自动化测试报告
   ✅ Keep past HTML reports
   ❌ Escape special characters
   ```
5. **保存**

---

### 步骤 5：运行！

1. 点击 **立即构建** (Build Now)
2. 点击构建编号（如 #1）
3. 点击 **控制台输出** (Console Output) 查看进度
4. 构建完成后点击 **自动化测试报告** 查看 HTML 报告

---

## 方式 2：使用 Pipeline 脚本（快速测试）

### 步骤 1：创建 Pipeline

1. **新建任务** → Pipeline → 确定

### 步骤 2：粘贴脚本

在 **Pipeline** 部分：
- Definition: **Pipeline script**
- 点击 **Pipeline 脚本** 文本框
- 粘贴以下内容：

```groovy
pipeline {
    agent any
    
    environment {
        PYTHONUNBUFFERED = '1'
    }
    
    parameters {
        choice(name: 'TEST_TYPE', choices: ['all', 'api', 'app'], description: '测试类型')
    }
    
    stages {
        stage('🔧 准备环境') {
            steps {
                sh '''
                    python3 --version
                    pip3 install -r requirements.txt
                    mkdir -p reports/html reports/markdown database logs
                '''
            }
        }
        
        stage('🧪 执行测试') {
            steps {
                sh '''
                    python3 src/run_tests.py --type ${params.TEST_TYPE} --ci-mode
                '''
            }
        }
        
        stage('📄 发布报告') {
            steps {
                publishHTML([
                    allowMissing: true,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: 'reports/html',
                    reportFiles: 'latest.html',
                    reportName: '自动化测试报告'
                ])
            }
        }
    }
}
```

### 步骤 3：保存并运行

- **保存** → **立即构建**

---

## 📸 配置截图说明

| 步骤 | 位置 | 截图说明 |
|------|------|---------|
| 1 | Jenkins 首页 | 点击"新建任务" |
| 2 | 新建任务 | 输入名称，选择 Pipeline |
| 3 | 源码管理 | 选择 Git，填写本地路径 |
| 4 | Pipeline | 选择 Pipeline script from SCM |
| 5 | 构建后操作 | 添加 Publish HTML reports |
| 6 | 运行 | 点击"立即构建" |

---

## ✅ 验证清单

运行成功后应该看到：

- [ ] 构建状态为绿色（✅）或蓝色（如果测试全通过）
- [ ] 控制台输出显示测试执行日志
- [ ] 左侧菜单有"自动化测试报告"链接
- [ ] 可以点击链接查看 HTML 报告
- [ ] 工作空间中有 `reports/` 和 `database/` 目录

---

## 🔍 故障排查

### 问题 1：找不到 Python
```
解决：在 Pipeline 开头添加
sh 'which python3'
sh 'python3 --version'
```

### 问题 2：权限问题
```bash
# 确保 Jenkins 有执行权限
chmod +x /Users/ruyuxinmac/.openclaw/workspace/test-automation-platform/src/run_tests.py
```

### 问题 3：HTML Publisher 插件未安装
```
解决：系统管理 → 插件管理 → 安装 HTML Publisher
```

### 问题 4：报告无法显示
```
检查：
1. reports/html/latest.html 是否存在
2. 构建后操作配置是否正确
3. 查看 Jenkins 系统日志
```

---

## 📊 查看结果

### 测试报告
- 任务页面 → **自动化测试报告**

### 构建历史
- 任务页面 → **构建历史**

### 趋势分析
```bash
sqlite3 database/test_results.db "SELECT * FROM test_runs ORDER BY created_at DESC;"
```

---

## 🎯 第一次运行预期结果

```
✅ Python 环境准备成功
✅ 依赖安装成功
✅ 执行 10 个测试用例
✅ 生成 HTML 报告
✅ 发布报告成功
⚠️ 可能有 2 个测试失败（网络相关）
```

---

## 需要帮助？

如果遇到问题：
1. 查看控制台输出
2. 检查 `logs/` 目录下的日志
3. 参考 `CHECK_REPORT.md`

---

*最后更新：2026-03-10*
