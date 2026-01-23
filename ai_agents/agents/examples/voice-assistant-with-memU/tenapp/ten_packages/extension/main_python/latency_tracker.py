"""
Latency Tracker for Voice Assistant Pipeline

Tracks timing metrics across the full voice pipeline:
- User speech end (last audio) -> ASR final result
- ASR final -> Zep memory service call start/end
- Memory service end -> LLM call start
- LLM call start -> LLM first response
- LLM first response -> TTS first audio chunk

This provides end-to-end latency measurement from user speech end
to first TTS audio playback.
"""

import time
from dataclasses import dataclass, field
from typing import Optional
from ten_runtime import AsyncTenEnv


@dataclass
class TurnLatencyMetrics:
    """Latency metrics for a single conversation turn."""

    turn_id: int

    # Timestamps (milliseconds since epoch)
    asr_final_time: Optional[float] = None  # When ASR final result received
    zep_start_time: Optional[float] = None  # When Zep memory call started
    zep_end_time: Optional[float] = None  # When Zep memory call ended
    llm_call_start_time: Optional[float] = None  # When LLM request sent
    llm_first_response_time: Optional[float] = None  # When first LLM delta received
    llm_final_response_time: Optional[float] = None  # When LLM response completed
    tts_first_chunk_time: Optional[float] = None  # When first TTS audio chunk sent

    def get_asr_to_zep_start_ms(self) -> Optional[float]:
        """Time from ASR final to Zep call start."""
        if self.asr_final_time and self.zep_start_time:
            return self.zep_start_time - self.asr_final_time
        return None

    def get_zep_duration_ms(self) -> Optional[float]:
        """Zep memory call duration."""
        if self.zep_start_time and self.zep_end_time:
            return self.zep_end_time - self.zep_start_time
        return None

    def get_zep_to_llm_start_ms(self) -> Optional[float]:
        """Time from Zep end to LLM call start."""
        if self.zep_end_time and self.llm_call_start_time:
            return self.llm_call_start_time - self.zep_end_time
        return None

    def get_llm_first_token_ms(self) -> Optional[float]:
        """Time to first LLM token (TTFT)."""
        if self.llm_call_start_time and self.llm_first_response_time:
            return self.llm_first_response_time - self.llm_call_start_time
        return None

    def get_llm_total_ms(self) -> Optional[float]:
        """Total LLM response time."""
        if self.llm_call_start_time and self.llm_final_response_time:
            return self.llm_final_response_time - self.llm_call_start_time
        return None

    def get_llm_to_tts_first_ms(self) -> Optional[float]:
        """Time from first LLM response to first TTS chunk."""
        if self.llm_first_response_time and self.tts_first_chunk_time:
            return self.tts_first_chunk_time - self.llm_first_response_time
        return None

    def get_end_to_end_ms(self) -> Optional[float]:
        """Total end-to-end latency: ASR final -> TTS first chunk."""
        if self.asr_final_time and self.tts_first_chunk_time:
            return self.tts_first_chunk_time - self.asr_final_time
        return None


class LatencyTracker:
    """
    Tracks latency metrics for voice assistant pipeline.

    Usage:
        tracker = LatencyTracker(ten_env)

        # On ASR final result
        tracker.mark_asr_final(turn_id)

        # Before/after Zep memory call
        tracker.mark_zep_start(turn_id)
        tracker.mark_zep_end(turn_id)

        # Before LLM call
        tracker.mark_llm_call_start(turn_id)

        # On first LLM delta
        tracker.mark_llm_first_response(turn_id)

        # On first TTS chunk - this prints the full report
        tracker.mark_tts_first_chunk(turn_id)
    """

    def __init__(self, ten_env: AsyncTenEnv):
        self.ten_env = ten_env
        self._turns: dict[int, TurnLatencyMetrics] = {}
        self._log_category = "LATENCY_TRACKER"

    def _get_or_create_turn(self, turn_id: int) -> TurnLatencyMetrics:
        """Get existing turn metrics or create new one."""
        if turn_id not in self._turns:
            self._turns[turn_id] = TurnLatencyMetrics(turn_id=turn_id)
        return self._turns[turn_id]

    def _now_ms(self) -> float:
        """Get current time in milliseconds."""
        return time.time() * 1000

    def mark_asr_final(self, turn_id: int) -> None:
        """Mark when ASR final result is received (user speech end point)."""
        turn = self._get_or_create_turn(turn_id)
        turn.asr_final_time = self._now_ms()
        self.ten_env.log_info(
            f"[{self._log_category}] Turn {turn_id}: ASR final received"
        )

    def mark_zep_start(self, turn_id: int) -> None:
        """Mark when Zep memory service call starts."""
        turn = self._get_or_create_turn(turn_id)
        turn.zep_start_time = self._now_ms()
        latency = turn.get_asr_to_zep_start_ms()
        self.ten_env.log_info(
            f"[{self._log_category}] Turn {turn_id}: Zep call start "
            f"(ASR->Zep: {latency:.1f}ms)"
            if latency
            else f"[{self._log_category}] Turn {turn_id}: Zep call start"
        )

    def mark_zep_end(self, turn_id: int) -> None:
        """Mark when Zep memory service call completes."""
        turn = self._get_or_create_turn(turn_id)
        turn.zep_end_time = self._now_ms()
        duration = turn.get_zep_duration_ms()
        self.ten_env.log_info(
            f"[{self._log_category}] Turn {turn_id}: Zep call end "
            f"(Zep duration: {duration:.1f}ms)"
            if duration
            else f"[{self._log_category}] Turn {turn_id}: Zep call end"
        )

    def mark_llm_call_start(self, turn_id: int) -> None:
        """Mark when LLM request is sent."""
        turn = self._get_or_create_turn(turn_id)
        turn.llm_call_start_time = self._now_ms()
        zep_to_llm = turn.get_zep_to_llm_start_ms()
        self.ten_env.log_info(
            f"[{self._log_category}] Turn {turn_id}: LLM call start "
            f"(Zep->LLM: {zep_to_llm:.1f}ms)"
            if zep_to_llm
            else f"[{self._log_category}] Turn {turn_id}: LLM call start"
        )

    def mark_llm_first_response(self, turn_id: int) -> None:
        """Mark when first LLM response token is received."""
        turn = self._get_or_create_turn(turn_id)
        # Only mark first response once per turn
        if turn.llm_first_response_time is None:
            turn.llm_first_response_time = self._now_ms()
            ttft = turn.get_llm_first_token_ms()
            self.ten_env.log_info(
                f"[{self._log_category}] Turn {turn_id}: LLM first token "
                f"(TTFT: {ttft:.1f}ms)"
                if ttft
                else f"[{self._log_category}] Turn {turn_id}: LLM first token"
            )

    def mark_llm_final_response(self, turn_id: int) -> None:
        """Mark when LLM response is complete."""
        turn = self._get_or_create_turn(turn_id)
        turn.llm_final_response_time = self._now_ms()
        total = turn.get_llm_total_ms()
        self.ten_env.log_info(
            f"[{self._log_category}] Turn {turn_id}: LLM complete "
            f"(Total LLM: {total:.1f}ms)"
            if total
            else f"[{self._log_category}] Turn {turn_id}: LLM complete"
        )

    def mark_tts_first_chunk(self, turn_id: int) -> None:
        """Mark when first TTS audio chunk is ready. Prints full latency report."""
        turn = self._get_or_create_turn(turn_id)
        # Only mark and report first TTS chunk once per turn
        if turn.tts_first_chunk_time is None:
            turn.tts_first_chunk_time = self._now_ms()
            self._print_latency_report(turn)

    def _print_latency_report(self, turn: TurnLatencyMetrics) -> None:
        """Print full latency report for a turn."""
        e2e = turn.get_end_to_end_ms()
        asr_to_zep = turn.get_asr_to_zep_start_ms()
        zep_duration = turn.get_zep_duration_ms()
        zep_to_llm = turn.get_zep_to_llm_start_ms()
        llm_ttft = turn.get_llm_first_token_ms()
        llm_to_tts = turn.get_llm_to_tts_first_ms()

        report_lines = [
            f"",
            f"{'=' * 60}",
            f"LATENCY REPORT - Turn {turn.turn_id}",
            f"{'=' * 60}",
            f"",
            f"Stage Breakdown:",
            f"  ASR Final -> Zep Start:     {asr_to_zep:.1f}ms"
            if asr_to_zep
            else "  ASR Final -> Zep Start:     N/A",
            f"  Zep Memory Duration:        {zep_duration:.1f}ms"
            if zep_duration
            else "  Zep Memory Duration:        N/A",
            f"  Zep End -> LLM Start:       {zep_to_llm:.1f}ms"
            if zep_to_llm
            else "  Zep End -> LLM Start:       N/A",
            f"  LLM Time-to-First-Token:    {llm_ttft:.1f}ms"
            if llm_ttft
            else "  LLM Time-to-First-Token:    N/A",
            f"  LLM First -> TTS First:     {llm_to_tts:.1f}ms"
            if llm_to_tts
            else "  LLM First -> TTS First:     N/A",
            f"",
            f"{'─' * 60}",
            f"  END-TO-END LATENCY:         {e2e:.1f}ms"
            if e2e
            else "  END-TO-END LATENCY:         N/A",
            f"  (User speech end -> First TTS audio)",
            f"{'=' * 60}",
            f"",
        ]

        report = "\n".join(report_lines)
        self.ten_env.log_info(f"[{self._log_category}]\n{report}")

    def cleanup_turn(self, turn_id: int) -> None:
        """Remove metrics for a completed turn to free memory."""
        if turn_id in self._turns:
            del self._turns[turn_id]

    def get_turn_metrics(self, turn_id: int) -> Optional[TurnLatencyMetrics]:
        """Get metrics for a specific turn."""
        return self._turns.get(turn_id)
