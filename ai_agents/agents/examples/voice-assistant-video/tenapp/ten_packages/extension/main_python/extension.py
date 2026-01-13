import asyncio
import json
import time
import traceback
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

        # ⭐ 新增：延迟追踪状态
        self.turn_vad_timestamp: float = 0  # [A] VAD 判停时刻
        self.turn_llm_first_token_time: float = 0  # [B] LLM 第一个 token 时刻
        self.current_turn_id: int = 0  # 当前追踪的 turn_id

    def _current_metadata(self) -> dict:
        return {"session_id": self.session_id, "turn_id": self.turn_id}

    async def on_init(self, ten_env: AsyncTenEnv):
        self.ten_env = ten_env

        # Load config from runtime properties
        config_json, _ = await ten_env.get_property_to_json(None)
        self.config = MainControlConfig.model_validate_json(config_json)

        self.agent = Agent(ten_env)

        # Now auto-register decorated methods
        for attr_name in dir(self):
            fn = getattr(self, attr_name)
            event_type = getattr(fn, "_agent_event_type", None)
            if event_type:
                self.agent.on(event_type, fn)

        ten_env.log_info("[MainControlExtension] Latency tracker initialized")

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

        # ⭐ VAD 判停时记录时间戳 [A]
        if event.final:
            self.turn_id += 1
            self.current_turn_id = self.turn_id
            self.turn_vad_timestamp = time.time()  # [时间点 A]
            self.turn_llm_first_token_time = 0  # 重置 LLM 时间

            # ⭐ 输出延迟追踪日志
            self.ten_env.log_info(
                f"[LATENCY_TRACKER] Turn {self.turn_id}: VAD stopped at {self.turn_vad_timestamp}"
            )

            await self.agent.queue_llm_input(event.text)

        await self._send_transcript("user", event.text, event.final, stream_id)

    @agent_event_handler(LLMResponseEvent)
    async def _on_llm_response(self, event: LLMResponseEvent):
        # ⭐ 检测 LLM 第一个 delta，记录时间 [B]
        if (
            self.turn_llm_first_token_time == 0
            and self.current_turn_id == self.turn_id
            and event.delta
            and not event.is_final
        ):
            self.turn_llm_first_token_time = time.time()  # [时间点 B]

            # 计算 LLM TTFT
            if self.turn_vad_timestamp > 0:
                llm_ttft_ms = (
                    self.turn_llm_first_token_time - self.turn_vad_timestamp
                ) * 1000
                self.ten_env.log_info(
                    f"[LATENCY_TRACKER] Turn {self.turn_id}: "
                    f"LLM first token at {self.turn_llm_first_token_time}, "
                    f"LLM_TTFT={llm_ttft_ms:.0f}ms"
                )

        # 正常处理 LLM 响应
        if not event.is_final and event.type == "message":
            sentences, self.sentence_fragment = parse_sentences(
                self.sentence_fragment, event.delta
            )
            for s in sentences:
                await self._send_to_tts(s, False)

        if event.is_final and event.type == "message":
            remaining_text = self.sentence_fragment or ""
            self.sentence_fragment = ""
            await self._send_to_tts(remaining_text, True)

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

    # ⭐ 监听所有数据（调试用）
    async def on_data(self, ten_env: AsyncTenEnv, data: Data):
        # ⭐ 调试日志：显示所有收到的数据名称
        data_name = data.get_name()
        ten_env.log_debug(f"[DEBUG] on_data received: name={data_name}")

        # ⭐ 监听 TTS 的 metrics 数据（包含 ttfb）
        if data_name == "metrics":
            ten_env.log_debug(f"[DEBUG] Received metrics data")
            await self._handle_tts_metrics(data)

        # 原有的 on_data 逻辑
        await self.agent.on_data(data)

    async def _handle_tts_metrics(self, data: Data):
        """⭐ 处理 TTS 返回的 metrics，计算完整 E2E 延迟"""
        try:
            # 注意：get_property_to_json 在这里不是 async 的
            metrics_json, _ = data.get_property_to_json(None)
            metrics = (
                json.loads(metrics_json)
                if isinstance(metrics_json, str)
                else metrics_json
            )

            # ⭐ 调试日志：打印完整 metrics
            self.ten_env.log_info(
                f"[DEBUG_METRICS] Raw metrics: {json.dumps(metrics, indent=2)}"
            )

            # 解析 metrics 结构
            module = metrics.get("module", "")
            metrics_dict = metrics.get("metrics", {})

            # 只处理 TTS TTFB metrics
            # 注意: module 是小写 "tts", key 是 "ttfb" (不是 "tts_ttfb")
            if module != "tts" or "ttfb" not in metrics_dict:
                self.ten_env.log_debug(
                    f"[DEBUG_METRICS] Not TTS TTFB: module={module}, keys={list(metrics_dict.keys())}"
                )
                return

            ttfb_ms = metrics_dict.get("ttfb", 0)
            self.ten_env.log_info(f"[DEBUG_METRICS] TTS TTFB: {ttfb_ms}ms")

            # 如果是当前追踪的 turn，计算完整延迟
            if self.current_turn_id == self.turn_id and self.turn_vad_timestamp > 0:
                now = time.time()

                # 计算各阶段延迟
                e2e_latency_ms = 0  # A → D
                llm_ttft_ms = 0  # A → B
                tts_ttfb_ms = float(ttfb_ms)  # TTS 内部 TTFB
                llm_to_tts_ms = 0  # B → D

                # E2E = (当前时间 - VAD 判停时间)
                e2e_latency_ms = (now - self.turn_vad_timestamp) * 1000

                # LLM TTFT (如果已记录）
                if self.turn_llm_first_token_time > 0:
                    llm_ttft_ms = (
                        self.turn_llm_first_token_time - self.turn_vad_timestamp
                    ) * 1000

                # LLM → TTS = E2E - LLM_TTFT - TTS_TTFB
                if e2e_latency_ms > 0:
                    llm_to_tts_ms = e2e_latency_ms - llm_ttft_ms - tts_ttfb_ms

                # ⭐ 输出完整延迟指标
                self.ten_env.log_info(
                    f"[LATENCY_METRICS] Turn {self.turn_id}: "
                    f"E2E={e2e_latency_ms:.0f}ms, "
                    f"LLM_TTFT={llm_ttft_ms:.0f}ms, "
                    f"TTS_TTFB={tts_ttfb_ms:.0f}ms, "
                    f"LLM→TTS={llm_to_tts_ms:.0f}ms"
                )

                # 清除当前 turn 的追踪状态
                self.turn_vad_timestamp = 0
                self.turn_llm_first_token_time = 0
                self.current_turn_id = 0
            else:
                self.ten_env.log_info(
                    f"[DEBUG_METRICS] Turn mismatch or no vad_timestamp: "
                    f"current_turn_id={self.current_turn_id}, "
                    f"turn_id={self.turn_id}, "
                    f"has_vad_timestamp={self.turn_vad_timestamp > 0}"
                )

        except Exception as e:
            self.ten_env.log_error(
                f"Error handling TTS metrics: {e}\n{traceback.format_exc()}"
            )

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
