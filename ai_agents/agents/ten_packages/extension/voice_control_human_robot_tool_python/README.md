# Voice Control Human Robot Tool Extension

一个通过 HTTP API 控制人形机器人（动作和 TTS 语音）的 TEN Framework 扩展。

## 功能特性

- **动作控制**：控制机器人执行预定义动作（握手、挥手、走路等）
- **TTS 语音**：让机器人说话，通过 TTS 系统播放
- **工具集成**：作为 LLM 工具，可以被 LLM 主动调用
- **超时处理**：支持配置超时时间

## 配置

### 环境变量

```bash
export ROBOT_SERVER_URL="http://60.205.136.51:6003"
```

### property.json 配置

```json
{
  "server_url": "${env:ROBOT_SERVER_URL|http://60.205.136.51:6003}",
  "timeout": 30
}
```

## 使用方法

### 1. 在 property.json 中添加节点

```json
{
  "nodes": [
    {
      "type": "extension",
      "name": "voice_control_human_robot_tool",
      "addon": "voice_control_human_robot_tool_python",
      "extension_group": "default",
      "property": {
        "server_url": "${env:ROBOT_SERVER_URL|http://60.205.136.51:6003}",
        "timeout": 30
      }
    }
  ]
}
```

### 2. 连接工具到 main_control

```json
{
  "connections": [
    {
      "extension": "main_control",
      "cmd": [
        {
          "names": ["tool_register"],
          "source": [
            {
              "extension": "voice_control_human_robot_tool"
            }
          ]
        }
      ]
    }
  ]
}
```

## 工具说明

### 工具 1: control_robot_action

控制机器人执行预定义动作。

**参数：**
- `action_name` (string, required): 动作名称，如 "双手居中"、"握手"、"挥手"、"手臂伸展"、"走路"、"停止走路"、"左转"、"右转"

**支持的动作：**
- 手臂动作：双手居中、握手、挥手、手臂伸展、手臂摆动、双手打开、双手闭合
- 身体动作：下蹲、起立、左倾斜、右倾斜、向前倾斜、向后倾斜
- 行走动作：走路、停止走路、左转、右转

**返回格式：**
```json
{
  "action_name": "握手",
  "status": "success",
  "response": "..."
}
```

### 工具 2: robot_speak

让机器人说话（TTS 语音合成）。

**参数：**
- `text` (string, required): 要播放的文本，如 "你好啊，欢迎参观"

**返回格式：**
```json
{
  "text": "你好啊，欢迎参观",
  "status": "success",
  "response": "..."
}
```

## 工作原理

1. **动作控制**：通过 HTTP POST 请求发送到 `{server_url}/kuavo/action`
   ```json
   {
     "action_name": "握手"
   }
   ```
2. **TTS 语音**：通过 HTTP POST 请求发送到 `{server_url}/kuavo/tts`
   ```json
   {
     "text": "你好啊，欢迎参观"
   }
   ```
3. **返回结果**：将执行结果返回给 LLM

## 示例

当用户说："机器人做一个握手的动作"

LLM 可以调用 `control_robot_action` 工具：
```json
{
  "action_name": "握手"
}
```

当用户说："请机器人说'欢迎参观'"

LLM 可以调用 `robot_speak` 工具：
```json
{
  "text": "欢迎参观"
}
```

## 依赖

- `aiohttp>=3.9.0`: 异步 HTTP 客户端库
- `ten_runtime_python`: TEN Framework Python 运行时
- `ten_ai_base`: TEN Framework AI 基础库

## 注意事项

- 需要确保机器人控制服务器已启动并可访问
- 默认服务器地址为 `http://60.205.136.51:6003`
- 可通过环境变量 `ROBOT_SERVER_URL` 自定义服务器地址
