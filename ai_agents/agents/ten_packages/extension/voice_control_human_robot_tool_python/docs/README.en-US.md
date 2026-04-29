# Voice Control Human Robot Tool

A TEN Framework extension for controlling a humanoid robot via HTTP API - action control and TTS.

## Features

- Action control: Control robot to perform predefined actions (handshake, wave, walk, etc.)
- TTS voice: Make the robot speak through TTS system
- Support timeout and error handling

## Tools

### control_robot_action

Control robot to perform predefined actions.

**Parameters:**
- `action_name` (string, required): Action name, e.g., "双手居中", "握手", "挥手", "走路"

**Supported actions:**
- Arm actions: 双手居中, 握手, 挥手, 手臂伸展, 手臂摆动
- Body actions: 下蹲, 起立, 左倾斜, 右倾斜
- Walk actions: 走路, 停止走路, 左转, 右转

### robot_speak

Make the robot speak (TTS).

**Parameters:**
- `text` (string, required): Text to speak

## Configuration

Refer to [property.json] for configuration:

- `server_url`: Robot server URL, default `http://60.205.136.51:6003`
- `timeout`: Timeout in seconds, default 30

You can override the server URL via environment variable `ROBOT_SERVER_URL`.

## Development

### Build

```bash
pip install -r requirements.txt
```

### Unit Test

```bash
pytest tests/
```
