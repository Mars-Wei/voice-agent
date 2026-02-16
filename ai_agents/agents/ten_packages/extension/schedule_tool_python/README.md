# Schedule Tool Python Extension

定时任务和日程管理工具扩展，用于创建、查询、取消和完成定时任务和日程提醒。

## 功能特性

- **创建定时任务/日程**：支持相对时间（如"30分钟后"、"明天上午9点"）和绝对时间（ISO格式）
- **重复任务支持**：支持每天、每周、每月、工作日、周末等重复模式
- **查询任务列表**：按状态、类型筛选任务
- **取消任务**：取消已创建的定时任务
- **完成任务**：标记任务为已完成
- **自动提醒**：后台服务每10秒检测一次，到达提醒时间时自动通过TTS提醒用户
- **重复任务自动调度**：重复任务执行后自动计算并更新下一个执行时间

## 工具列表

### 1. create_schedule
创建定时任务或日程提醒。

**使用场景**：
- 用户说："提醒我30分钟后开会"
- 用户说："设置明天上午9点的闹钟"
- 用户说："安排一个任务，2小时后提醒我"

**参数**：
- `title` (必需): 任务或日程的标题
- `scheduled_time` (必需): 提醒时间，支持ISO格式或相对时间
- `description` (可选): 详细描述
- `schedule_type` (可选): 'reminder' 或 'task'，默认为 'reminder'
- `recurrence_rule` (可选): 重复规则，支持以下格式：
  - `"daily"` 或 `"每天"` - 每天同一时间
  - `"weekly"` 或 `"每周"` - 每周同一时间
  - `"monthly"` 或 `"每月"` - 每月同一时间
  - `"weekdays"` 或 `"工作日"` - 工作日（周一到周五）
  - `"weekends"` 或 `"周末"` - 周末（周六和周日）
  - `"every_N_days"` - 每N天（如 `"every_3_days"` 表示每3天）
  - `"every_N_weeks"` - 每N周（如 `"every_2_weeks"` 表示每2周）
  - `"every_N_months"` - 每N月（如 `"every_1_months"` 表示每月）
- `session_id` (可选): 会话ID

**重复任务示例**：
- 用户说："每天上午10点提醒我吃药" → `create_schedule(title="吃药", scheduled_time="10:00", recurrence_rule="daily")`
- 用户说："每周一提醒我开会" → `create_schedule(title="开会", scheduled_time="下周一9:00", recurrence_rule="weekly")`
- 用户说："工作日早上8点提醒我起床" → `create_schedule(title="起床", scheduled_time="8:00", recurrence_rule="weekdays")`

### 2. list_schedules
查询用户的定时任务和日程列表。

**使用场景**：
- 用户问："我的日程有哪些？"
- 用户问："有什么待办事项？"

**参数**：
- `status` (可选): 'pending', 'completed', 'cancelled' 或 'all'
- `schedule_type` (可选): 'reminder', 'task' 或 'all'
- `session_id` (可选): 会话ID

### 3. cancel_schedule
取消或删除一个定时任务或日程。

**使用场景**：
- 用户说："取消ID为1的任务"
- 用户说："删除那个提醒"

**参数**：
- `schedule_id` (必需): 要取消的任务ID
- `session_id` (可选): 会话ID

### 4. complete_schedule
标记一个任务为已完成。

**使用场景**：
- 用户说："完成任务ID 1"
- 用户说："标记完成"

**参数**：
- `schedule_id` (必需): 要完成的任务ID
- `session_id` (可选): 会话ID

## 时间格式支持

### 相对时间
- "30分钟后"
- "2小时后"
- "明天上午9点"
- "3天后"

### 绝对时间（ISO格式）
- "2024-01-15T14:30:00"
- "2024-01-15T09:00:00+08:00"

## 数据存储

数据存储在 SQLite 数据库中，位置：`extension/data/schedules.db`

## 提醒机制

后台服务每10秒检查一次待提醒的任务。当任务到达提醒时间时：
1. 自动发送提醒通知到 `main_control` 扩展
2. `main_control` 通过 TTS 播放提醒内容
3. 对于非重复任务：标记任务为已发送提醒
4. 对于重复任务：自动计算下一个执行时间并更新，继续循环提醒

## 重复任务说明

- **重复任务不会自动完成**：重复任务会一直保持 `pending` 状态，每次到达时间都会提醒
- **下一个执行时间**：系统会自动计算并更新 `next_scheduled_time` 字段
- **取消重复任务**：使用 `cancel_schedule` 可以取消重复任务
- **时间计算**：
  - 每天：基于原始时间的时分秒，每天重复
  - 每周：基于原始时间，每周同一天重复
  - 每月：基于原始时间的日期，每月重复（如果目标月份没有该日期，使用月末）
  - 工作日：自动跳过周末
  - 周末：自动跳过工作日

## 配置

在 `property.json` 中添加：

```json
{
  "type": "extension",
  "name": "schedule_tool_python",
  "addon": "schedule_tool_python",
  "extension_group": "default",
  "property": {}
}
```

## 依赖

- `python-dateutil>=2.8.0` - 用于时间解析

## 注意事项

- 提醒时间不能是过去的时间
- 每个会话的任务是独立的（通过 session_id 区分）
- 提醒通知会通过 TTS 播放，确保用户能听到
