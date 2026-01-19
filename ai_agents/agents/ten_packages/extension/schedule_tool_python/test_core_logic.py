#!/usr/bin/env python3
"""
测试 Schedule Tool 的核心逻辑（不依赖框架）
包括：时间解析、重复任务计算、数据库操作等
"""

import os
import sys
import sqlite3
import tempfile
from datetime import datetime, timedelta
import re

# 直接复制核心逻辑进行测试
def parse_relative_time(time_str: str) -> datetime:
    """解析相对时间"""
    now = datetime.now()
    time_str = time_str.lower()

    # 匹配"X分钟后"
    match = re.search(r'(\d+)\s*分钟', time_str)
    if match:
        minutes = int(match.group(1))
        return now + timedelta(minutes=minutes)

    # 匹配"X小时后"
    match = re.search(r'(\d+)\s*小时', time_str)
    if match:
        hours = int(match.group(1))
        return now + timedelta(hours=hours)

    # 匹配"明天X点"
    if "明天" in time_str:
        match = re.search(r'(\d+)\s*点', time_str)
        hour = int(match.group(1)) if match else 9
        match_min = re.search(r'(\d+)\s*分', time_str)
        minute = int(match_min.group(1)) if match_min else 0
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # 匹配"X天后"
    match = re.search(r'(\d+)\s*天', time_str)
    if match:
        days = int(match.group(1))
        return now + timedelta(days=days)

    # 默认：1小时后
    return now + timedelta(hours=1)


def calculate_next_recurrence(base_time: datetime, recurrence_rule: str) -> datetime:
    """计算下一个重复执行时间"""
    rule = recurrence_rule.lower().strip()
    now = datetime.now()

    if rule == "daily" or rule == "每天":
        # 每天同一时间
        today_at_time = now.replace(
            hour=base_time.hour,
            minute=base_time.minute,
            second=0,
            microsecond=0
        )

        if today_at_time > now:
            return today_at_time
        return today_at_time + timedelta(days=1)

    elif rule == "weekly" or rule == "每周":
        next_time = now.replace(
            hour=base_time.hour,
            minute=base_time.minute,
            second=0,
            microsecond=0
        )
        days_ahead = base_time.weekday() - next_time.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return next_time + timedelta(days=days_ahead)

    elif rule == "monthly" or rule == "每月":
        next_time = now.replace(
            hour=base_time.hour,
            minute=base_time.minute,
            second=0,
            microsecond=0
        )
        if next_time.month == 12:
            next_time = next_time.replace(year=next_time.year + 1, month=1, day=base_time.day)
        else:
            try:
                next_time = next_time.replace(month=next_time.month + 1, day=base_time.day)
            except ValueError:
                if next_time.month == 12:
                    next_time = next_time.replace(year=next_time.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    next_time = next_time.replace(month=next_time.month + 1, day=1) - timedelta(days=1)
        if next_time <= now:
            if next_time.month == 12:
                next_time = next_time.replace(year=next_time.year + 1, month=1, day=base_time.day)
            else:
                try:
                    next_time = next_time.replace(month=next_time.month + 1, day=base_time.day)
                except ValueError:
                    if next_time.month == 12:
                        next_time = next_time.replace(year=next_time.year + 1, month=1, day=1) - timedelta(days=1)
                    else:
                        next_time = next_time.replace(month=next_time.month + 1, day=1) - timedelta(days=1)
        return next_time

    elif rule == "weekdays" or rule == "工作日":
        next_time = base_time + timedelta(days=1)
        while next_time.weekday() >= 5:
            next_time += timedelta(days=1)
        return next_time

    elif rule == "weekends" or rule == "周末":
        next_time = base_time + timedelta(days=1)
        while next_time.weekday() < 5:
            next_time += timedelta(days=1)
        return next_time

    elif rule.startswith("every_"):
        parts = rule.split("_")
        if len(parts) >= 3:
            try:
                n = int(parts[1])
                unit = parts[2] if len(parts) > 2 else "days"

                if unit.startswith("day"):
                    return base_time + timedelta(days=n)
                elif unit.startswith("week"):
                    return base_time + timedelta(weeks=n)
                elif unit.startswith("month"):
                    return base_time + timedelta(days=n * 30)
            except ValueError:
                pass

    return base_time + timedelta(days=1)


def test_time_parsing():
    """测试时间解析"""
    print("\n" + "="*60)
    print("测试时间解析功能")
    print("="*60 + "\n")

    now = datetime.now()

    # 测试1: 30分钟后
    parsed = parse_relative_time("30分钟后")
    expected = now + timedelta(minutes=30)
    assert abs((parsed - expected).total_seconds()) < 60, f"30分钟后解析错误"
    print(f"✓ '30分钟后' 解析正确: {parsed.strftime('%Y-%m-%d %H:%M:%S')}")

    # 测试2: 2小时后
    parsed = parse_relative_time("2小时后")
    expected = now + timedelta(hours=2)
    assert abs((parsed - expected).total_seconds()) < 60, f"2小时后解析错误"
    print(f"✓ '2小时后' 解析正确: {parsed.strftime('%Y-%m-%d %H:%M:%S')}")

    # 测试3: 明天9点
    parsed = parse_relative_time("明天9点")
    tomorrow = now + timedelta(days=1)
    expected = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
    assert parsed.date() == expected.date(), f"明天日期错误"
    assert parsed.hour == 9, f"小时错误"
    print(f"✓ '明天9点' 解析正确: {parsed.strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n✓ 所有时间解析测试通过！\n")


def test_recurrence_calculation():
    """测试重复任务计算"""
    print("\n" + "="*60)
    print("测试重复任务时间计算")
    print("="*60 + "\n")

    now = datetime.now()

    # 测试1: 每天 - 今天时间已过
    base_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
    if base_time < now:
        next_time = calculate_next_recurrence(base_time, "daily")
        assert next_time.date() > now.date() or (next_time.date() == now.date() and next_time > now), f"应该返回未来时间"
        assert next_time.hour == 8 and next_time.minute == 0, f"时间应该保持"
        print(f"✓ 每天（已过时间）计算正确: {next_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 测试2: 每天 - 今天时间未到
    base_time = now.replace(hour=23, minute=0, second=0, microsecond=0)
    if base_time > now:
        next_time = calculate_next_recurrence(base_time, "daily")
        assert next_time.date() == now.date(), f"应该返回今天"
        assert next_time.hour == 23 and next_time.minute == 0, f"时间应该保持"
        print(f"✓ 每天（未到时间）计算正确: {next_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 测试3: 每周
    base_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
    next_time = calculate_next_recurrence(base_time, "weekly")
    assert next_time.weekday() == base_time.weekday(), f"应该保持相同的星期几"
    assert next_time.hour == 9 and next_time.minute == 0, f"时间应该保持"
    print(f"✓ 每周计算正确: {next_time.strftime('%Y-%m-%d %H:%M:%S')} (星期{next_time.weekday()})")

    # 测试4: 工作日
    base_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
    next_time = calculate_next_recurrence(base_time, "weekdays")
    assert next_time.weekday() < 5, f"应该是工作日"
    print(f"✓ 工作日计算正确: {next_time.strftime('%Y-%m-%d %H:%M:%S')} (星期{next_time.weekday()})")

    # 测试5: 每3天
    base_time = now.replace(hour=10, minute=0, second=0, microsecond=0)
    next_time = calculate_next_recurrence(base_time, "every_3_days")
    expected = base_time + timedelta(days=3)
    assert abs((next_time - expected).total_seconds()) < 60, f"每3天计算错误"
    print(f"✓ 每3天计算正确: {next_time.strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n✓ 所有重复任务计算测试通过！\n")


def test_database_operations():
    """测试数据库操作"""
    print("\n" + "="*60)
    print("测试数据库操作")
    print("="*60 + "\n")

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test_schedules.db")

        # 初始化数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        conn.commit()

        # 测试1: 插入单次任务
        future_time = (datetime.now() + timedelta(hours=1)).isoformat()
        cursor.execute('''
            INSERT INTO schedules
            (session_id, title, description, schedule_type, scheduled_time, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ("test_session", "测试任务", "描述", "reminder", future_time, datetime.now().isoformat(), "pending"))
        task_id_1 = cursor.lastrowid
        print(f"✓ 插入单次任务成功，ID: {task_id_1}")

        # 测试2: 插入重复任务
        tomorrow_10am = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
        next_time = calculate_next_recurrence(tomorrow_10am, "daily")
        cursor.execute('''
            INSERT INTO schedules
            (session_id, title, schedule_type, scheduled_time, created_at, status, recurrence_rule, next_scheduled_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ("test_session", "每天吃药", "reminder", tomorrow_10am.isoformat(),
              datetime.now().isoformat(), "pending", "daily", next_time.isoformat()))
        task_id_2 = cursor.lastrowid
        print(f"✓ 插入重复任务成功，ID: {task_id_2}")

        # 测试3: 查询任务
        cursor.execute('''
            SELECT id, title, recurrence_rule, next_scheduled_time
            FROM schedules
            WHERE session_id = ?
        ''', ("test_session",))
        rows = cursor.fetchall()
        assert len(rows) == 2, f"应该找到2个任务，实际找到{len(rows)}个"
        print(f"✓ 查询任务成功，找到 {len(rows)} 个任务")

        # 测试4: 更新任务状态
        cursor.execute('''
            UPDATE schedules
            SET status = 'cancelled'
            WHERE id = ?
        ''', (task_id_1,))
        cursor.execute('SELECT status FROM schedules WHERE id = ?', (task_id_1,))
        status = cursor.fetchone()[0]
        assert status == "cancelled", f"状态应该为 cancelled"
        print(f"✓ 更新任务状态成功")

        # 测试5: 更新重复任务的下次时间
        new_next_time = calculate_next_recurrence(tomorrow_10am, "daily")
        cursor.execute('''
            UPDATE schedules
            SET next_scheduled_time = ?
            WHERE id = ?
        ''', (new_next_time.isoformat(), task_id_2))
        cursor.execute('SELECT next_scheduled_time FROM schedules WHERE id = ?', (task_id_2,))
        stored_time = cursor.fetchone()[0]
        assert stored_time == new_next_time.isoformat(), f"下次时间更新失败"
        print(f"✓ 更新重复任务下次时间成功")

        conn.close()
        print("\n✓ 所有数据库操作测试通过！\n")


if __name__ == "__main__":
    try:
        test_time_parsing()
        test_recurrence_calculation()
        test_database_operations()
        print("="*60)
        print("✓ 所有测试通过！")
        print("="*60)
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
