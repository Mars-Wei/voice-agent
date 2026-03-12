# Voice Control Car Tool

A TEN Framework extension for controlling a car via voice commands through WebSocket connection to ROS2.

## Features

- Connect to ROS2 car control system via WebSocket
- Send voice commands to control car movement (forward, backward, turn left, turn right, stop, etc.)
- Support timeout and error handling

## Tools

### control_car

A tool to control the car using voice commands.

**Parameters:**
- `command` (string, required): Voice command, e.g., "forward 3 seconds", "backward 2 seconds", "turn left", "turn right", "stop"

## Configuration

Refer to [property.json] for configuration:

- `ws_url`: WebSocket server URL, default `ws://60.205.136.51:8765/robot_control`
- `timeout`: Timeout in seconds, default 30

You can override the WebSocket URL via environment variable `CAR_CONTROL_WS_URL`.

## Development

### Build

```bash
pip install -r requirements.txt
```

### Unit Test

```bash
pytest tests/
```
