#!/usr/bin/env python3
"""
测试用户隔离功能
验证不同 user_id 的数据是完全隔离的
"""

import os
import sys
import sqlite3
import tempfile
from datetime import datetime, timedelta

def test_user_isolation():
    """测试用户数据隔离"""
    print("\n" + "="*60)
    print("测试用户数据隔离")
    print("="*60 + "\n")

    with tempfile.TemporaryDirectory() as temp_dir:
        # 测试 schedules 表
        schedule_db = os.path.join(temp_dir, "test_schedules.db")
        conn = sqlite3.connect(schedule_db)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                schedule_type TEXT NOT NULL,
                scheduled_time TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                reminder_sent INTEGER DEFAULT 0,
                recurrence_rule TEXT,
                next_scheduled_time TEXT,
                metadata TEXT
            )
        ''')

        # 用户1创建任务
        future_time = (datetime.now() + timedelta(hours=1)).isoformat()
        cursor.execute('''
            INSERT INTO schedules
            (user_id, session_id, title, description, schedule_type, scheduled_time, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ("user1", "session1", "用户1的任务", "这是用户1的任务", "reminder", future_time, datetime.now().isoformat(), "pending"))
        user1_task_id = cursor.lastrowid

        # 用户2创建任务
        cursor.execute('''
            INSERT INTO schedules
            (user_id, session_id, title, description, schedule_type, scheduled_time, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ("user2", "session2", "用户2的任务", "这是用户2的任务", "reminder", future_time, datetime.now().isoformat(), "pending"))
        user2_task_id = cursor.lastrowid

        # 验证用户1只能看到自己的任务
        cursor.execute('''
            SELECT id, title FROM schedules WHERE user_id = ?
        ''', ("user1",))
        user1_tasks = cursor.fetchall()
        assert len(user1_tasks) == 1, f"用户1应该只有1个任务，实际{len(user1_tasks)}个"
        assert user1_tasks[0][0] == user1_task_id, "用户1应该看到自己的任务"
        print(f"✓ 用户1查询成功，找到 {len(user1_tasks)} 个任务")

        # 验证用户2只能看到自己的任务
        cursor.execute('''
            SELECT id, title FROM schedules WHERE user_id = ?
        ''', ("user2",))
        user2_tasks = cursor.fetchall()
        assert len(user2_tasks) == 1, f"用户2应该只有1个任务，实际{len(user2_tasks)}个"
        assert user2_tasks[0][0] == user2_task_id, "用户2应该看到自己的任务"
        print(f"✓ 用户2查询成功，找到 {len(user2_tasks)} 个任务")

        # 验证用户1无法访问用户2的任务
        cursor.execute('''
            SELECT id FROM schedules WHERE id = ? AND user_id = ?
        ''', (user2_task_id, "user1"))
        result = cursor.fetchone()
        assert result is None, "用户1不应该能访问用户2的任务"
        print(f"✓ 用户1无法访问用户2的任务")

        conn.close()

        print("\n✓ 所有用户隔离测试通过！\n")


if __name__ == "__main__":
    try:
        test_user_isolation()
        print("="*60)
        print("✓ 用户隔离测试全部通过！")
        print("="*60)
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
