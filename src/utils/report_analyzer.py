#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告分析模块 - 解析 pytest JSON 报告并提取统计信息
"""

import json
import os
from typing import Optional, Dict, List
from loguru import logger


def analyze_pytest_report(json_report_path: str) -> Optional[Dict]:
    """
    解析 pytest 生成的 JSON 报告，返回统计信息
    
    Args:
        json_report_path: JSON 报告文件路径
        
    Returns:
        包含统计信息的字典，解析失败返回 None
    """
    if not os.path.exists(json_report_path):
        logger.warning(f"未找到 pytest JSON 报告：{json_report_path}")
        return None

    try:
        with open(json_report_path, encoding='utf-8') as f:
            report_data = json.load(f)

        summary = report_data.get('summary', {})
        
        total = summary.get('total', 0)
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        skipped = summary.get('skipped', 0)
        xfailed = summary.get('xfailed', 0)
        xpassed = summary.get('xpassed', 0)

        # 计算通过率
        executed = passed + failed + skipped
        pass_rate = (passed / executed * 100) if executed > 0 else 0

        # 提取失败用例详情
        failures = []
        tests = report_data.get('tests', [])
        for test in tests:
            if test.get('outcome') == 'failed':
                failures.append({
                    'test_name': test.get('nodeid', 'unknown'),
                    'test_file': test.get('filename', ''),
                    'error_message': _extract_error_message(test),
                    'error_traceback': test.get('call', {}).get('longrepr', ''),
                    'duration': test.get('duration', 0)
                })

        stats = {
            'total': total,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'xfailed': xfailed,
            'xpassed': xpassed,
            'executed': executed,
            'pass_rate': round(pass_rate, 2),
            'has_failures': failed > 0,
            'failures': failures,
            'failure_count': len(failures)
        }

        logger.info(f"📊 测试统计结果：总数={total}, 通过={passed}, 失败={failed}, 通过率={pass_rate}%")
        return stats

    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败：{e}")
        return None
    except Exception as e:
        logger.error(f"解析 pytest JSON 报告失败：{e}")
        return None


def _extract_error_message(test: Dict) -> str:
    """从测试结果中提取错误消息"""
    call_data = test.get('call', {})
    longrepr = call_data.get('longrepr', '')
    
    if isinstance(longrepr, str):
        # 提取第一行作为错误消息
        lines = longrepr.strip().split('\n')
        for line in lines:
            if line.strip() and not line.startswith('E   '):
                continue
            if line.startswith('E   '):
                return line[3:].strip()
        return lines[0][:200] if lines else 'Unknown error'
    
    return str(longrepr)[:200]


def get_failure_summary(stats: Dict, max_failures: int = 5) -> str:
    """
    生成失败用例摘要（用于通知）
    
    Args:
        stats: 统计信息字典
        max_failures: 最大显示的失败用例数
        
    Returns:
        失败摘要字符串
    """
    if not stats.get('failures'):
        return "无失败用例"
    
    failures = stats['failures'][:max_failures]
    summary_lines = []
    
    for i, f in enumerate(failures, 1):
        test_name = f['test_name'].split('::')[-1][:50]
        error_msg = f['error_message'][:100]
        summary_lines.append(f"{i}. {test_name}\n   └─ {error_msg}")
    
    if len(failures) < stats['failure_count']:
        summary_lines.append(f"... 还有 {stats['failure_count'] - len(failures)} 个失败用例")
    
    return '\n\n'.join(summary_lines)


def analyze_test_duration(report_data: Dict) -> Dict:
    """分析测试执行时间"""
    tests = report_data.get('tests', [])
    
    durations = [t.get('duration', 0) for t in tests if t.get('duration')]
    
    if not durations:
        return {'total': 0, 'avg': 0, 'min': 0, 'max': 0, 'slowest': []}
    
    # 找出最慢的测试
    sorted_tests = sorted(tests, key=lambda x: x.get('duration', 0), reverse=True)
    slowest = [
        {
            'name': t.get('nodeid', '').split('::')[-1],
            'duration': t.get('duration', 0)
        }
        for t in sorted_tests[:5]
    ]
    
    return {
        'total': sum(durations),
        'avg': sum(durations) / len(durations),
        'min': min(durations),
        'max': max(durations),
        'slowest': slowest
    }


# 使用示例
if __name__ == '__main__':
    stats = analyze_pytest_report('./reports/pytest-report.json')
    if stats:
        print(f"通过率：{stats['pass_rate']}%")
        if stats['has_failures']:
            print("\n失败摘要:")
            print(get_failure_summary(stats))
