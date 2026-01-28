import asyncio
import json
import time
from typing import Literal

from .agent.decorators import agent_event_handler
from ten_runtime import (
    AsyncExtension,
    AsyncTenEnv,
    Cmd,
    Data,
)

from .agent.agent import Agent
from .agent.events import (
    ASRResultEvent,
    LLMResponseEvent,
    ToolRegisterEvent,
    UserJoinedEvent,
    UserLeftEvent,
)
from .helper import _send_cmd, _send_data, parse_sentences
from .config import MainControlConfig  # assume extracted from your base model
import uuid
import traceback

from .memory import MemoryStore, ZepMemoryStore
from zep_cloud.types import Message as ZepMessage


class MainControlExtension(AsyncExtension):
    """
    The entry point of the agent module.
    Consumes semantic AgentEvents from the Agent class and drives the runtime behavior.
    """

    def __init__(self, name: str):
        super().__init__(name)
        self.ten_env: AsyncTenEnv = None
        self.agent: Agent = None
        self.config: MainControlConfig = None

        self.stopped: bool = False
        self._rtc_user_count: int = 0
        self.sentence_fragment: str = ""
        self.turn_id: int = 0
        self.session_id: str = "0"

        self.zep_client: MemoryStore | None = None

    def _current_metadata(self) -> dict:
        return {"session_id": self.session_id, "turn_id": self.turn_id}

    async def on_init(self, ten_env: AsyncTenEnv):
        self.ten_env = ten_env

        config_json, _ = await ten_env.get_property_to_json(None)
        self.config = MainControlConfig.model_validate_json(config_json)

        self.zep_client = ZepMemoryStore(
            env=ten_env,
            api_key=self.config.zep_api_key,
        )

        self.agent = Agent(ten_env)

        # Load memory summary and write into LLM context
        await self._load_memory_to_context()

        # Now auto-register decorated methods
        for attr_name in dir(self):
            fn = getattr(self, attr_name)
            event_type = getattr(fn, "_agent_event_type", None)
            if event_type:
                self.agent.on(event_type, fn)

    # === Register handlers with decorators ===
    @agent_event_handler(UserJoinedEvent)
    async def _on_user_joined(self, event: UserJoinedEvent):
        self._rtc_user_count += 1
        if self._rtc_user_count == 1 and self.config and self.config.greeting:
            await self._send_to_tts(self.config.greeting, True)
            await self._send_transcript("assistant", self.config.greeting, True, 100)

    @agent_event_handler(UserLeftEvent)
    async def _on_user_left(self, event: UserLeftEvent):
        self._rtc_user_count -= 1

    @agent_event_handler(ToolRegisterEvent)
    async def _on_tool_register(self, event: ToolRegisterEvent):
        await self.agent.register_llm_tool(event.tool, event.source)

    @agent_event_handler(ASRResultEvent)
    async def _on_asr_result(self, event: ASRResultEvent):
        self.session_id = event.metadata.get("session_id", "100")
        stream_id = int(self.session_id)
        if not event.text:
            return
        if event.final or len(event.text) > 2:
            await self._interrupt()
        if event.final:
            self.turn_id += 1
            related_memory = await self._retrieve_related_memory(query=event.text, user_id=self.config.user_id)
            self.ten_env.log_info(f"[_on_asr_result_memory] related_memory: \n{related_memory}\n\n")
            if related_memory:
                context_message = f"[Related Memory Context]\n{related_memory}\n\n[Current User Question]\n{event.text}"
                await self.agent.queue_llm_input(context_message)
            else:
                await self.agent.queue_llm_input(event.text)

        await self._send_transcript("user", event.text, event.final, stream_id)

    @agent_event_handler(LLMResponseEvent)
    async def _on_llm_response(self, event: LLMResponseEvent):
        if not event.is_final and event.type == "message":
            sentences, self.sentence_fragment = parse_sentences(
                self.sentence_fragment, event.delta
            )
            for s in sentences:
                await self._send_to_tts(s, False)

            # Early send: if sentence_fragment exceeds min_tts_chunk_size, send it to TTS
            # This reduces latency for first TTS audio when LLM outputs long text without punctuation
            min_chunk_size = getattr(self.config, 'min_tts_chunk_size', 5)
            if self.sentence_fragment and len(self.sentence_fragment) >= min_chunk_size:
                await self._send_to_tts(self.sentence_fragment, False)
                self.sentence_fragment = ""

        if event.is_final and event.type == "message":
            remaining_text = self.sentence_fragment or ""
            self.sentence_fragment = ""
            await self._send_to_tts(remaining_text, True)

            if self.turn_id % 2 == 0 and self.config.enable_memorization:
                zep_start = time.perf_counter()
                await self._memorize_conversation()
                zep_end = time.perf_counter()
                self.ten_env.log_info(f"[MainControlExtension] _add_message_to_zep cost: {round((zep_end - zep_start) * 1000, 2)} ms")

        await self._send_transcript(
            "assistant",
            event.text,
            event.is_final,
            100,
            data_type=("reasoning" if event.type == "reasoning" else "text"),
        )

    async def on_start(self, ten_env: AsyncTenEnv):
        ten_env.log_info("[MainControlExtension] on_start")

    async def on_stop(self, ten_env: AsyncTenEnv):
        ten_env.log_info("[MainControlExtension] on_stop")
        self.stopped = True
        await self.agent.stop()

    async def on_cmd(self, ten_env: AsyncTenEnv, cmd: Cmd):
        await self.agent.on_cmd(cmd)

    async def on_data(self, ten_env: AsyncTenEnv, data: Data):
        await self.agent.on_data(data)

    # === helpers ===
    async def _send_transcript(
        self,
        role: str,
        text: str,
        final: bool,
        stream_id: int,
        data_type: Literal["text", "reasoning"] = "text",
    ):
        """
        Sends the transcript (ASR or LLM output) to the message collector.
        """
        if data_type == "text":
            await _send_data(
                self.ten_env,
                "message",
                "message_collector",
                {
                    "data_type": "transcribe",
                    "role": role,
                    "text": text,
                    "text_ts": int(time.time() * 1000),
                    "is_final": final,
                    "stream_id": stream_id,
                },
            )
        elif data_type == "reasoning":
            await _send_data(
                self.ten_env,
                "message",
                "message_collector",
                {
                    "data_type": "raw",
                    "role": role,
                    "text": json.dumps(
                        {
                            "type": "reasoning",
                            "data": {
                                "text": text,
                            },
                        }
                    ),
                    "text_ts": int(time.time() * 1000),
                    "is_final": final,
                    "stream_id": stream_id,
                },
            )
        self.ten_env.log_info(
            f"[MainControlExtension] Sent transcript: {role}, final={final}, text={text}"
        )

    async def _send_to_tts(self, text: str, is_final: bool):
        """
        Sends a sentence to the TTS system.
        """
        request_id = f"tts-request-{self.turn_id}"
        await _send_data(
            self.ten_env,
            "tts_text_input",
            "tts",
            {
                "request_id": request_id,
                "text": text,
                "text_input_end": is_final,
                "metadata": self._current_metadata(),
            },
        )
        self.ten_env.log_info(
            f"[MainControlExtension] Sent to TTS: is_final={is_final}, text={text}"
        )

    async def _interrupt(self):
        """
        Interrupts ongoing LLM and TTS generation. Typically called when user speech is detected.
        """
        self.sentence_fragment = ""
        await self.agent.flush_llm()
        await _send_data(
            self.ten_env, "tts_flush", "tts", {"flush_id": str(uuid.uuid4())}
        )
        await _send_cmd(self.ten_env, "flush", "agora_rtc")
        self.ten_env.log_info("[MainControlExtension] Interrupt signal sent")

    # === Memory related methods ===
    async def _retrieve_related_memory(
        self, query: str, user_id: str = None
    ) -> str:
        """Retrieve related memory based on user query using Zep semantic search"""
        if not self.zep_client  or not isinstance(self.zep_client, ZepMemoryStore):
            return ""

        try:
            memory_text = await self.zep_client.retrieve_user_preferences_context(user_id, query)
            self.ten_env.log_info(
                f"[MainControlExtension] Retrieved related memory (length: {len(memory_text)})"
            )
            return memory_text

        except Exception as e:
            self.ten_env.log_error(
                f"[MainControlExtension] Failed to retrieve related memory: {e}"
            )
            self.ten_env.log_error(traceback.format_exc())
            return ""

    async def _load_memory_to_context(self):
        """Load memory summary into LLM context at startup (as a system message)."""
        if not self.zep_client or not isinstance(self.zep_client, ZepMemoryStore):
            return

        try:
            user_id = self.config.user_id
            agent_id = self.config.agent_id
            memory_summary = await self.zep_client.retrieve_user_context(
                user_id=user_id, agent_id=agent_id
            )
            self.ten_env.log_info(
                f"[MainControlExtension] Memory summary: {memory_summary}"
            )

            if memory_summary and self.agent and self.agent.llm_exec:
                self.agent.llm_exec.clear_context()
                await self.agent.llm_exec.write_context(
                    self.ten_env,
                    "assistant",
                    "Memory summary of previous conversations:\n\n" + memory_summary,
                )
                self.ten_env.log_info(
                    "[MainControlExtension] Memory summary written into LLM context"
                )

        except Exception as e:
            self.ten_env.log_error(
                f"[MainControlExtension] Failed to load memory to context: {e}"
            )

    async def _memorize_conversation(self, user_id: str = None, user_name: str = None):
        """Memorize the current conversation via configured store"""
        if not self.zep_client or not isinstance(self.zep_client, ZepMemoryStore):
            return

        try:
            llm_context = (
                self.agent.llm_exec.get_context()
                if self.agent and self.agent.llm_exec
                else []
            )
            zep_messages = []
            for m in llm_context:
                role = getattr(m, "role", None)
                content = getattr(m, "content", None)
                if role in ["user", "assistant"] and isinstance(content, str):
                    self.ten_env.log_info(f"[MainControlExtension] _memorize_conversation_debug, role: {role}, content: {content}")
                    if role=="user":
                        query= await self._get_query(content)
                        if query:
                            content=query
                        zep_messages.append(ZepMessage(
                            name=self.config.user_name,
                            content=content,
                            role=role)
                        )
                    else:
                        zep_messages.append(ZepMessage(
                            name="AI Assistant",
                            content=content,
                            role=role)
                        )
                    self.ten_env.log_info(f"[MainControlExtension] _memorize_conversation_debug, role: {role}, content: {content}")

            if not zep_messages:
                return
            self.ten_env.log_info(f"[MainControlExtension] _memorize_conversation_debug, zep_messages: {zep_messages}")
            asyncio.create_task(self.zep_client.add_message_to_zep(self.config.user_id, self.config.agent_id, messages=zep_messages))
        except Exception as e:
            self.ten_env.log_error(f"[MainControlExtension] Failed to memorize conversation: {e}")

    async def _get_query(self, mem_content:str)->str:
        separator = "[Current User Question]\n"
        sep_index = mem_content.rfind(separator)
        if sep_index == -1:
            return ""

        query_start = sep_index + len(separator)
        query= mem_content[query_start:]
        return query.strip()
