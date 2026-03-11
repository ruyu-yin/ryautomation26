
# -*- coding: utf-8 -*-
"""
报告生成模块 - 生成 HTML 和 Markdown 格式的质量报告
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

try:
    import markdown
    from jinja2 import Template
except ImportError:
    logger.warning("缺少依赖：pip install Jinja2 markdown")


def generate_markdown_report(stats: Dict, output_path: str, 
                             trend_data: List[Dict] = None,
                             failure_details: List[Dict] = None) -> str:
    """
    生成 Markdown 格式测试报告
    
    Args:
        stats: 测试统计信息
        output_path: 输出文件路径
        trend_data: 趋势数据（可选）
        failure_details: 失败详情（可选）
        
    Returns:
        生成的报告内容
    """
    exec_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status = "❌ 失败" if stats['has_failures'] else "✅ 通过"
    
    content = f"""# 自动化测试报告

## 执行信息

- **执行时间**: {exec_time}
- **测试状态**: {status}
- **测试类型**: API + Android App

---

## 📊 测试统计

| 指标 | 数值 |
|------|------|
| 总用例数 | {stats['total']} |
| ✅ 通过 | {stats['passed']} |
| ❌ 失败 | {stats['failed']} |
| ⏭️ 跳过 | {stats['skipped']} |
| **通过率** | **{stats['pass_rate']}%** |

---

## 失败用例详情

"""
    
    if failure_details:
        for i, failure in enumerate(failure_details[:10], 1):
            test_name = failure.get('test_name', 'unknown').split('::')[-1]
            error_msg = failure.get('error_message', 'Unknown error')
            content += f"""### {i}. {test_name}

```
{error_msg}
```

"""
        if len(failure_details) > 10:
            content += f"\n> ... 还有 {len(failure_details) - 10} 个失败用例，请查看完整报告\n"
    else:
        content += "无失败用例 🎉\n"
    
    if trend_data:
        content += """
---

## 📈 趋势分析（最近 30 天）

| 日期 | 平均通过率 | 执行次数 | 总失败数 |
|------|-----------|---------|---------|
"""
        for day in trend_data[-7:]:
            content += f"| {day['date']} | {day['avg_pass_rate']:.1f}% | {day['run_count']} | {day['total_failures']} |\n"
    
    content += f"""
---

*报告生成时间：{exec_time}*
*自动化测试平台 v1.0*
"""
    
    # 确保目录存在
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"📝 Markdown 报告已生成：{output_path}")
    return content


def generate_html_report(stats: Dict, output_path: str,
                         trend_data: List[Dict] = None,
                         failure_details: List[Dict] = None) -> str:
    """
    生成 HTML 格式测试报告
    
    Args:
        stats: 测试统计信息
        output_path: 输出文件路径
        trend_data: 趋势数据（可选）
        failure_details: 失败详情（可选）
        
    Returns:
        生成的 HTML 内容
    """
    exec_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status_text = "失败" if stats['has_failures'] else "通过"
    status_color = "#d32f2f" if stats['has_failures'] else "#388e3c"
    status_icon = "❌" if stats['has_failures'] else "✅"
    
    # 生成失败详情 HTML
    failures_html = ""
    if failure_details:
        for i, failure in enumerate(failure_details[:10], 1):
            test_name = failure.get('test_name', 'unknown').split('::')[-1]
            error_msg = failure.get('error_message', 'Unknown error')
            failures_html += f"""
            <div class="failure-item">
                <div class="failure-header">
                    <span class="failure-number">{i}</span>
                    <span class="failure-name">{test_name}</span>
                </div>
                <div class="failure-error"><code>{error_msg}</code></div>
            </div>
            """
        if len(failure_details) > 10:
            failures_html += f'<p class="more-failures">... 还有 {len(failure_details) - 10} 个失败用例</p>'
    else:
        failures_html = '<p class="no-failures">无失败用例 🎉</p>'
    
    # 生成趋势图表 HTML（简单表格版）
    trend_html = ""
    if trend_data:
        trend_rows = ""
        for day in trend_data[-7:]:
            trend_rows += f"""
            <tr>
                <td>{day['date']}</td>
                <td>{day['avg_pass_rate']:.1f}%</td>
                <td>{day['run_count']}</td>
                <td>{day['total_failures']}</td>
            </tr>
            """
        trend_html = f"""
        <h2>📈 趋势分析（最近 7 天）</h2>
        <table class="trend-table">
            <thead>
                <tr>
                    <th>日期</th>
                    <th>平均通过率</th>
                    <th>执行次数</th>
                    <th>总失败数</th>
                </tr>
            </thead>
            <tbody>
                {trend_rows}
            </tbody>
        </table>
        """
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>自动化测试报告 - {exec_time}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        .container {{ background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 30px; }}
        h1 {{ color: #1a73e8; margin-bottom: 10px; }}
        h2 {{ color: #333; margin: 30px 0 15px; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; }}
        .exec-info {{ background: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 20px; }}
        .status-badge {{ display: inline-block; padding: 6px 16px; border-radius: 20px; color: white; font-weight: bold; }}
        .status-pass {{ background: #388e3c; }}
        .status-fail {{ background: #d32f2f; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #1a73e8; }}
        .stat-label {{ color: #666; font-size: 0.9em; margin-top: 5px; }}
        .pass-rate {{ font-size: 2.5em; color: {status_color}; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #1a73e8; color: white; }}
        tr:hover {{ background: #f5f5f5; }}
        .failure-item {{ background: #ffebee; border-left: 4px solid #d32f2f; padding: 15px; margin: 10px 0; border-radius: 4px; }}
        .failure-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }}
        .failure-number {{ background: #d32f2f; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8em; }}
        .failure-name {{ font-weight: bold; color: #c62828; }}
        .failure-error {{ background: #fff; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 0.9em; overflow-x: auto; }}
        .no-failures {{ color: #388e3c; font-size: 1.2em; text-align: center; padding: 30px; }}
        .more-failures {{ color: #666; font-style: italic; text-align: center; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 0.9em; text-align: center; }}
        .trend-table {{ background: #fff; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 自动化测试报告</h1>
        
        <div class="exec-info">
            <p><strong>执行时间</strong>: {exec_time}</p>
            <p><strong>测试状态</strong>: <span class="status-badge {'status-pass' if not stats['has_failures'] else 'status-fail'}">{status_icon} {status_text}</span></p>
            <p><strong>测试类型</strong>: API + Android App</p>
        </div>
        
        <h2>📊 测试统计</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats['total']}</div>
                <div class="stat-label">总用例数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #388e3c;">{stats['passed']}</div>
                <div class="stat-label">✅ 通过</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #d32f2f;">{stats['failed']}</div>
                <div class="stat-label">❌ 失败</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['skipped']}</div>
                <div class="stat-label">⏭️ 跳过</div>
            </div>
            <div class="stat-card">
                <div class="pass-rate">{stats['pass_rate']}%</div>
                <div class="stat-label">通过率</div>
            </div>
        </div>
        
        <h2>🐛 失败用例详情</h2>
        {failures_html}
        
        {trend_html}
        
        <div class="footer">
            <p>报告生成时间：{exec_time}</p>
            <p>自动化测试平台 v1.0</p>
        </div>
    </div>
</body>
</html>
"""
    
    # 确保目录存在
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    logger.info(f"📄 HTML 报告已生成：{output_path}")
    return html


def generate_all_reports(stats: Dict, reports_dir: str,
                         trend_data: List[Dict] = None,
                         failure_details: List[Dict] = None) -> Dict[str, str]:
    """
    生成所有格式的报告
    
    Returns:
        各报告文件路径
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    paths = {
        'markdown': os.path.join(reports_dir, 'markdown', f'report_{timestamp}.md'),
        'html': os.path.join(reports_dir, 'html', f'report_{timestamp}.html')
    }
    
    generate_markdown_report(stats, paths['markdown'], trend_data, failure_details)
    generate_html_report(stats, paths['html'], trend_data, failure_details)
    
    # 同时生成 latest 版本
    latest_paths = {
        'markdown': os.path.join(reports_dir, 'markdown', 'latest.md'),
        'html': os.path.join(reports_dir, 'html', 'latest.html')
    }
    
    generate_markdown_report(stats, latest_paths['markdown'], trend_data, failure_details)
    generate_html_report(stats, latest_paths['html'], trend_data, failure_details)
    
    paths['latest_markdown'] = latest_paths['markdown']
    paths['latest_html'] = latest_paths['html']
    
    return paths


# 使用示例
if __name__ == '__main__':
    stats = {
        'total': 50,
        'passed': 45,
        'failed': 5,
        'skipped': 0,
        'pass_rate': 90.0,
        'has_failures': True
    }
    
    paths = generate_all_reports(stats, './reports')
    print(f"报告生成完成：{paths}")
