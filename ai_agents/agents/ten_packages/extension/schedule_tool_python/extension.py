#
# This file is part of TEN Framework, an open source project.
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file for more information.
#
import os
import asyncio
import json
import sqlite3
import re
from datetime import datetime, timedelta
from typing import Optional

try:
    from dateutil import parser
except ImportError:
    parser = None

try:
    from ten_ai_base.types import (
        LLMToolMetadata,
        LLMToolMetadataParameter,
        LLMToolResultLLMResult,
    )
except Exception as e:
    import traceback
    traceback.print_exc()
    raise

try:
    from ten_ai_base.llm_tool import AsyncLLMToolBaseExtension
except Exception as e:
    import traceback
    traceback.print_exc()
    raise

try:
    from ten_runtime import (
        AsyncTenEnv,
        Cmd,
        Data,
    )
except Exception as e:
    import traceback
    traceback.print_exc()
    raise


class ScheduleToolExtension(AsyncLLMToolBaseExtension):
    """
    定时任务和日程管理工具
    功能：创建、查询、取消、完成定时任务和日程提醒
    """
    def __init__(self, name: str = "schedule_tool_python"):
        super().__init__(name)
        self.db_path: Optional[str] = None
        self.check_task: Optional[asyncio.Task] = None
        self.ten_env: Optional[AsyncTenEnv] = None
        self.session_id: str = "default"

    async def on_init(self, ten_env: AsyncTenEnv) -> None:
        await super().on_init(ten_env)
        self.ten_env = ten_env

    async def on_start(self, ten_env: AsyncTenEnv) -> None:
        await super().on_start(ten_env)

        # 初始化数据库
        db_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(db_dir, exist_ok=True)
        self.db_path = os.path.join(db_dir, "schedules.db")
        self._init_database()

        # 启动后台检测任务
        self.check_task = asyncio.create_task(self._background_checker())

        ten_env.log_info("[ScheduleTool] Extension started")

    async def on_stop(self, ten_env: AsyncTenEnv) -> None:
        if self.check_task:
            self.check_task.cancel()
            try:
                await self.check_task
            except asyncio.CancelledError:
                pass
        await super().on_stop(ten_env)

    def _init_database(self):
        """初始化SQLite数据库"""
        conn = sqlite3.connect(self.db_path)
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
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_scheduled_time
            ON schedules(scheduled_time, status)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_next_scheduled_time
            ON schedules(next_scheduled_time, status)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_session_status
            ON schedules(session_id, status)
        ''')

        # 迁移旧数据：如果表没有 recurrence_rule 字段，添加它
        try:
            cursor.execute('ALTER TABLE schedules ADD COLUMN recurrence_rule TEXT')
        except sqlite3.OperationalError:
            pass  # 字段已存在

        try:
            cursor.execute('ALTER TABLE schedules ADD COLUMN next_scheduled_time TEXT')
        except sqlite3.OperationalError:
            pass  # 字段已存在

        # 迁移旧数据：如果表没有 user_id 字段，添加它（默认使用 session_id 作为 user_id）
        try:
            cursor.execute('ALTER TABLE schedules ADD COLUMN user_id TEXT')
            cursor.execute('UPDATE schedules SET user_id = session_id WHERE user_id IS NULL')
            conn.commit()  # 提交更改，确保字段已添加
        except sqlite3.OperationalError:
            pass  # 字段已存在

        # 在 user_id 字段添加后创建索引
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_status
                ON schedules(user_id, status)
            ''')
        except sqlite3.OperationalError:
            pass  # 如果字段不存在，跳过索引创建

        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_session
                ON schedules(user_id, session_id)
            ''')
        except sqlite3.OperationalError:
            pass  # 如果字段不存在，跳过索引创建

        conn.commit()
        conn.close()

    def get_tool_metadata(self, ten_env: AsyncTenEnv) -> list[LLMToolMetadata]:
        """定义工具元数据"""
        return [
            LLMToolMetadata(
                name="create_schedule",
                description="创建定时任务或日程提醒。当用户提到'提醒我'、'设置闹钟'、'安排日程'、'X分钟后提醒'等时使用。可以设置未来的某个时间点进行提醒。支持重复任务，如'每天'、'每周'、'工作日'等。",
                parameters=[
                    LLMToolMetadataParameter(
                        name="title",
                        type="string",
                        description="任务或日程的标题",
                        required=True
                    ),
                    LLMToolMetadataParameter(
                        name="scheduled_time",
                        type="string",
                        description="提醒时间，ISO格式 (例如: 2024-01-15T14:30:00) 或相对时间 (例如: '30分钟后', '明天上午9点', '2小时后')",
                        required=True
                    ),
                    LLMToolMetadataParameter(
                        name="description",
                        type="string",
                        description="任务或日程的详细描述",
                        required=False
                    ),
                    LLMToolMetadataParameter(
                        name="schedule_type",
                        type="string",
                        description="类型：'reminder' (提醒) 或 'task' (任务)，默认为 'reminder'",
                        required=False
                    ),
                    LLMToolMetadataParameter(
                        name="recurrence_rule",
                        type="string",
                        description="重复规则，支持：'daily' (每天), 'weekly' (每周), 'monthly' (每月), 'weekdays' (工作日), 'weekends' (周末), 'every_N_days' (每N天，如 'every_3_days'), 'every_N_weeks' (每N周), 'every_N_months' (每N月)。留空表示不重复。",
                        required=False
                    ),
                    LLMToolMetadataParameter(
                        name="user_id",
                        type="string",
                        description="用户ID，用于区分不同用户，必需",
                        required=True
                    ),
                    LLMToolMetadataParameter(
                        name="session_id",
                        type="string",
                        description="会话ID，用于标识会话，通常可以自动获取",
                        required=False
                    )
                ]
            ),
            LLMToolMetadata(
                name="list_schedules",
                description="查询用户的定时任务和日程列表。当用户问'我的日程'、'有什么提醒'、'待办事项'时使用。可以按状态、类型筛选。",
                parameters=[
                    LLMToolMetadataParameter(
                        name="status",
                        type="string",
                        description="筛选状态：'pending' (待处理), 'completed' (已完成), 'cancelled' (已取消) 或 'all' (全部)",
                        required=False
                    ),
                    LLMToolMetadataParameter(
                        name="schedule_type",
                        type="string",
                        description="筛选类型：'reminder' (提醒), 'task' (任务) 或 'all' (全部)",
                        required=False
                    ),
                    LLMToolMetadataParameter(
                        name="user_id",
                        type="string",
                        description="用户ID，用于区分不同用户，必需",
                        required=True
                    ),
                    LLMToolMetadataParameter(
                        name="session_id",
                        type="string",
                        description="会话ID",
                        required=False
                    )
                ]
            ),
            LLMToolMetadata(
                name="cancel_schedule",
                description="取消或删除一个定时任务或日程。当用户说'取消提醒'、'删除任务'时使用。",
                parameters=[
                    LLMToolMetadataParameter(
                        name="schedule_id",
                        type="integer",
                        description="要取消的任务ID",
                        required=True
                    ),
                    LLMToolMetadataParameter(
                        name="user_id",
                        type="string",
                        description="用户ID，用于区分不同用户，必需",
                        required=True
                    ),
                    LLMToolMetadataParameter(
                        name="session_id",
                        type="string",
                        description="会话ID",
                        required=False
                    )
                ]
            ),
            LLMToolMetadata(
                name="complete_schedule",
                description="标记一个任务为已完成。当用户说'完成任务'、'标记完成'时使用。",
                parameters=[
                    LLMToolMetadataParameter(
                        name="schedule_id",
                        type="integer",
                        description="要完成的任务ID",
                        required=True
                    ),
                    LLMToolMetadataParameter(
                        name="user_id",
                        type="string",
                        description="用户ID，用于区分不同用户，必需",
                        required=True
                    ),
                    LLMToolMetadataParameter(
                        name="session_id",
                        type="string",
                        description="会话ID",
                        required=False
                    )
                ]
            )
        ]

    async def run_tool(self, ten_env: AsyncTenEnv, name: str, args: dict):
        """执行工具调用"""
        try:
            user_id = args.get("user_id")
            if not user_id:
                return "错误：缺少必需的参数 user_id"

            session_id = args.get("session_id", self.session_id)

            if name == "create_schedule":
                result = await self._create_schedule(ten_env, args, user_id, session_id)
            elif name == "list_schedules":
                result = await self._list_schedules(ten_env, args, user_id, session_id)
            elif name == "cancel_schedule":
                result = await self._cancel_schedule(ten_env, args, user_id, session_id)
            elif name == "complete_schedule":
                result = await self._complete_schedule(ten_env, args, user_id, session_id)
            else:
                result = f"未知工具: {name}"

            return LLMToolResultLLMResult(type="llmresult", content=result)
        except Exception as e:
            ten_env.log_error(f"[ScheduleTool] Tool execution failed: {e}")
            import traceback
            ten_env.log_error(traceback.format_exc())
            return LLMToolResultLLMResult(
                type="llmresult",
                content=f"操作失败: {str(e)}"
            )

    async def _create_schedule(self, ten_env: AsyncTenEnv, args: dict, user_id: str, session_id: str) -> str:
        """创建定时任务"""
        title = args["title"]
        scheduled_time_str = args["scheduled_time"]
        description = args.get("description", "")
        schedule_type = args.get("schedule_type", "reminder")
        recurrence_rule = args.get("recurrence_rule", "")

        # 解析时间
        try:
            if parser:
                scheduled_time = parser.parse(scheduled_time_str)
            else:
                # 如果没有dateutil，尝试简单的ISO格式解析
                scheduled_time = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
        except:
            scheduled_time = self._parse_relative_time(scheduled_time_str)

        if scheduled_time <= datetime.now() and not recurrence_rule:
            return f"错误：提醒时间不能是过去的时间。当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        # 如果时间已过但有重复规则，计算下一个执行时间
        if scheduled_time <= datetime.now() and recurrence_rule:
            scheduled_time = self._calculate_next_recurrence(scheduled_time, recurrence_rule)

        # 计算下一个执行时间（用于重复任务）
        next_scheduled_time = None
        if recurrence_rule:
            next_scheduled_time = self._calculate_next_recurrence(scheduled_time, recurrence_rule)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO schedules
            (user_id, session_id, title, description, schedule_type, scheduled_time, created_at, status, recurrence_rule, next_scheduled_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            session_id,
            title,
            description,
            schedule_type,
            scheduled_time.isoformat(),
            datetime.now().isoformat(),
            "pending",
            recurrence_rule if recurrence_rule else None,
            next_scheduled_time.isoformat() if next_scheduled_time else None
        ))
        schedule_id = cursor.lastrowid
        conn.commit()
        conn.close()

        ten_env.log_info(f"[ScheduleTool] Created schedule: {schedule_id} - {title} at {scheduled_time}, recurrence: {recurrence_rule}")

        recurrence_text = ""
        if recurrence_rule:
            recurrence_text = f"，重复规则：{self._format_recurrence_rule(recurrence_rule)}"

        return f"已创建{'任务' if schedule_type == 'task' else '提醒'}：{title}，将在 {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')} 提醒您{recurrence_text}。任务ID: {schedule_id}"

    def _parse_relative_time(self, time_str: str) -> datetime:
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

    def _calculate_next_recurrence(self, base_time: datetime, recurrence_rule: str) -> datetime:
        """计算下一个重复执行时间"""
        rule = recurrence_rule.lower().strip()
        now = datetime.now()

        if rule == "daily" or rule == "每天":
            # 每天同一时间
            # 计算今天的同一时间
            today_at_time = now.replace(
                hour=base_time.hour,
                minute=base_time.minute,
                second=0,
                microsecond=0
            )

            # 如果今天的时间还没到，返回今天
            if today_at_time > now:
                return today_at_time
            # 否则返回明天
            return today_at_time + timedelta(days=1)

        elif rule == "weekly" or rule == "每周":
            # 每周同一时间（保持星期几和时分秒）
            next_time = now.replace(
                hour=base_time.hour,
                minute=base_time.minute,
                second=0,
                microsecond=0
            )
            # 计算到下一个相同星期几的天数
            days_ahead = base_time.weekday() - next_time.weekday()
            if days_ahead <= 0:  # 如果这周已经过了，计算下周
                days_ahead += 7
            return next_time + timedelta(days=days_ahead)

        elif rule == "monthly" or rule == "每月":
            # 每月同一时间（保持日期和时分秒）
            next_time = now.replace(
                hour=base_time.hour,
                minute=base_time.minute,
                second=0,
                microsecond=0
            )
            # 尝试设置为下个月的同一日期
            if next_time.month == 12:
                next_time = next_time.replace(year=next_time.year + 1, month=1, day=base_time.day)
            else:
                try:
                    next_time = next_time.replace(month=next_time.month + 1, day=base_time.day)
                except ValueError:
                    # 如果目标月份没有这一天（如2月30日），使用月末
                    if next_time.month == 12:
                        next_time = next_time.replace(year=next_time.year + 1, month=1, day=1) - timedelta(days=1)
                    else:
                        next_time = next_time.replace(month=next_time.month + 1, day=1) - timedelta(days=1)
            # 如果下个月的时间还没到，就使用下个月；否则使用再下个月
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
            # 工作日（周一到周五）
            next_time = base_time + timedelta(days=1)
            # 跳过周末
            while next_time.weekday() >= 5:  # 5=Saturday, 6=Sunday
                next_time += timedelta(days=1)
            return next_time

        elif rule == "weekends" or rule == "周末":
            # 周末（周六和周日）
            next_time = base_time + timedelta(days=1)
            # 找到下一个周末
            while next_time.weekday() < 5:
                next_time += timedelta(days=1)
            return next_time

        elif rule.startswith("every_"):
            # 每N天/周/月
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
                        # 简化处理
                        return base_time + timedelta(days=n * 30)
                except ValueError:
                    pass

        # 默认：每天
        return base_time + timedelta(days=1)

    def _format_recurrence_rule(self, recurrence_rule: str) -> str:
        """格式化重复规则为中文描述"""
        rule = recurrence_rule.lower().strip()
        rule_map = {
            "daily": "每天",
            "weekly": "每周",
            "monthly": "每月",
            "weekdays": "工作日",
            "weekends": "周末",
            "每天": "每天",
            "每周": "每周",
            "每月": "每月",
            "工作日": "工作日",
            "周末": "周末"
        }

        if rule in rule_map:
            return rule_map[rule]

        if rule.startswith("every_"):
            parts = rule.split("_")
            if len(parts) >= 3:
                try:
                    n = int(parts[1])
                    unit = parts[2] if len(parts) > 2 else "days"

                    if unit.startswith("day"):
                        return f"每{n}天"
                    elif unit.startswith("week"):
                        return f"每{n}周"
                    elif unit.startswith("month"):
                        return f"每{n}月"
                except ValueError:
                    pass

        return recurrence_rule

    async def _list_schedules(self, ten_env: AsyncTenEnv, args: dict, user_id: str, session_id: str) -> str:
        """列出任务"""
        status = args.get("status", "pending")
        schedule_type = args.get("schedule_type", "all")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT id, title, description, schedule_type, scheduled_time, status, recurrence_rule, next_scheduled_time FROM schedules WHERE user_id = ?"
        params = [user_id]

        if status != "all":
            query += " AND status = ?"
            params.append(status)

        if schedule_type != "all":
            query += " AND schedule_type = ?"
            params.append(schedule_type)

        query += " ORDER BY scheduled_time ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return "没有找到匹配的任务或日程。"

        result = []
        for row in rows:
            schedule_id, title, desc, s_type, s_time, status, recurrence_rule, next_scheduled_time = row
            try:
                if parser:
                    s_time_obj = parser.parse(s_time)
                else:
                    s_time_obj = datetime.fromisoformat(s_time.replace('Z', '+00:00'))
            except:
                s_time_obj = datetime.now()

            # 如果有重复规则，显示下一个执行时间
            display_time = s_time_obj
            if recurrence_rule and next_scheduled_time:
                try:
                    if parser:
                        display_time = parser.parse(next_scheduled_time)
                    else:
                        display_time = datetime.fromisoformat(next_scheduled_time.replace('Z', '+00:00'))
                except:
                    pass

            type_name = "任务" if s_type == "task" else "提醒"
            status_name = {"pending": "待处理", "completed": "已完成", "cancelled": "已取消"}.get(status, status)

            recurrence_text = ""
            if recurrence_rule:
                recurrence_text = f"\n  重复: {self._format_recurrence_rule(recurrence_rule)}"

            result.append(
                f"ID: {schedule_id}, {type_name}: {title}\n"
                f"  下次时间: {display_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"  状态: {status_name}{recurrence_text}\n"
                f"  描述: {desc or '无'}"
            )

        return "\n\n".join(result)

    async def _cancel_schedule(self, ten_env: AsyncTenEnv, args: dict, user_id: str, session_id: str) -> str:
        """取消任务"""
        schedule_id = args["schedule_id"]

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE schedules
            SET status = 'cancelled'
            WHERE id = ? AND user_id = ?
        ''', (schedule_id, user_id))

        if cursor.rowcount == 0:
            conn.close()
            return f"未找到ID为 {schedule_id} 的任务，或该任务不属于当前用户。"

        conn.commit()
        conn.close()

        return f"已取消任务 ID: {schedule_id}"

    async def _complete_schedule(self, ten_env: AsyncTenEnv, args: dict, user_id: str, session_id: str) -> str:
        """完成任务"""
        schedule_id = args["schedule_id"]

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE schedules
            SET status = 'completed'
            WHERE id = ? AND user_id = ?
        ''', (schedule_id, user_id))

        if cursor.rowcount == 0:
            conn.close()
            return f"未找到ID为 {schedule_id} 的任务。"

        conn.commit()
        conn.close()

        return f"已标记任务 ID: {schedule_id} 为完成"

    async def _background_checker(self):
        """后台任务检测循环"""
        while True:
            try:
                await asyncio.sleep(10)  # 每10秒检查一次
                await self._check_and_trigger_reminders()
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.ten_env:
                    self.ten_env.log_error(f"[ScheduleTool] Background checker error: {e}")

    async def _check_and_trigger_reminders(self):
        """检查并触发提醒"""
        now = datetime.now()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 查找需要提醒的任务
        # 对于非重复任务：检查 scheduled_time
        # 对于重复任务：检查 next_scheduled_time
        cursor.execute('''
            SELECT id, user_id, session_id, title, description, schedule_type, scheduled_time, recurrence_rule, next_scheduled_time
            FROM schedules
            WHERE status = 'pending'
            AND (
                (recurrence_rule IS NULL OR recurrence_rule = '') AND reminder_sent = 0 AND scheduled_time <= ?
                OR
                (recurrence_rule IS NOT NULL AND recurrence_rule != '') AND (next_scheduled_time IS NULL OR next_scheduled_time <= ?)
            )
        ''', (now.isoformat(), now.isoformat()))

        rows = cursor.fetchall()

        for row in rows:
            schedule_id, user_id, session_id, title, desc, s_type, s_time, recurrence_rule, next_scheduled_time = row

            # 发送提醒
            await self._send_reminder(user_id, session_id, schedule_id, title, desc, s_type)

            if recurrence_rule:
                # 重复任务：计算下一个执行时间
                try:
                    if parser:
                        base_time = parser.parse(s_time)
                    else:
                        base_time = datetime.fromisoformat(s_time.replace('Z', '+00:00'))
                except:
                    base_time = datetime.now()

                # 使用原始时间的时分秒，基于当前日期计算下一个时间
                next_time = self._calculate_next_recurrence(base_time, recurrence_rule)

                # 更新下一个执行时间
                cursor.execute('''
                    UPDATE schedules
                    SET next_scheduled_time = ?
                    WHERE id = ?
                ''', (next_time.isoformat(), schedule_id))
            else:
                # 非重复任务：标记为已发送
                cursor.execute('''
                    UPDATE schedules
                    SET reminder_sent = 1
                    WHERE id = ?
                ''', (schedule_id,))

        conn.commit()
        conn.close()

    async def _send_reminder(self, user_id: str, session_id: str, schedule_id: int, title: str, description: str, schedule_type: str):
        """发送提醒通知"""
        if not self.ten_env:
            return

        # 构建提醒消息
        reminder_text = f"提醒：{title}"
        if description:
            reminder_text += f"，{description}"

        # 通过发送数据到 main_control 来触发TTS输出
        await self._notify_user(reminder_text)

        self.ten_env.log_info(
            f"[ScheduleTool] Sent reminder: {schedule_id} - {title} to session {session_id}"
        )

    async def _notify_user(self, text: str):
        """通知用户（通过TTS或消息系统）"""
        from ten_runtime import Data
        data = Data.create("reminder_notification", "main_control")
        data.set_property_from_json(None, json.dumps({
            "text": text,
            "type": "reminder"
        }))
        await self.ten_env.send_data(data)
