#
# This file is part of TEN Framework, an open source project.
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file for more information.
#
import os

from ten_ai_base.types import (
    LLMToolMetadata,
    LLMToolMetadataParameter,
    LLMToolResultLLMResult,
)
from ten_ai_base.llm_tool import AsyncLLMToolBaseExtension
from ten_runtime import (
    AsyncTenEnv,
    Cmd,
    Data,
)


class ZepMemoryToolExtension(AsyncLLMToolBaseExtension):
    def __init__(self, name: str):
        super().__init__(name)
        self.zep_client = None
        self.ten_env = None

    async def on_init(self, ten_env: AsyncTenEnv) -> None:
        ten_env.log_debug("[ZepMemoryTool] on_init")

    async def on_start(self, ten_env: AsyncTenEnv) -> None:
        ten_env.log_debug("[ZepMemoryTool] on_start")
        await super().on_start(ten_env)

        # Store ten_env for later use
        self.ten_env = ten_env

        # Initialize Zep client
        zep_api_key = os.getenv("ZEP_API_KEY")

        if zep_api_key:
            try:
                from zep_cloud import Zep

                self.zep_client = Zep(api_key=zep_api_key)
                ten_env.log_info("[ZepMemoryTool] Zep client initialized successfully")
            except ImportError as e:
                ten_env.log_error(
                    f"[ZepMemoryTool] zep-cloud not installed. "
                    f"Install with: pip install zep-cloud. Error: {e}"
                )
            except Exception as e:
                ten_env.log_error(
                    f"[ZepMemoryTool] Failed to initialize Zep client: {e}"
                )
        else:
            ten_env.log_warn(
                "[ZepMemoryTool] ZEP_API_KEY not set, memory tool will be disabled"
            )

    async def on_stop(self, ten_env: AsyncTenEnv) -> None:
        ten_env.log_debug("[ZepMemoryTool] on_stop")

    async def on_deinit(self, ten_env: AsyncTenEnv) -> None:
        ten_env.log_debug("[ZepMemoryTool] on_deinit")

    async def on_cmd(self, ten_env: AsyncTenEnv, cmd: Cmd) -> None:
        cmd_name = cmd.get_name()
        ten_env.log_debug(f"[ZepMemoryTool] on_cmd name {cmd_name}")
        await super().on_cmd(ten_env, cmd)

    async def on_data(self, ten_env: AsyncTenEnv, data: Data) -> None:
        pass

    def get_tool_metadata(self, ten_env: AsyncTenEnv) -> list[LLMToolMetadata]:
        return [
            LLMToolMetadata(
                name="add_memory",
                description="Add a conversation turn to long-term memory. "
                "Call this after each meaningful conversation exchange "
                "to build up the user's memory.",
                parameters=[
                    LLMToolMetadataParameter(
                        name="user_message",
                        type="string",
                        description="The user's message in the conversation",
                        required=True,
                    ),
                    LLMToolMetadataParameter(
                        name="assistant_response",
                        type="string",
                        description="The assistant's response in the conversation",
                        required=True,
                    ),
                    LLMToolMetadataParameter(
                        name="session_id",
                        type="string",
                        description="Unique session identifier",
                        required=True,
                    ),
                ],
            ),
            LLMToolMetadata(
                name="retrieve_memory",
                description="Retrieve relevant memories based on a query. "
                "Use this when you need to recall information about the user "
                "or previous conversations.",
                parameters=[
                    LLMToolMetadataParameter(
                        name="query",
                        type="string",
                        description="The search query to find relevant memories",
                        required=True,
                    ),
                    LLMToolMetadataParameter(
                        name="session_id",
                        type="string",
                        description="Unique session identifier",
                        required=True,
                    ),
                ],
            ),
            LLMToolMetadata(
                name="get_memory_summary",
                description="Get a summary of the user's memory profile. "
                "Use this at the start of conversations to understand "
                "the user better.",
                parameters=[
                    LLMToolMetadataParameter(
                        name="session_id",
                        type="string",
                        description="Unique session identifier",
                        required=True,
                    ),
                ],
            ),
        ]

    async def run_tool(self, ten_env: AsyncTenEnv, name: str, args: dict):
        if not self.zep_client:
            return LLMToolResultLLMResult(
                type="llmresult",
                content="Memory system is not available. "
                "Please check ZEP_API_KEY configuration.",
            )

        try:
            if name == "add_memory":
                result = await self._add_memory(ten_env, args)
            elif name == "retrieve_memory":
                result = await self._retrieve_memory(ten_env, args)
            elif name == "get_memory_summary":
                result = await self._get_memory_summary(ten_env, args)
            else:
                result = f"Unknown tool: {name}"

            return LLMToolResultLLMResult(type="llmresult", content=result)

        except Exception as e:
            ten_env.log_error(f"[ZepMemoryTool] Tool execution failed: {e}")
            return LLMToolResultLLMResult(
                type="llmresult", content=f"Memory operation failed: {str(e)}"
            )

    async def _add_memory(self, ten_env: AsyncTenEnv, args: dict) -> str:
        """Add conversation to Zep memory"""
        from zep_cloud.types import Message

        session_id = args.get("session_id", "default")
        thread_id = f"session_{session_id}"

        messages = [
            Message(role="user", content=args["user_message"]),
            Message(role="assistant", content=args["assistant_response"]),
        ]

        try:
            self.zep_client.thread.add_messages(thread_id=thread_id, messages=messages)
            ten_env.log_info(f"[ZepMemoryTool] Memory added to thread {thread_id}")
            return "Memory added successfully"
        except Exception as e:
            raise Exception(f"Failed to add memory: {str(e)}")

    async def _retrieve_memory(self, ten_env: AsyncTenEnv, args: dict) -> str:
        """Retrieve relevant memories based on query"""
        session_id = args.get("session_id", "default")
        thread_id = f"session_{session_id}"

        try:
            context_response = self.zep_client.thread.get_user_context(
                thread_id=thread_id
            )

            if hasattr(context_response, "context") and context_response.context:
                return f"Available context:\n{context_response.context}"
            else:
                return "No context available."

        except Exception as e:
            raise Exception(f"Failed to retrieve memory: {str(e)}")

    async def _get_memory_summary(self, ten_env: AsyncTenEnv, args: dict) -> str:
        """Get user memory summary"""
        session_id = args.get("session_id", "default")
        thread_id = f"session_{session_id}"

        try:
            context_response = self.zep_client.thread.get_user_context(
                thread_id=thread_id
            )

            if hasattr(context_response, "context") and context_response.context:
                return f"Memory context:\n{context_response.context}"
            else:
                return "No memory context available. This appears to be a new session."

        except Exception as e:
            raise Exception(f"Failed to get memory summary: {str(e)}")
