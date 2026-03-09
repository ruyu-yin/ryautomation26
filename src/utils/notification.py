#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知模块 - 飞书和邮件通知
"""

import json
import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, Optional
import yaml
import requests
from loguru import logger


class FeishuNotifier:
    """飞书机器人通知"""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.webhook_url = self.config.get('webhook_url', '')
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        if not os.path.exists(config_path):
            logger.warning(f"飞书配置文件不存在：{config_path}")
            return {}
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def send_notification(self, stats: Dict, report_url: str = '') -> bool:
        """
        发送飞书通知
        
        Args:
            stats: 测试统计信息
            report_url: 报告链接
            
        Returns:
            是否发送成功
        """
        if not self.webhook_url or 'YOUR_WEBHOOK_TOKEN' in self.webhook_url:
            logger.warning("飞书 Webhook URL 未配置，跳过通知")
            return False
        
        exec_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status_emoji = "❌" if stats['has_failures'] else "✅"
        status_text = "失败" if stats['has_failures'] else "通过"
        
        # 生成失败详情
        failure_details = ""
        if stats['has_failures']:
            from .report_analyzer import get_failure_summary
            failure_details = f"\n**失败详情**:\n{get_failure_summary(stats, max_failures=3)}"
        
        message = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"{status_emoji} 自动化测试{status_text}"
                    },
                    "template": "red" if stats['has_failures'] else "green"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"""**执行时间**: {exec_time}
**通过率**: {stats['pass_rate']}%
**测试结果**: {stats['passed']}/{stats['total']}

**失败用例数**: {stats['failed']}
**跳过用例数**: {stats['skipped']}"""
                        }
                    }
                ]
            }
        }
        
        if failure_details:
            message["card"]["elements"].append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": failure_details
                }
            })
        
        if report_url:
            message["card"]["elements"].append({
                "tag": "action",
                "actions": [{
                    "tag": "button",
                    "text": {
                        "tag": "plain_text",
                        "content": "查看报告"
                    },
                    "url": report_url,
                    "type": "default"
                }]
            })
        
        try:
            response = requests.post(
                self.webhook_url,
                json=message,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('StatusCode') == 0 or result.get('code') == 0:
                    logger.info("✅ 飞书通知发送成功")
                    return True
            
            logger.error(f"飞书通知发送失败：{response.text}")
            return False
            
        except Exception as e:
            logger.error(f"飞书通知发送异常：{e}")
            return False


class EmailNotifier:
    """邮件通知"""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        if not os.path.exists(config_path):
            logger.warning(f"邮件配置文件不存在：{config_path}")
            return {}
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 从环境变量获取密码
        smtp = config.get('smtp', {})
        password_env = smtp.get('password_env')
        if password_env:
            smtp['password'] = os.environ.get(password_env, '')
        
        return config
    
    def send_notification(self, stats: Dict, report_url: str = '') -> bool:
        """
        发送邮件通知
        
        Args:
            stats: 测试统计信息
            report_url: 报告链接
            
        Returns:
            是否发送成功
        """
        smtp = self.config.get('smtp', {})
        from_config = self.config.get('from', {})
        to_list = self.config.get('to', [])
        cc_list = self.config.get('cc', [])
        template = self.config.get('template', {})
        
        if not smtp.get('server') or not to_list:
            logger.warning("邮件配置不完整，跳过通知")
            return False
        
        exec_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status = "失败" if stats['has_failures'] else "通过"
        header_color = "#d32f2f" if stats['has_failures'] else "#388e3c"
        title = f"❌ 自动化测试失败" if stats['has_failures'] else "✅ 自动化测试通过"
        
        # 生成失败详情
        from .report_analyzer import get_failure_summary
        failure_details = get_failure_summary(stats, max_failures=10) if stats['has_failures'] else "无失败用例"
        
        # 渲染邮件正文
        body = template.get('body', '').format(
            header_color=header_color,
            title=title,
            exec_time=exec_time,
            total=stats['total'],
            passed=stats['passed'],
            failed=stats['failed'],
            skipped=stats['skipped'],
            pass_rate=stats['pass_rate'],
            failure_details=failure_details,
            report_url=report_url or '#'
        )
        
        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = template.get('subject', '[自动化测试] {status}').format(
            status=status,
            pass_rate=stats['pass_rate'],
            exec_time=exec_time
        )
        msg['From'] = f"{from_config.get('name', '')} <{from_config.get('email', '')}>"
        msg['To'] = ', '.join(to_list)
        if cc_list:
            msg['Cc'] = ', '.join(cc_list)
        
        msg.attach(MIMEText(body, 'html', 'utf-8'))
        
        try:
            server = smtplib.SMTP(smtp['server'], smtp['port'])
            if smtp.get('use_tls'):
                server.starttls()
            
            if smtp.get('username') and smtp.get('password'):
                server.login(smtp['username'], smtp['password'])
            
            all_recipients = to_list + cc_list
            server.sendmail(msg['From'], all_recipients, msg.as_string())
            server.quit()
            
            logger.info("✅ 邮件通知发送成功")
            return True
            
        except Exception as e:
            logger.error(f"邮件通知发送失败：{e}")
            return False


class NotificationManager:
    """通知管理器 - 统一管理多个通知渠道"""
    
    def __init__(self, config_path: str = 'config/config.yaml'):
        self.config = self._load_config(config_path)
        self.feishu_notifier = None
        self.email_notifier = None
        self._init_notifiers()
    
    def _load_config(self, config_path: str) -> Dict:
        """加载主配置"""
        if not os.path.exists(config_path):
            return {}
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _init_notifiers(self):
        """初始化通知器"""
        notification_config = self.config.get('notification', {})
        
        # 飞书通知
        feishu_config = notification_config.get('feishu', {})
        if feishu_config.get('enabled'):
            config_file = feishu_config.get('config_file', 'config/feishu_config.yaml')
            self.feishu_notifier = FeishuNotifier(config_file)
        
        # 邮件通知
        email_config = notification_config.get('email', {})
        if email_config.get('enabled'):
            config_file = email_config.get('config_file', 'config/email_config.yaml')
            self.email_notifier = EmailNotifier(config_file)
    
    def send_all(self, stats: Dict, report_url: str = '') -> Dict[str, bool]:
        """
        发送所有启用的通知渠道
        
        Args:
            stats: 测试统计信息
            report_url: 报告链接
            
        Returns:
            各渠道发送结果
        """
        results = {}
        
        if self.feishu_notifier:
            results['feishu'] = self.feishu_notifier.send_notification(stats, report_url)
        
        if self.email_notifier:
            results['email'] = self.email_notifier.send_notification(stats, report_url)
        
        return results


# 使用示例
if __name__ == '__main__':
    # 示例统计
    stats = {
        'total': 50,
        'passed': 45,
        'failed': 5,
        'skipped': 0,
        'pass_rate': 90.0,
        'has_failures': True
    }
    
    # 发送通知
    manager = NotificationManager()
    results = manager.send_all(stats, 'http://example.com/report')
    print(f"通知结果：{results}")
