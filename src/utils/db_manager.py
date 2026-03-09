#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理模块 - 存储测试结果用于趋势分析
"""

import sqlite3
from datetime import datetime
from pathlib import Path
import json


class TestResultDB:
    """测试结果数据库管理类"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()
    
    def init_db(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 测试执行记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total INTEGER NOT NULL,
                passed INTEGER NOT NULL,
                failed INTEGER NOT NULL,
                skipped INTEGER NOT NULL,
                xfailed INTEGER DEFAULT 0,
                xpassed INTEGER DEFAULT 0,
                pass_rate REAL NOT NULL,
                duration_seconds REAL,
                test_type TEXT,  -- api / app / all
                ci_build_number TEXT,
                git_commit TEXT,
                branch TEXT,
                status TEXT NOT NULL  -- success / failure
            )
        ''')
        
        # 失败用例详情表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                test_name TEXT NOT NULL,
                test_file TEXT,
                error_message TEXT,
                error_traceback TEXT,
                duration_seconds REAL,
                FOREIGN KEY (run_id) REFERENCES test_runs(run_id)
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_run_id ON test_failures(run_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON test_runs(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON test_runs(status)')
        
        conn.commit()
        conn.close()
    
    def save_test_run(self, stats: dict, run_id: str, test_type: str = 'all',
                      ci_build_number: str = None, git_commit: str = None,
                      branch: str = None, duration_seconds: float = None):
        """保存测试执行记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        status = 'failure' if stats['has_failures'] else 'success'
        
        cursor.execute('''
            INSERT INTO test_runs 
            (run_id, total, passed, failed, skipped, xfailed, xpassed, 
             pass_rate, duration_seconds, test_type, ci_build_number, 
             git_commit, branch, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            run_id,
            stats['total'],
            stats['passed'],
            stats['failed'],
            stats['skipped'],
            stats.get('xfailed', 0),
            stats.get('xpassed', 0),
            stats['pass_rate'],
            duration_seconds,
            test_type,
            ci_build_number,
            git_commit,
            branch,
            status
        ))
        
        conn.commit()
        conn.close()
        return run_id
    
    def save_failure_details(self, run_id: str, failures: list):
        """保存失败用例详情"""
        if not failures:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for failure in failures:
            cursor.execute('''
                INSERT INTO test_failures 
                (run_id, test_name, test_file, error_message, error_traceback, duration_seconds)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                run_id,
                failure.get('test_name', 'unknown'),
                failure.get('test_file', ''),
                failure.get('error_message', '')[:500],  # 限制长度
                failure.get('error_traceback', '')[:2000],
                failure.get('duration', 0)
            ))
        
        conn.commit()
        conn.close()
    
    def get_recent_runs(self, limit: int = 10):
        """获取最近的测试执行记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT run_id, created_at, total, passed, failed, skipped, 
                   pass_rate, status, test_type
            FROM test_runs
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        columns = ['run_id', 'created_at', 'total', 'passed', 'failed', 
                   'skipped', 'pass_rate', 'status', 'test_type']
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def get_trend_data(self, days: int = 30):
        """获取趋势分析数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date(created_at) as date, 
                   AVG(pass_rate) as avg_pass_rate,
                   COUNT(*) as run_count,
                   SUM(failed) as total_failures
            FROM test_runs
            WHERE created_at >= date('now', ?)
            GROUP BY date(created_at)
            ORDER BY date ASC
        ''', (f'-{days} days',))
        
        columns = ['date', 'avg_pass_rate', 'run_count', 'total_failures']
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def get_statistics(self):
        """获取总体统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_runs,
                AVG(pass_rate) as avg_pass_rate,
                MIN(pass_rate) as min_pass_rate,
                MAX(pass_rate) as max_pass_rate,
                SUM(total) as total_tests,
                SUM(passed) as total_passed,
                SUM(failed) as total_failed
            FROM test_runs
        ''')
        
        row = cursor.fetchone()
        columns = ['total_runs', 'avg_pass_rate', 'min_pass_rate', 'max_pass_rate',
                   'total_tests', 'total_passed', 'total_failed']
        result = dict(zip(columns, row)) if row else {}
        
        conn.close()
        return result


# 使用示例
if __name__ == '__main__':
    db = TestResultDB('./database/test_results.db')
    
    # 示例：保存测试结果
    stats = {
        'total': 50,
        'passed': 48,
        'failed': 2,
        'skipped': 0,
        'pass_rate': 96.0,
        'has_failures': True
    }
    
    run_id = db.save_test_run(stats, 'run_20240101_120000', duration_seconds=120.5)
    print(f"Saved test run: {run_id}")
    
    # 查询最近记录
    recent = db.get_recent_runs(5)
    print(f"Recent runs: {recent}")
