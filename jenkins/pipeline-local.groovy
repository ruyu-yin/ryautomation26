// 本地 Jenkins Pipeline - 无需 GitHub
// 直接粘贴到 Jenkins Pipeline 配置中

pipeline {
    agent any
    
    environment {
        PYTHONUNBUFFERED = '1'
        PYTEST_ADDOPTS = '--color=yes'
    }
    
    parameters {
        choice(
            name: 'TEST_TYPE',
            choices: ['all', 'api', 'app'],
            description: '选择要执行的测试类型'
        )
        booleanParam(
            name: 'SEND_NOTIFICATION',
            defaultValue: false,  // 本地测试先不发送通知
            description: '是否发送测试通知'
        )
    }
    
    stages {
        stage('🔧 准备环境') {
            steps {
                echo '🔧 准备测试环境...'
                sh '''
                    python3 --version
                    pip3 install --upgrade pip
                    pip3 install -r requirements.txt
                '''
                
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
        }
        
        stage('📊 生成 Allure 报告') {
            steps {
                echo '📊 生成 Allure 报告...'
                script {
                    try {
                        allure([
                            includeProperties: false,
                            jdk: '',
                            properties: [],
                            reportBuildPolicy: 'ALWAYS',
                            results: [[path: 'reports/allure-results']]
                        ])
                    } catch (Exception e) {
                        echo '⚠️ Allure 插件未安装，跳过'
                    }
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
            
            // 归档报告文件
            archiveArtifacts artifacts: 'reports/**/*.html, reports/**/*.md, reports/**/*.json', 
                             fingerprint: true, allowEmptyArchive: true
        }
        
        failure {
            echo '❌ 测试失败！请查看报告了解详情'
        }
        
        success {
            echo '✅ 所有测试通过！'
        }
    }
}
