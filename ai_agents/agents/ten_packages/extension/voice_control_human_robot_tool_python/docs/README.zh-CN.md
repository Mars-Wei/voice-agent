# 语音控制人形机器人工具

通过HTTP API控制人形机器人（动作和TTS语音）的TEN Framework扩展。

## 功能

- 动作控制：控制机器人执行预定义动作（握手、挥手、走路等）
- TTS语音：让机器人说话，通过TTS系统播放
- 支持超时和错误处理

## 工具

### control_robot_action

控制机器人执行预定义动作。

**参数：**
- `action_name` (string, 必需): 动作名称，如 "双手居中"、"握手"、"挥手"、"走路"、"停止走路"

**支持的动作：**
- 手臂动作：双手居中、握手、挥手、手臂伸展、手臂摆动
- 身体动作：下蹲、起立、左倾斜、右倾斜
- 行走动作：走路、停止走路、左转、右转

### robot_speak

让机器人说话（TTS语音合成）。

**参数：**
- `text` (string, 必需): 要播放的文本

## 配置

请参考 [property.json] 中的配置项：

- `server_url`: 机器人服务器URL，默认 `http://60.205.136.51:6003`
- `timeout`: 超时时间（秒），默认30秒

可通过环境变量 `ROBOT_SERVER_URL` 覆盖服务器URL。

## 开发

### 构建

```bash
pip install -r requirements.txt
```

### 单元测试

```bash
pytest tests/
```
