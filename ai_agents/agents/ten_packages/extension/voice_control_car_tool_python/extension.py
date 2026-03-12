
import json
import asyncio
from typing import Any, Optional
from dataclasses import dataclass
import traceback

import websockets

from ten_runtime import Cmd
from ten_runtime.async_ten_env import AsyncTenEnv
from ten_ai_base.config import BaseConfig
from ten_ai_base.types import (
    LLMToolMetadata,
    LLMToolMetadataParameter,
    LLMToolResult,
    LLMToolResultLLMResult,
)
from ten_ai_base.llm_tool import AsyncLLMToolBaseExtension

TOOL_NAME = "control_car"
TOOL_DESCRIPTION = (
    "Control a car to move using voice commands. Use this tool when the user wants "
    "to control the car (forward, backward, turn left, turn right, stop, etc.). "
    "The command will be sent to the ROS2-based car control system via WebSocket. "
    "Example commands: '向前移动3秒', '向后移动2秒', '左转', '右转', '停止'."
)

PROPERTY_WS_URL = "ws_url"
PROPERTY_TIMEOUT = "timeout"


@dataclass
class VoiceControlCarToolConfig(BaseConfig):
    ws_url: str = "ws://60.205.136.51:8765/robot_control"
    timeout: int = 30


class VoiceControlCarToolExtension(AsyncLLMToolBaseExtension):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.ten_env = None
        self.config: Optional[VoiceControlCarToolConfig] = None

    async def on_init(self, ten_env: AsyncTenEnv) -> None:
        ten_env.log_debug("[VoiceControlCarTool] on_init")

    async def on_start(self, ten_env: AsyncTenEnv) -> None:
        ten_env.log_debug("[VoiceControlCarTool] on_start")

        self.config = await VoiceControlCarToolConfig.create_async(ten_env=ten_env)
        ten_env.log_info(f"[VoiceControlCarTool] config: {self.config}")

        await super().on_start(ten_env)
        self.ten_env = ten_env

    async def on_stop(self, ten_env: AsyncTenEnv) -> None:
        ten_env.log_debug("[VoiceControlCarTool] on_stop")

    async def on_deinit(self, ten_env: AsyncTenEnv) -> None:
        ten_env.log_debug("[VoiceControlCarTool] on_deinit")

    async def on_cmd(self, ten_env: AsyncTenEnv, cmd: Cmd) -> None:
        cmd_name = cmd.get_name()
        ten_env.log_debug(f"[VoiceControlCarTool] on_cmd name: {cmd_name}")

        await super().on_cmd(ten_env, cmd)

    def get_tool_metadata(self, ten_env: AsyncTenEnv) -> list[LLMToolMetadata]:
        return [
            LLMToolMetadata(
                name=TOOL_NAME,
                description=TOOL_DESCRIPTION,
                parameters=[
                    LLMToolMetadataParameter(
                        name="command",
                        type="string",
                        description="The voice command to control the car, e.g., '向前移动3秒', '向后移动2秒', '左转', '右转', '停止'",
                        required=True,
                    ),
                ],
            ),
        ]

    async def run_tool(
        self, ten_env: AsyncTenEnv, name: str, args: dict
    ) -> LLMToolResult | None:
        ten_env.log_info(f"[VoiceControlCarTool] run_tool name: {name}, args: {args}")

        if name == TOOL_NAME:
            result = await self._control_car(args)
            return LLMToolResultLLMResult(
                type="llmresult",
                content=json.dumps(result, ensure_ascii=False),
            )

        return None

    async def _control_car(self, args: dict) -> Any:
        if "command" not in args:
            raise ValueError("Missing required parameter: command")

        command = args["command"]
        ws_url = self.config.ws_url
        timeout = self.config.timeout

        try:
            self.ten_env.log_info(
                f"[VoiceControlCarTool] Sending command to car: {command}"
            )

            async with websockets.connect(ws_url) as websocket:
                # Send command
                await websocket.send(json.dumps({
                    "type": "command",
                    "text": command
                }))

                # Wait for response
                response = await asyncio.wait_for(
                    websocket.recv(),
                    timeout=timeout
                )

                self.ten_env.log_info(
                    f"[VoiceControlCarTool] Received response: {response}"
                )

                return {
                    "command": command,
                    "status": "success",
                    "response": response,
                }

        except asyncio.TimeoutError:
            self.ten_env.log_error(
                f"[VoiceControlCarTool] Timeout waiting for response from car control server"
            )
            return {
                "command": command,
                "status": "error",
                "error": "Timeout waiting for response from car control server",
            }

        except websockets.exceptions.ConnectionRefusedError:
            self.ten_env.log_error(
                f"[VoiceControlCarTool] Connection refused - car control server may not be running"
            )
            return {
                "command": command,
                "status": "error",
                "error": "Connection refused - car control server may not be running",
            }

        except Exception as e:
            self.ten_env.log_error(f"[VoiceControlCarTool] Failed to control car: {e}")
            self.ten_env.log_error(traceback.format_exc())
            return {
                "command": command,
                "status": "error",
                "error": str(e),
            }
