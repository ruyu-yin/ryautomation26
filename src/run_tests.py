#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化测试执行入口

支持 API 测试和 Android App 测试，集成报告生成、通知、数据库存储
"""

import os
import sys
import time
import uuid
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from loguru import logger

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import yaml
from src.utils.report_analyzer import analyze_pytest_report, get_failure_summary
from src.utils.report_generator import generate_all_reports
from src.utils.notification import NotificationManager
from src.utils.db_manager import TestResultDB


# 配置日志
logger.remove()
logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>")
logger.add("./logs/test_{time:YYYY-MM-DD}.log", level="DEBUG", rotation="1 day")


def load_config(config_path: str = 'config/config.yaml') -> dict:
    """加载配置文件"""
    if not os.path.exists(config_path):
        logger.error(f"配置文件不存在：{config_path}")
        return {}
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def clean_directories(dirs: list):
    """清理旧报告目录"""
    for dir_path in dirs:
        path = Path(dir_path)
        if path.exists():
            # 清空目录内容但保留目录本身
            for item in path.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    import shutil
                    shutil.rmtree(item)
            logger.debug(f"已清理目录：{dir_path}")


def record_execution_info(record_file: str):
    """记录执行信息"""
    path = Path(record_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    info = {
        'start_time': datetime.now().isoformat(),
        'hostname': os.uname().nodename,
        'user': os.environ.get('USER', 'unknown'),
        'workspace': os.getcwd()
    }
    
    with open(path, 'w', encoding='utf-8') as f:
        import json
        json.dump(info, f, indent=2, ensure_ascii=False)


def run_pytest(test_dirs: list, pytest_args: list, test_type: str = 'all') -> int:
    """
    执行 pytest
    
    Returns:
        pytest 返回码
    """
    # 构建 pytest 命令
    cmd = ['pytest'] + pytest_args
    
    # 添加测试目录
    for test_dir in test_dirs:
        if test_type == 'api' and 'api' not in test_dir:
            continue
        if test_type == 'app' and 'app' not in test_dir:
            continue
        if os.path.exists(test_dir):
            cmd.append(test_dir)
    
    logger.info(f"🚀 执行命令：{' '.join(cmd)}")
    
    # 执行 pytest
    result = subprocess.run(cmd, capture_output=False)
    
    return result.returncode


def get_ci_info() -> dict:
    """获取 CI 环境信息"""
    return {
        'ci_build_number': os.environ.get('BUILD_NUMBER', os.environ.get('GITHUB_RUN_NUMBER', None)),
        'git_commit': os.environ.get('GIT_COMMIT', os.environ.get('GITHUB_SHA', None)),
        'branch': os.environ.get('BRANCH_NAME', os.environ.get('GITHUB_REF_NAME', None)),
        'is_ci': os.environ.get('CI', 'false').lower() == 'true'
    }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='自动化测试执行')
    parser.add_argument('--type', choices=['all', 'api', 'app'], default='all',
                        help='测试类型')
    parser.add_argument('--config', default='config/config.yaml',
                        help='配置文件路径')
    parser.add_argument('--ci-mode', action='store_true',
                        help='CI 模式运行')
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("🔁 启动自动化测试任务...")
    logger.info("=" * 60)
    
    start_time = time.time()
    
    # 加载配置
    config = load_config(args.config)
    if not config:
        logger.error("配置加载失败，退出")
        sys.exit(1)
    
    # 生成唯一运行 ID
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    logger.info(f"运行 ID: {run_id}")
    
    # 1. 清理旧数据
    clean_dirs = config.get('clean_dirs', [])
    if clean_dirs:
        logger.info("🧹 清理旧报告...")
        clean_directories(clean_dirs)
    
    # 2. 记录执行信息
    record_execution_info(config.get('execution_record_file', './reports/execution_info.json'))
    
    # 3. 获取 CI 信息
    ci_info = get_ci_info()
    if ci_info['is_ci']:
        logger.info(f"🏗️ CI 模式 - Build: {ci_info['ci_build_number']}, Branch: {ci_info['branch']}")
    
    # 4. 执行测试
    test_dirs = config.get('test', {}).get('test_dirs', ['tests'])
    pytest_args = config.get('test', {}).get('pytest_args', ['-v'])
    
    logger.info(f"📁 测试目录：{test_dirs}")
    logger.info(f"📝 测试类型：{args.type}")
    
    return_code = run_pytest(test_dirs, pytest_args, args.type)
    
    # 5. 解析测试报告
    json_report_path = config.get('reports', {}).get('json_report', './reports/pytest-report.json')
    test_stats = analyze_pytest_report(json_report_path)
    
    if not test_stats:
        logger.error("❌ 无法解析测试报告，退出")
        sys.exit(1)
    
    # 6. 计算执行时间
    duration = time.time() - start_time
    logger.info(f"⏱️ 执行耗时：{duration:.2f} 秒")
    
    # 7. 保存结果到数据库
    db_path = config.get('database', {}).get('path', './database/test_results.db')
    db = TestResultDB(db_path)
    
    db.save_test_run(
        stats=test_stats,
        run_id=run_id,
        test_type=args.type,
        ci_build_number=ci_info['ci_build_number'],
        git_commit=ci_info['git_commit'],
        branch=ci_info['branch'],
        duration_seconds=duration
    )
    
    if test_stats['has_failures']:
        db.save_failure_details(run_id, test_stats.get('failures', []))
    
    logger.info(f"💾 测试结果已保存到数据库：{db_path}")
    
    # 8. 生成报告
    reports_dir = config.get('reports', {}).get('output_dir', './reports')
    trend_data = db.get_trend_data(days=30)
    
    report_paths = generate_all_reports(
        stats=test_stats,
        reports_dir=reports_dir,
        trend_data=trend_data,
        failure_details=test_stats.get('failures', [])
    )
    
    logger.info(f"📄 报告已生成:")
    logger.info(f"   HTML: {report_paths['latest_html']}")
    logger.info(f"   Markdown: {report_paths['latest_markdown']}")
    
    # 9. 发送通知（严格模式：有失败就通知）
    notification_config = config.get('notification', {})
    if notification_config.get('strict_mode', True) and test_stats['has_failures']:
        logger.info("📢 发送失败通知...")
        
        manager = NotificationManager(args.config)
        results = manager.send_all(
            stats=test_stats,
            report_url=f"file://{os.path.abspath(report_paths['latest_html'])}"
        )
        
        for channel, success in results.items():
            status = "✅" if success else "❌"
            logger.info(f"   {status} {channel}: {'成功' if success else '失败'}")
    else:
        if not test_stats['has_failures']:
            logger.info("✅ 所有用例通过，无需发送通知")
        else:
            logger.info("⏭️ 通知已禁用，跳过发送")
    
    # 10. 输出总结
    logger.info("=" * 60)
    logger.info("📊 测试总结")
    logger.info("=" * 60)
    logger.info(f"总用例数：{test_stats['total']}")
    logger.info(f"✅ 通过：{test_stats['passed']}")
    logger.info(f"❌ 失败：{test_stats['failed']}")
    logger.info(f"⏭️ 跳过：{test_stats['skipped']}")
    logger.info(f"📈 通过率：{test_stats['pass_rate']}%")
    logger.info(f"⏱️ 耗时：{duration:.2f}秒")
    logger.info("=" * 60)
    
    # 11. 返回退出码
    if test_stats['has_failures']:
        logger.error("❌ 测试执行存在失败用例")
        sys.exit(1)
    else:
        logger.info("🎉 所有测试用例通过！")
        sys.exit(0)


if __name__ == '__main__':
    main()
