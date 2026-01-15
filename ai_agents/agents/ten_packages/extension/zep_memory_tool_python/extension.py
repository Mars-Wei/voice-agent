#
# This file is part of TEN Framework, an open source project.
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file for more information.
#
import os

try:
    from ten_ai_base.types import (
        LLMToolMetadata,
        LLMToolMetadataParameter,
        LLMToolResultLLMResult,
    )
except Exception as e:
    import traceback
    traceback.print_exc()
    raise

try:
    from ten_ai_base.llm_tool import AsyncLLMToolBaseExtension
except Exception as e:
    import traceback
    traceback.print_exc()
    raise

try:
    from ten_runtime import (
        AsyncTenEnv,
        Cmd,
        Data,
    )
except Exception as e:
    import traceback
    traceback.print_exc()
    raise


class ZepMemoryToolExtension(AsyncLLMToolBaseExtension):
    def __init__(self, name: str):
        try:
            super().__init__(name)
            self.zep_client = None
            self.ten_env = None
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise

    async def on_init(self, ten_env: AsyncTenEnv) -> None:
        ten_env.log_info("[ZepMemoryTool] on_init started")
        try:
            ten_env.log_info("[ZepMemoryTool] on_init: checking imports...")
            # Test if we can import the base classes
            from ten_ai_base.types import LLMToolMetadata
        except Exception as e:
            error_msg = f"[ZepMemoryTool] on_init ERROR: {e}"
            ten_env.log_error(error_msg)
            import traceback
            ten_env.log_error(traceback.format_exc())
            raise

    async def on_start(self, ten_env: AsyncTenEnv) -> None:
        ten_env.log_info("[ZepMemoryTool] on_start started")

        try:
            ten_env.log_info("[ZepMemoryTool] on_start: calling super().on_start()...")
            await super().on_start(ten_env)
            ten_env.log_info("[ZepMemoryTool] on_start: super().on_start() completed")

            # Store ten_env for later use
            self.ten_env = ten_env
            ten_env.log_info("[ZepMemoryTool] on_start: ten_env stored")

            # Initialize Zep client
            ten_env.log_info("[ZepMemoryTool] on_start: checking ZEP_API_KEY environment variable...")
            zep_api_key = os.getenv("ZEP_API_KEY")

            if zep_api_key:
                api_key_preview = f"{zep_api_key[:10]}..." if len(zep_api_key) > 10 else "***"
                ten_env.log_info(f"[ZepMemoryTool] on_start: ZEP_API_KEY found: {api_key_preview} (length: {len(zep_api_key)})")

                try:
                    ten_env.log_info("[ZepMemoryTool] on_start: importing zep_cloud...")
                    from zep_cloud import Zep
                    ten_env.log_info("[ZepMemoryTool] on_start: zep_cloud imported successfully")

                    ten_env.log_info("[ZepMemoryTool] on_start: creating Zep client...")
                    self.zep_client = Zep(api_key=zep_api_key)
                    ten_env.log_info("[ZepMemoryTool] Zep client initialized successfully")
                except ImportError as e:
                    error_msg = f"[ZepMemoryTool] zep-cloud not installed. Install with: pip install zep-cloud. Error: {e}"
                    ten_env.log_error(error_msg)
                    import traceback
                    ten_env.log_error(traceback.format_exc())
                except Exception as e:
                    error_msg = f"[ZepMemoryTool] Failed to initialize Zep client: {e}"
                    ten_env.log_error(error_msg)
                    import traceback
                    ten_env.log_error(traceback.format_exc())
            else:
                ten_env.log_warn(
                    "[ZepMemoryTool] ZEP_API_KEY not set, memory tool will be disabled"
                )

            ten_env.log_info("[ZepMemoryTool] on_start completed successfully")
        except Exception as e:
            error_msg = f"[ZepMemoryTool] on_start ERROR: {e}"
            ten_env.log_error(error_msg)
            import traceback
            ten_env.log_error(traceback.format_exc())
            raise

    async def on_stop(self, ten_env: AsyncTenEnv) -> None:
        ten_env.log_info("[ZepMemoryTool] on_stop")

    async def on_deinit(self, ten_env: AsyncTenEnv) -> None:
        ten_env.log_info("[ZepMemoryTool] on_deinit")

    async def on_cmd(self, ten_env: AsyncTenEnv, cmd: Cmd) -> None:
        cmd_name = cmd.get_name()
        ten_env.log_debug(f"[ZepMemoryTool] on_cmd name {cmd_name}")
        await super().on_cmd(ten_env, cmd)

    async def on_data(self, ten_env: AsyncTenEnv, data: Data) -> None:
        pass

    def get_tool_metadata(self, ten_env: AsyncTenEnv) -> list[LLMToolMetadata]:
        ten_env.log_info("[ZepMemoryTool] get_tool_metadata called")
        try:
            tools = [
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
            ten_env.log_info(f"[ZepMemoryTool] get_tool_metadata: returning {len(tools)} tools")
            return tools
        except Exception as e:
            error_msg = f"[ZepMemoryTool] get_tool_metadata ERROR: {e}"
            ten_env.log_error(error_msg)
            import traceback
            ten_env.log_error(traceback.format_exc())
            raise

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
        """Add conversation to Zep memory

        According to Zep best practices:
        - user_id: Unique identifier for the user (in voice assistant, we use session_id as user_id)
        - thread_id: Unique identifier for the conversation thread (we use session_id as thread_id)
        """
        from zep_cloud.types import Message

        session_id = args.get("session_id", "default")
        # In voice assistant scenario, each session corresponds to one user and one thread
        user_id = session_id  # Use session_id as user_id
        thread_id = session_id  # Use session_id as thread_id (no prefix needed)

        messages = [
            Message(role="user", content=args["user_message"]),
            Message(role="assistant", content=args["assistant_response"]),
        ]

        try:
            # Ensure user exists (create if not exists)
            try:
                self.zep_client.user.get(user_id=user_id)
                ten_env.log_debug(f"[ZepMemoryTool] User {user_id} already exists")
            except Exception as e:
                if "not found" in str(e).lower() or "404" in str(e) or "user not found" in str(e).lower():
                    ten_env.log_info(f"[ZepMemoryTool] Creating user {user_id}")
                    self.zep_client.user.add(user_id=user_id)
                else:
                    ten_env.log_error(f"[ZepMemoryTool] Error getting user {user_id}: {e}")
                    raise

            # Ensure thread exists (create if not exists)
            try:
                self.zep_client.thread.get(thread_id=thread_id)
                ten_env.log_debug(f"[ZepMemoryTool] Thread {thread_id} already exists")
            except Exception as e:
                if "not found" in str(e).lower() or "404" in str(e) or "thread not found" in str(e).lower():
                    ten_env.log_info(f"[ZepMemoryTool] Creating thread {thread_id} for user {user_id}")
                    self.zep_client.thread.create(thread_id=thread_id, user_id=user_id)
                else:
                    ten_env.log_error(f"[ZepMemoryTool] Error getting thread {thread_id}: {e}")
                    raise

            # Add messages to thread
            self.zep_client.thread.add_messages(thread_id=thread_id, messages=messages)
            ten_env.log_info(f"[ZepMemoryTool] Memory added to thread {thread_id} for user {user_id}")
            return "Memory added successfully"
        except Exception as e:
            ten_env.log_error(f"[ZepMemoryTool] Failed to add memory: {e}")
            raise Exception(f"Failed to add memory: {str(e)}")

    async def _retrieve_memory(self, ten_env: AsyncTenEnv, args: dict) -> str:
        """Retrieve relevant memories based on query"""
        session_id = args.get("session_id", "default")
        thread_id = session_id  # Use session_id as thread_id

        try:
            # Ensure thread exists (it should, but check anyway)
            try:
                self.zep_client.thread.get(thread_id=thread_id)
            except Exception as e:
                if "not found" in str(e).lower() or "404" in str(e) or "thread not found" in str(e).lower():
                    ten_env.log_info(f"[ZepMemoryTool] Thread {thread_id} does not exist yet")
                    return "No context available. Thread does not exist yet."
                ten_env.log_error(f"[ZepMemoryTool] Error getting thread {thread_id}: {e}")
                raise

            context_response = self.zep_client.thread.get_user_context(
                thread_id=thread_id
            )

            if hasattr(context_response, "context") and context_response.context:
                ten_env.log_info(f"[ZepMemoryTool] Retrieved context for thread {thread_id}")
                return f"Available context:\n{context_response.context}"
            else:
                ten_env.log_info(f"[ZepMemoryTool] No context available for thread {thread_id}")
                return "No context available."

        except Exception as e:
            ten_env.log_error(f"[ZepMemoryTool] Failed to retrieve memory: {e}")
            raise Exception(f"Failed to retrieve memory: {str(e)}")

    async def _get_memory_summary(self, ten_env: AsyncTenEnv, args: dict) -> str:
        """Get user memory summary"""
        session_id = args.get("session_id", "default")
        thread_id = session_id  # Use session_id as thread_id

        try:
            # Ensure thread exists (it should, but check anyway)
            try:
                self.zep_client.thread.get(thread_id=thread_id)
            except Exception as e:
                if "not found" in str(e).lower() or "404" in str(e) or "thread not found" in str(e).lower():
                    ten_env.log_info(f"[ZepMemoryTool] Thread {thread_id} does not exist yet")
                    return "No memory context available. This appears to be a new session."
                ten_env.log_error(f"[ZepMemoryTool] Error getting thread {thread_id}: {e}")
                raise

            context_response = self.zep_client.thread.get_user_context(
                thread_id=thread_id
            )

            if hasattr(context_response, "context") and context_response.context:
                ten_env.log_info(f"[ZepMemoryTool] Retrieved memory summary for thread {thread_id}")
                return f"Memory context:\n{context_response.context}"
            else:
                ten_env.log_info(f"[ZepMemoryTool] No memory context available for thread {thread_id}")
                return "No memory context available. This appears to be a new session."

        except Exception as e:
            ten_env.log_error(f"[ZepMemoryTool] Failed to get memory summary: {e}")
            raise Exception(f"Failed to get memory summary: {str(e)}")
