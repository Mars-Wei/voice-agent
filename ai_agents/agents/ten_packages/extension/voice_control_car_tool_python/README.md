# Voice Control Car Tool Extension

一个通过 WebSocket 连接 ROS2 系统，发送语音指令控制小车移动的 TEN Framework 扩展。

## 功能特性

- **WebSocket 连接**：通过 WebSocket 连接到 ROS2 小车控制系统
- **语音控制**：发送语音指令控制小车移动（前進、后腿、左转、右转、停止等）
- **工具集成**：作为 LLM 工具，可以被 LLM 主动调用
- **超时处理**：支持配置超时时间

## 配置

### 环境变量

```bash
export CAR_CONTROL_WS_URL="ws://60.205.136.51:8765/robot_control"
```

### property.json 配置

```json
{
  "ws_url": "${env:CAR_CONTROL_WS_URL|ws://60.205.136.51:8765/robot_control}",
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
      "name": "voice_control_car_tool",
      "addon": "voice_control_car_tool_python",
      "extension_group": "default",
      "property": {
        "ws_url": "${env:CAR_CONTROL_WS_URL|ws://60.205.136.51:8765/robot_control}",
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
              "extension": "voice_control_car_tool"
            }
          ]
        }
      ]
    }
  ]
}
```

## 工具说明

### 工具名称
`control_car`

### 工具描述
控制小车移动的语音指令工具。当前用户想要控制小车（前進、后腿、左转、右转、停止等）时使用此工具。命令会通过 WebSocket 发送到 ROS2 系统。示例指令："向前移动3秒"、"向后移动2秒"、"左转"、"右转"、"停止"。

### 参数
- `command` (string, required): 语音指令，例如 "向前移动3秒"、"向后移动2秒"、"左转"、"右转"、"停止"

### 返回格式

```json
{
  "command": "向前移动3秒",
  "status": "success",
  "response": "..."
}
```

## 工作原理

1. **WebSocket 连接**：使用 `websockets` 库连接到配置的 WebSocket 服务器
2. **发送命令**：将语音命令以 JSON 格式发送到服务器
   ```json
   {
     "type": "command",
     "text": "向前移动3秒"
   }
   ```
3. **等待响应**：等待服务器响应，支持超时配置
4. **返回结果**：将执行结果返回给 LLM

## 示例

当用户说："小车向前移动3秒"

LLM 可以调用 `control_car` 工具：
```json
{
  "command": "向前移动3秒"
}
```

工具会发送指令到 ROS2 系统控制小车移动，并返回执行结果。

## 依赖

- `websockets>=12.0`: WebSocket 客户端库
- `ten_runtime_python`: TEN Framework Python 运行时
- `ten_ai_base`: TEN Framework AI 基础库

## 注意事项

- 需要确保 ROS2 小车控制服务器已启动并可访问
- 默认 WebSocket 服务器地址为 `ws://60.205.136.51:8765/robot_control`
- 可通过环境变量 `CAR_CONTROL_WS_URL` 自定义服务器地址
