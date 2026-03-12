# 语音控制小车工具

通过WebSocket连接ROS2系统，发送语音指令控制小车移动的TEN Framework扩展。

## 功能

- 通过WebSocket连接到ROS2小车控制系统
- 发送语音指令控制小车移动（前进、后退、左转、右转、停止等）
- 支持超时和错误处理

## 工具

### control_car

控制小车移动的语音指令工具。

**参数：**
- `command` (string, 必需): 语音指令，例如 "向前移动3秒"、"向后移动2秒"、"左转"、"右转"、"停止"

## 配置

请参考 [property.json] 中的配置项：

- `ws_url`: WebSocket服务器URL，默认 `ws://60.205.136.51:8765/robot_control`
- `timeout`: 超时时间（秒），默认30秒

可通过环境变量 `CAR_CONTROL_WS_URL` 覆盖WebSocket URL。

## 开发

### 构建

```bash
pip install -r requirements.txt
```

### 单元测试

```bash
pytest tests/
```
