#!/usr/bin/env python3
"""
测试 Schedule Tool Extension 的功能
包括：创建任务、查询任务、取消任务、重复任务等
"""

import os
import sys
import asyncio
import sqlite3
import tempfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock

# Add the extension path to Python path
sys.path.insert(
    0,
    os.path.dirname(os.path.abspath(__file__)),
)

# Mock ten_ai_base before importing extension
sys.modules['ten_ai_base'] = MagicMock()
sys.modules['ten_ai_base.types'] = MagicMock()
sys.modules['ten_ai_base.llm_tool'] = MagicMock()
sys.modules['ten_runtime'] = MagicMock()

# Create mock classes
class MockLLMToolMetadata:
    def __init__(self, name, description, parameters):
        self.name = name
        self.description = description
        self.parameters = parameters

class MockLLMToolMetadataParameter:
    def __init__(self, name, type, description, required):
        self.name = name
        self.type = type
        self.description = description
        self.required = required

class MockLLMToolResultLLMResult:
    def __init__(self, type, content):
        self.type = type
        self.content = content

# Patch the modules
sys.modules['ten_ai_base'].types.LLMToolMetadata = MockLLMToolMetadata
sys.modules['ten_ai_base'].types.LLMToolMetadataParameter = MockLLMToolMetadataParameter
sys.modules['ten_ai_base'].types.LLMToolResultLLMResult = MockLLMToolResultLLMResult
sys.modules['ten_ai_base'].llm_tool.AsyncLLMToolBaseExtension = object


class MockTenEnv:
    """模拟 TenEnv 对象"""
    def __init__(self):
        self.logs = []

    def log_debug(self, msg):
        self.logs.append(("debug", msg))
        print(f"[DEBUG] {msg}")

    def log_info(self, msg):
        self.logs.append(("info", msg))
        print(f"[INFO] {msg}")

    def log_warn(self, msg):
        self.logs.append(("warn", msg))
        print(f"[WARN] {msg}")

    def log_error(self, msg):
        self.logs.append(("error", msg))
        print(f"[ERROR] {msg}")


async def test_schedule_tool():
    """测试 Schedule Tool 的基本功能"""

    print("\n" + "="*60)
    print("测试 Schedule Tool Extension")
    print("="*60 + "\n")

    try:
        from extension import ScheduleToolExtension

        # 使用临时数据库
        with tempfile.TemporaryDirectory() as temp_dir:
            extension = ScheduleToolExtension("test_schedule")
            extension.db_path = os.path.join(temp_dir, "test_schedules.db")
            extension.session_id = "test_session"
            mock_env = MockTenEnv()
            extension.ten_env = mock_env

            # 初始化数据库
            extension._init_database()
            print("✓ 数据库初始化成功")

            # 测试1: 创建单次任务
            print("\n--- 测试1: 创建单次任务 ---")
            future_time = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
            result = await extension._create_schedule(
                mock_env,
                {
                    "title": "测试任务",
                    "scheduled_time": future_time,
                    "description": "这是一个测试任务",
                    "schedule_type": "reminder"
                },
                "test_session"
            )
            assert "已创建提醒" in result, f"创建任务失败: {result}"
            assert "测试任务" in result, f"任务标题未包含: {result}"
            schedule_id_1 = int(result.split("任务ID: ")[1])
            print(f"✓ 创建单次任务成功，ID: {schedule_id_1}")

            # 测试2: 创建重复任务（每天）
            print("\n--- 测试2: 创建重复任务（每天） ---")
            tomorrow_10am = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
            result = await extension._create_schedule(
                mock_env,
                {
                    "title": "每天吃药",
                    "scheduled_time": tomorrow_10am.isoformat(),
                    "description": "每天上午10点吃药",
                    "schedule_type": "reminder",
                    "recurrence_rule": "daily"
                },
                "test_session"
            )
            assert "已创建提醒" in result, f"创建重复任务失败: {result}"
            assert "每天" in result, f"重复规则未显示: {result}"
            schedule_id_2 = int(result.split("任务ID: ")[1])
            print(f"✓ 创建重复任务成功，ID: {schedule_id_2}")

            # 测试3: 创建工作日重复任务
            print("\n--- 测试3: 创建工作日重复任务 ---")
            next_weekday = datetime.now()
            while next_weekday.weekday() >= 5:
                next_weekday += timedelta(days=1)
            next_weekday = next_weekday.replace(hour=8, minute=0, second=0, microsecond=0)
            result = await extension._create_schedule(
                mock_env,
                {
                    "title": "工作日起床",
                    "scheduled_time": next_weekday.isoformat(),
                    "recurrence_rule": "weekdays"
                },
                "test_session"
            )
            assert "工作日" in result, f"工作日规则未显示: {result}"
            schedule_id_3 = int(result.split("任务ID: ")[1])
            print(f"✓ 创建工作日任务成功，ID: {schedule_id_3}")

            # 测试4: 查询任务列表
            print("\n--- 测试4: 查询任务列表 ---")
            result = await extension._list_schedules(
                mock_env,
                {"status": "all", "schedule_type": "all"},
                "test_session"
            )
            assert "测试任务" in result, f"查询结果未包含测试任务: {result}"
            assert "每天吃药" in result, f"查询结果未包含重复任务: {result}"
            assert "工作日起床" in result, f"查询结果未包含工作日任务: {result}"
            print(f"✓ 查询任务列表成功，找到 {result.count('ID:')} 个任务")

            # 测试5: 取消任务
            print("\n--- 测试5: 取消任务 ---")
            result = await extension._cancel_schedule(
                mock_env,
                {"schedule_id": schedule_id_1},
                "test_session"
            )
            assert "已取消" in result, f"取消任务失败: {result}"
            print(f"✓ 取消任务成功")

            # 验证任务状态
            conn = sqlite3.connect(extension.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM schedules WHERE id = ?", (schedule_id_1,))
            status = cursor.fetchone()[0]
            assert status == "cancelled", f"任务状态应为 cancelled，实际为: {status}"
            conn.close()
            print(f"✓ 任务状态已更新为 cancelled")

            # 测试6: 测试重复任务的下一次时间计算
            print("\n--- 测试6: 测试重复任务时间计算 ---")
            base_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)

            # 测试每天
            next_daily = extension._calculate_next_recurrence(base_time, "daily")
            assert next_daily.hour == 10, f"每天任务时间计算错误: {next_daily}"
            assert next_daily.minute == 0, f"每天任务时间计算错误: {next_daily}"
            print(f"✓ 每天重复计算正确: {next_daily}")

            # 测试工作日
            next_weekday = extension._calculate_next_recurrence(base_time, "weekdays")
            assert next_weekday.weekday() < 5, f"工作日任务计算错误: {next_weekday.weekday()}"
            print(f"✓ 工作日重复计算正确: {next_weekday}")

            # 测试7: 测试相对时间解析
            print("\n--- 测试7: 测试相对时间解析 ---")
            now = datetime.now()

            # 测试"30分钟后"
            parsed = extension._parse_relative_time("30分钟后")
            expected = now + timedelta(minutes=30)
            assert abs((parsed - expected).total_seconds()) < 60, f"30分钟后解析错误: {parsed}"
            print(f"✓ '30分钟后' 解析正确: {parsed}")

            # 测试"2小时后"
            parsed = extension._parse_relative_time("2小时后")
            expected = now + timedelta(hours=2)
            assert abs((parsed - expected).total_seconds()) < 60, f"2小时后解析错误: {parsed}"
            print(f"✓ '2小时后' 解析正确: {parsed}")

            # 测试8: 测试格式化重复规则
            print("\n--- 测试8: 测试格式化重复规则 ---")
            assert extension._format_recurrence_rule("daily") == "每天"
            assert extension._format_recurrence_rule("weekly") == "每周"
            assert extension._format_recurrence_rule("weekdays") == "工作日"
            assert extension._format_recurrence_rule("every_3_days") == "每3天"
            print(f"✓ 重复规则格式化正确")

            # 测试9: 测试工具元数据
            print("\n--- 测试9: 测试工具元数据 ---")
            tools = extension.get_tool_metadata(mock_env)
            tool_names = [tool.name for tool in tools]
            expected_tools = ["create_schedule", "list_schedules", "cancel_schedule", "complete_schedule"]
            for expected in expected_tools:
                assert expected in tool_names, f"缺少工具: {expected}"
            print(f"✓ 所有工具元数据正确: {tool_names}")

            print("\n" + "="*60)
            print("✓ 所有测试通过！")
            print("="*60 + "\n")
            return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_recurrence_calculations():
    """专门测试重复任务的时间计算"""

    print("\n" + "="*60)
    print("测试重复任务时间计算")
    print("="*60 + "\n")

    try:
        from extension import ScheduleToolExtension

        extension = ScheduleToolExtension("test_recurrence")
        now = datetime.now()

        # 测试场景1: 每天 - 今天的时间还没到
        print("--- 测试场景1: 每天 - 今天的时间还没到 ---")
        base_time = now.replace(hour=15, minute=30, second=0, microsecond=0)
        if base_time > now:
            next_time = extension._calculate_next_recurrence(base_time, "daily")
            assert next_time.date() == now.date(), f"应该返回今天: {next_time}"
            assert next_time.hour == 15 and next_time.minute == 30, f"时间应该保持: {next_time}"
            print(f"✓ 今天时间未到，返回今天: {next_time}")

        # 测试场景2: 每天 - 今天的时间已过
        print("--- 测试场景2: 每天 - 今天的时间已过 ---")
        base_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if base_time < now:
            next_time = extension._calculate_next_recurrence(base_time, "daily")
            assert next_time.date() > now.date(), f"应该返回明天: {next_time}"
            assert next_time.hour == 8 and next_time.minute == 0, f"时间应该保持: {next_time}"
            print(f"✓ 今天时间已过，返回明天: {next_time}")

        # 测试场景3: 每周
        print("--- 测试场景3: 每周 ---")
        base_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
        next_time = extension._calculate_next_recurrence(base_time, "weekly")
        assert next_time.weekday() == base_time.weekday(), f"应该保持相同的星期几: {next_time}"
        assert next_time.hour == 9 and next_time.minute == 0, f"时间应该保持: {next_time}"
        print(f"✓ 每周计算正确: {next_time} (星期{next_time.weekday()})")

        # 测试场景4: 工作日
        print("--- 测试场景4: 工作日 ---")
        base_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
        next_time = extension._calculate_next_recurrence(base_time, "weekdays")
        assert next_time.weekday() < 5, f"应该是工作日: {next_time.weekday()}"
        print(f"✓ 工作日计算正确: {next_time} (星期{next_time.weekday()})")

        # 测试场景5: 每N天
        print("--- 测试场景5: 每3天 ---")
        base_time = now.replace(hour=10, minute=0, second=0, microsecond=0)
        next_time = extension._calculate_next_recurrence(base_time, "every_3_days")
        expected = base_time + timedelta(days=3)
        assert abs((next_time - expected).total_seconds()) < 60, f"每3天计算错误: {next_time}"
        print(f"✓ 每3天计算正确: {next_time}")

        print("\n" + "="*60)
        print("✓ 所有重复任务计算测试通过！")
        print("="*60 + "\n")
        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success1 = asyncio.run(test_schedule_tool())
    success2 = asyncio.run(test_recurrence_calculations())
    sys.exit(0 if (success1 and success2) else 1)
