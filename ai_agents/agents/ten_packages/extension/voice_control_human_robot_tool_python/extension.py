
import json
from typing import Any, Optional
from dataclasses import dataclass
import traceback

import aiohttp

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

TOOL_NAME_ACTION = "control_robot_action"
TOOL_DESCRIPTION_ACTION = (
    "Control a humanoid robot to perform predefined actions. Use this tool when the user wants "
    "the robot to perform specific actions like greeting, waving, nodding, raising arms, etc. "
    "Supported actions: '双手居中', '握手', '挥手', '走路', '停止走路'."
)

TOOL_NAME_SPEAK = "robot_speak"
TOOL_DESCRIPTION_SPEAK = (
    "Make the humanoid robot speak text via TTS. Use this tool when the user wants "
    "the robot to say something. The text will be sent to the robot's TTS system and played through its speakers. "
    "Example: '你好啊，欢迎参观', '我正在为您服务', '再见'."
)

TOOL_NAME_GREET = "robot_greet"
TOOL_DESCRIPTION_GREET = (
    "Make the humanoid robot perform a greeting action with speech. Use this tool when the user says "
    "something like 'let the robot say hello', 'let the robot greet', '让机器人打个招呼', etc. "
    "This will execute the greeting action combined with appropriate greeting speech. "
    "Example phrases: '让机器人打个招呼', '机器人问好', '机器人欢迎'."
)

TOOL_NAME_NAVIGATE = "robot_navigate"
TOOL_DESCRIPTION_NAVIGATE = (
    "Make the humanoid robot navigate to a specific location. Use this tool when the user says "
    "something like 'let the robot come here', 'let the robot go to the door', '让机器人到门口来', "
    "'让机器人回去吧', '让机器人回去', '让机器人过来', etc. "
    "The robot will navigate to the specified destination. "
    "Example phrases: '让机器人到门口来', '让机器人回去吧', '让机器人过来', '让机器人回去'."
)

PROPERTY_SERVER_URL = "server_url"
PROPERTY_TIMEOUT = "timeout"


@dataclass
class VoiceControlHumanRobotToolConfig(BaseConfig):
    server_url: str = "http://182.92.132.168:6003"
    timeout: int = 30


class VoiceControlHumanRobotToolExtension(AsyncLLMToolBaseExtension):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.ten_env = None
        self.config: Optional[VoiceControlHumanRobotToolConfig] = None

    async def on_init(self, ten_env: AsyncTenEnv) -> None:
        ten_env.log_debug("[VoiceControlHumanRobotTool] on_init")

    async def on_start(self, ten_env: AsyncTenEnv) -> None:
        ten_env.log_debug("[VoiceControlHumanRobotTool] on_start")

        self.config = await VoiceControlHumanRobotToolConfig.create_async(ten_env=ten_env)
        ten_env.log_info(f"[VoiceControlHumanRobotTool] config: {self.config}")

        await super().on_start(ten_env)
        self.ten_env = ten_env

    async def on_stop(self, ten_env: AsyncTenEnv) -> None:
        ten_env.log_debug("[VoiceControlHumanRobotTool] on_stop")

    async def on_deinit(self, ten_env: AsyncTenEnv) -> None:
        ten_env.log_debug("[VoiceControlHumanRobotTool] on_deinit")

    async def on_cmd(self, ten_env: AsyncTenEnv, cmd: Cmd) -> None:
        cmd_name = cmd.get_name()
        ten_env.log_debug(f"[VoiceControlHumanRobotTool] on_cmd name: {cmd_name}")

        await super().on_cmd(ten_env, cmd)

    def get_tool_metadata(self, ten_env: AsyncTenEnv) -> list[LLMToolMetadata]:
        return [
            LLMToolMetadata(
                name=TOOL_NAME_ACTION,
                description=TOOL_DESCRIPTION_ACTION,
                parameters=[
                    LLMToolMetadataParameter(
                        name="action_name",
                        type="string",
                        description="The action name for the robot, e.g., '打招呼', '双手居中', '握手', '挥手', '手臂伸展', '走路', '停止走路', '左转', '右转'",
                        required=True,
                    ),
                ],
            ),
            LLMToolMetadata(
                name=TOOL_NAME_SPEAK,
                description=TOOL_DESCRIPTION_SPEAK,
                parameters=[
                    LLMToolMetadataParameter(
                        name="text",
                        type="string",
                        description="The text for the robot to speak, e.g., '你好啊，欢迎参观', '我正在为您服务'",
                        required=True,
                    ),
                ],
            ),
            LLMToolMetadata(
                name=TOOL_NAME_GREET,
                description=TOOL_DESCRIPTION_GREET,
                parameters=[
                    LLMToolMetadataParameter(
                        name="greeting_text",
                        type="string",
                        description="The greeting text for the robot to speak, e.g., '你好啊，欢迎参观', '大家好', '欢迎光临'",
                        required=True,
                    ),
                ],
            ),
            LLMToolMetadata(
                name=TOOL_NAME_NAVIGATE,
                description=TOOL_DESCRIPTION_NAVIGATE,
                parameters=[
                    LLMToolMetadataParameter(
                        name="destination",
                        type="string",
                        description="The destination for the robot to navigate to. Use '门口' or '过来' for task_id 2 (come here/to door), use '回去' or '回去的位置' for task_id 3 (go back). e.g., '门口', '过来', '回去'",
                        required=True,
                    ),
                ],
            ),
        ]

    async def run_tool(
        self, ten_env: AsyncTenEnv, name: str, args: dict
    ) -> LLMToolResult | None:
        ten_env.log_info(f"[VoiceControlHumanRobotTool] run_tool name: {name}, args: {args}")

        if name == TOOL_NAME_ACTION:
            result = await self._control_robot_action(args)
            return LLMToolResultLLMResult(
                type="llmresult",
                content=json.dumps(result, ensure_ascii=False),
            )

        if name == TOOL_NAME_SPEAK:
            result = await self._robot_speak(args)
            return LLMToolResultLLMResult(
                type="llmresult",
                content=json.dumps(result, ensure_ascii=False),
            )

        if name == TOOL_NAME_GREET:
            result = await self._robot_greet(args)
            return LLMToolResultLLMResult(
                type="llmresult",
                content=json.dumps(result, ensure_ascii=False),
            )

        if name == TOOL_NAME_NAVIGATE:
            result = await self._robot_navigate(args)
            return LLMToolResultLLMResult(
                type="llmresult",
                content=json.dumps(result, ensure_ascii=False),
            )

        return None

    async def _control_robot_action(self, args: dict) -> Any:
        if "action_name" not in args:
            raise ValueError("Missing required parameter: action_name")

        action_name = args["action_name"]
        server_url = self.config.server_url
        timeout = self.config.timeout
        action_url = f"{server_url}/kuavo/action"

        try:
            self.ten_env.log_info(
                f"[VoiceControlHumanRobotTool] Sending action to robot: {action_name}"
            )

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    action_url,
                    json={"action_name": action_name},
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    result = await response.text()
                    self.ten_env.log_info(
                        f"[VoiceControlHumanRobotTool] Received response: {result}"
                    )

                    if response.status == 200:
                        return {
                            "action_name": action_name,
                            "status": "success",
                            "response": result,
                        }
                    else:
                        return {
                            "action_name": action_name,
                            "status": "error",
                            "error": f"HTTP {response.status}: {result}",
                        }

        except aiohttp.ClientConnectorError:
            self.ten_env.log_error(
                f"[VoiceControlHumanRobotTool] Connection failed - robot server may not be running"
            )
            return {
                "action_name": action_name,
                "status": "error",
                "error": "Connection failed - robot server may not be running",
            }

        except Exception as e:
            self.ten_env.log_error(f"[VoiceControlHumanRobotTool] Failed to control robot: {e}")
            self.ten_env.log_error(traceback.format_exc())
            return {
                "action_name": action_name,
                "status": "error",
                "error": str(e),
            }

    async def _robot_speak(self, args: dict) -> Any:
        if "text" not in args:
            raise ValueError("Missing required parameter: text")

        text = args["text"]
        server_url = self.config.server_url
        timeout = self.config.timeout
        tts_url = f"{server_url}/kuavo/tts"

        try:
            self.ten_env.log_info(
                f"[VoiceControlHumanRobotTool] Sending text to robot TTS: {text}"
            )

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    tts_url,
                    json={"text": text},
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    result = await response.text()
                    self.ten_env.log_info(
                        f"[VoiceControlHumanRobotTool] Received response: {result}"
                    )

                    if response.status == 200:
                        return {
                            "text": text,
                            "status": "success",
                            "response": result,
                        }
                    else:
                        return {
                            "text": text,
                            "status": "error",
                            "error": f"HTTP {response.status}: {result}",
                        }

        except aiohttp.ClientConnectorError:
            self.ten_env.log_error(
                f"[VoiceControlHumanRobotTool] Connection failed - robot TTS server may not be running"
            )
            return {
                "text": text,
                "status": "error",
                "error": "Connection failed - robot TTS server may not be running",
            }

        except Exception as e:
            self.ten_env.log_error(f"[VoiceControlHumanRobotTool] Failed to make robot speak: {e}")
            self.ten_env.log_error(traceback.format_exc())
            return {
                "text": text,
                "status": "error",
                "error": str(e),
            }

    async def _robot_greet(self, args: dict) -> Any:
        if "greeting_text" not in args:
            raise ValueError("Missing required parameter: greeting_text")

        greeting_text = args["greeting_text"]
        server_url = self.config.server_url
        timeout = self.config.timeout
        action_url = f"{server_url}/kuavo/action"
        tts_url = f"{server_url}/kuavo/tts"

        results = []

        # First, execute the greeting action
        try:
            self.ten_env.log_info(
                f"[VoiceControlHumanRobotTool] Sending greeting action to robot"
            )

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    action_url,
                    json={"action_name": "打招呼"},
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    result = await response.text()
                    self.ten_env.log_info(
                        f"[VoiceControlHumanRobotTool] Received action response: {result}"
                    )

                    if response.status == 200:
                        results.append({
                            "action": "打招呼",
                            "status": "success",
                            "response": result,
                        })
                    else:
                        results.append({
                            "action": "打招呼",
                            "status": "error",
                            "error": f"HTTP {response.status}: {result}",
                        })

        except Exception as e:
            self.ten_env.log_error(f"[VoiceControlHumanRobotTool] Failed to execute greeting action: {e}")
            results.append({
                "action": "打招呼",
                "status": "error",
                "error": str(e),
            })

        # Then, execute the TTS with greeting text
        try:
            self.ten_env.log_info(
                f"[VoiceControlHumanRobotTool] Sending greeting text to robot TTS: {greeting_text}"
            )

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    tts_url,
                    json={"text": greeting_text},
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    result = await response.text()
                    self.ten_env.log_info(
                        f"[VoiceControlHumanRobotTool] Received TTS response: {result}"
                    )

                    if response.status == 200:
                        results.append({
                            "tts": greeting_text,
                            "status": "success",
                            "response": result,
                        })
                    else:
                        results.append({
                            "tts": greeting_text,
                            "status": "error",
                            "error": f"HTTP {response.status}: {result}",
                        })

        except Exception as e:
            self.ten_env.log_error(f"[VoiceControlHumanRobotTool] Failed to make robot speak greeting: {e}")
            results.append({
                "tts": greeting_text,
                "status": "error",
                "error": str(e),
            })

        return {
            "command": "greet",
            "greeting_text": greeting_text,
            "results": results,
            "status": "success" if all(r.get("status") == "success" for r in results) else "partial_error",
        }

    async def _robot_navigate(self, args: dict) -> Any:
        if "destination" not in args:
            raise ValueError("Missing required parameter: destination")

        destination = args["destination"]
        server_url = self.config.server_url
        timeout = self.config.timeout
        navigate_url = f"{server_url}/kuavo/navigate"

        # Determine task_id based on destination
        # task_id 2 = go back / return
        # task_id 3 = come here / to door
        # Check go_back first to avoid "回去" matching "来" in come_here_keywords
        go_back_keywords = ["回去", "回原位", "回起点"]
        come_here_keywords = ["门口", "过来", "来这里", "到这里", "到我这里"]

        if any(destination == keyword or keyword in destination for keyword in go_back_keywords):
            task_id = 2
        elif any(destination == keyword or keyword in destination for keyword in come_here_keywords):
            task_id = 3
        else:
            # Default to task_id 2 (go back) for unknown destinations
            task_id = 2

        try:
            self.ten_env.log_info(
                f"[VoiceControlHumanRobotTool] Sending navigate command to robot: destination={destination}, task_id={task_id}"
            )

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    navigate_url,
                    json={"task_id": task_id},
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    result = await response.text()
                    self.ten_env.log_info(
                        f"[VoiceControlHumanRobotTool] Received navigate response: {result}"
                    )

                    if response.status == 200:
                        return {
                            "destination": destination,
                            "task_id": task_id,
                            "status": "success",
                            "response": result,
                        }
                    else:
                        return {
                            "destination": destination,
                            "task_id": task_id,
                            "status": "error",
                            "error": f"HTTP {response.status}: {result}",
                        }

        except aiohttp.ClientConnectorError:
            self.ten_env.log_error(
                f"[VoiceControlHumanRobotTool] Connection failed - robot navigation server may not be running"
            )
            return {
                "destination": destination,
                "task_id": task_id,
                "status": "error",
                "error": "Connection failed - robot navigation server may not be running",
            }

        except Exception as e:
            self.ten_env.log_error(f"[VoiceControlHumanRobotTool] Failed to navigate robot: {e}")
            self.ten_env.log_error(traceback.format_exc())
            return {
                "destination": destination,
                "task_id": task_id,
                "status": "error",
                "error": str(e),
            }
