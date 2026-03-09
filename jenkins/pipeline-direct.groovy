// Jenkins Declarative Pipeline - 直接配置版本
// 复制这个到 Jenkins Pipeline 配置中

pipeline {
    agent any
    
    tools {
        // 配置 Python 工具（需要在 Jenkins 系统配置中先定义）
        // python 'Python3'
    }
    
    environment {
        PYTHONUNBUFFERED = '1'
        PYTEST_ADDOPTS = '--color=yes'
        REPORT_DIR = 'reports'
        DATABASE_DIR = 'database'
        // 从 Jenkins 凭证获取敏感信息
        EMAIL_PASSWORD = credentials('email-password-id')
        GITHUB_TOKEN = credentials('github-token-id')
    }
    
    parameters {
        choice(
            name: 'TEST_TYPE',
            choices: ['all', 'api', 'app'],
            description: '选择要执行的测试类型'
        )
        booleanParam(
            name: 'SEND_NOTIFICATION',
            defaultValue: true,
            description: '是否发送测试通知'
        )
        string(
            name: 'GIT_BRANCH',
            defaultValue: 'main',
            description: 'Git 分支'
        )
    }
    
    stages {
        stage('📥 拉取代码') {
            steps {
                echo '📥 从 GitHub 拉取代码...'
                checkout scmGit(
                    branches: [[name: "*/${params.GIT_BRANCH}"]],
                    extensions: [],
                    userRemoteConfigs: [[
                        url: 'https://github.com/你的用户名/test-automation-platform.git',
                        credentialsId: 'github-credentials-id'
                    ]]
                )
            }
        }
        
        stage('🔧 准备环境') {
            steps {
                echo '🔧 准备测试环境...'
                sh '''
                    python3 --version
                    pip3 install --upgrade pip
                    pip3 install -r requirements.txt
                '''
                
                // 创建必要目录
                sh '''
                    mkdir -p reports/html reports/markdown reports/allure-results
                    mkdir -p database logs
                '''
            }
        }
        
        stage('🧪 执行测试') {
            steps {
                echo '🧪 执行自动化测试...'
                sh '''
                    python3 src/run_tests.py \
                        --type ${params.TEST_TYPE} \
                        --ci-mode
                '''
            }
            post {
                always {
                    // 保存测试报告
                    archiveArtifacts artifacts: 'reports/**/*.html, reports/**/*.md, reports/**/*.json', 
                                     fingerprint: true, allowEmptyArchive: true
                     
                    // 保存 Allure 结果
                    archiveArtifacts artifacts: 'reports/allure-results/**', 
                                     fingerprint: true, allowEmptyArchive: true
                }
            }
        }
        
        stage('📊 生成 Allure 报告') {
            steps {
                echo '📊 生成 Allure 报告...'
                script {
                    // 使用 Allure 插件
                    allure([
                        includeProperties: false,
                        jdk: '',
                        properties: [],
                        reportBuildPolicy: 'ALWAYS',
                        results: [[path: 'reports/allure-results']]
                    ])
                }
            }
        }
        
        stage('📄 发布 HTML 报告') {
            steps {
                echo '📄 发布 HTML 报告...'
                publishHTML([
                    allowMissing: true,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: 'reports/html',
                    reportFiles: 'latest.html',
                    reportName: '自动化测试报告',
                    reportTitles: ['自动化测试报告']
                ])
            }
        }
    }
    
    post {
        always {
            echo '📋 测试执行完成'
            
            // 清理工作空间（可选）
            // cleanWs()
        }
        
        failure {
            echo '❌ 测试失败！请查看报告了解详情'
            
            // 可以在这里添加额外的失败处理逻辑
            script {
                // 例如：发送紧急通知
                // emailext subject: '测试失败', body: '请查看 Jenkins', to: 'team@example.com'
            }
        }
        
        success {
            echo '✅ 所有测试通过！'
        }
    }
}
