from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass
from enum import Enum

import cv2
import numpy as np
from cv2.typing import MatLike

from one_dragon.utils import debug_utils
from one_dragon.utils.log_utils import log
from .keyboard_controller import (
    MusicGame26KeyboardController,
)


@dataclass(frozen=True)
class HsvRange:
    lower: np.ndarray
    upper: np.ndarray


@dataclass(frozen=True)
class LaneFramePacket:
    anchor_image: MatLike
    tail_image: MatLike
    frame_time: float


@dataclass(frozen=True)
class LaneWorkerSettings:
    lane_idx: int
    roi_mode: str
    worker_poll_timeout_ms: int
    tap_release_ms: int
    enable_hold: bool
    rearm_absence_frames: int
    head_min_ratio: float
    hold_retrigger_head_ratio: float
    hold_retrigger_guard_ms: int
    hold_start_min_ratio: float
    tail_min_ratio: float
    tail_guard_ms: int
    tail_edge_mode: str
    hold_timeout_ms: int
    debug_dump_unknown: bool
    key_mapping: dict[str, frozenset[str]]
    head_hsv: dict[str, HsvRange]
    hold_start_hsv: dict[str, HsvRange]
    tail_hsv: dict[str, HsvRange]


class LaneState(Enum):
    IDLE = "IDLE"
    TAP_PENDING_RELEASE = "TAP_PENDING_RELEASE"
    WAITING_FOR_TAIL = "WAITING_FOR_TAIL"


class MusicGame26LaneWorker:

    def __init__(
        self,
        settings: LaneWorkerSettings,
        keyboard_controller: MusicGame26KeyboardController,
    ):
        self.settings = settings
        self.lane_idx: int = settings.lane_idx
        self.keyboard_controller = keyboard_controller
        self.frame_queue: queue.Queue[LaneFramePacket] = queue.Queue(maxsize=1)
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._thread: threading.Thread | None = None

        self._state: LaneState = LaneState.IDLE
        self._armed: bool = True
        self._absence_frames: int = 0
        self._current_color: str | None = None
        self._tap_release_deadline: float | None = None
        self._hold_deadline: float | None = None
        self._hold_start_time: float | None = None
        self._tail_signal_active: bool = False
        self._last_anchor_image: MatLike | None = None
        self._last_tail_image: MatLike | None = None
        self._last_debug_dump_time: dict[str, float] = {}
        self._last_hold_ratio: float = 0.0
        self._last_tail_ratio: float = 0.0
        self._last_anchor_confidence_log_time: float = 0.0

    @property
    def state(self) -> LaneState:
        return self._state

    @property
    def current_color(self) -> str | None:
        return self._current_color

    @property
    def armed(self) -> bool:
        return self._armed

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._pause_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name=f"music_game_26_lane_{self.lane_idx + 1}",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._pause_event.clear()
        if self._thread is not None:
            self._thread.join(timeout=1)
            self._thread = None
        self._flush_queue()
        self.keyboard_controller.clear_lane(self.lane_idx)
        self._reset_state()

    def pause(self) -> None:
        self._pause_event.set()
        self._flush_queue()
        self.keyboard_controller.clear_lane(self.lane_idx)
        self._reset_state()

    def resume(self) -> None:
        self._flush_queue()
        self._reset_state()
        self._pause_event.clear()

    def submit_frame(self, packet: LaneFramePacket) -> None:
        if self._stop_event.is_set() or self._pause_event.is_set():
            return
        try:
            self.frame_queue.put_nowait(packet)
        except queue.Full:
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.frame_queue.put_nowait(packet)
            except queue.Full:
                pass

    def classify_head_color(self, anchor_image: MatLike) -> str | None:
        hsv_image = cv2.cvtColor(anchor_image, cv2.COLOR_RGB2HSV)
        best_color, best_ratio = self._pick_best_ratio(
            self._collect_ratios(hsv_image, self.settings.head_hsv)
        )
        if best_color is None or best_ratio < self.settings.head_min_ratio:
            return None
        return best_color

    def _run(self) -> None:
        while not self._stop_event.is_set():
            if self._pause_event.is_set():
                time.sleep(0.01)
                continue

            now = time.perf_counter()
            self._process_timers(now)
            timeout = self._get_poll_timeout_seconds(now)

            try:
                if timeout <= 0:
                    packet = self.frame_queue.get_nowait()
                else:
                    packet = self.frame_queue.get(timeout=timeout)
            except queue.Empty:
                self._process_timers(time.perf_counter())
                continue

            if self._pause_event.is_set():
                continue

            self._process_packet(packet, time.perf_counter())
            self._process_timers(time.perf_counter())

    def _get_poll_timeout_seconds(self, now: float) -> float:
        poll_timeout = max(self.settings.worker_poll_timeout_ms / 1000.0, 0.001)
        deadlines = [
            deadline
            for deadline in (self._tap_release_deadline, self._hold_deadline)
            if deadline is not None
        ]
        if not deadlines:
            return poll_timeout
        remaining = max(0.0, min(deadlines) - now)
        return min(poll_timeout, remaining)

    def _process_packet(self, packet: LaneFramePacket, now: float) -> None:
        self._last_anchor_image = packet.anchor_image
        self._last_tail_image = packet.tail_image

        anchor_hsv = cv2.cvtColor(packet.anchor_image, cv2.COLOR_RGB2HSV)
        head_ratios = self._collect_ratios(anchor_hsv, self.settings.head_hsv)
        head_color, head_ratio = self._pick_best_ratio(head_ratios)
        self._maybe_log_anchor_confidence(head_color, head_ratio, head_ratios, now)

        if head_color is None or head_ratio < self.settings.head_min_ratio:
            self._absence_frames += 1
            if self._absence_frames >= self.settings.rearm_absence_frames:
                self._armed = True
            self._maybe_dump_unknown_anchor(
                packet.anchor_image, head_color, head_ratio, head_ratios, now
            )
        else:
            self._absence_frames = 0
            if self._should_retrigger_from_waiting_tail(head_ratio, now):
                self._release_note()
                self._armed = False
                self._handle_head_detected(packet, head_color, head_ratio, now)
                return
            if self._armed and self._state == LaneState.IDLE:
                self._armed = False
                self._handle_head_detected(packet, head_color, head_ratio, now)

        if self._state == LaneState.WAITING_FOR_TAIL:
            self._check_tail_signal(packet.tail_image, now)

    def _handle_head_detected(
        self, packet: LaneFramePacket, head_color: str, head_ratio: float, now: float
    ) -> None:
        if not self.settings.enable_hold:
            self._enter_tap(head_color, now)
            return

        tail_hsv = cv2.cvtColor(packet.tail_image, cv2.COLOR_RGB2HSV)
        hold_ratio = self._mask_ratio(
            tail_hsv, self.settings.hold_start_hsv[head_color]
        )
        self._last_hold_ratio = hold_ratio

        if hold_ratio >= self.settings.hold_start_min_ratio:
            self._enter_hold(head_color, now)
            return

        self._enter_tap(head_color, now)

    def _enter_tap(self, color: str, now: float) -> None:
        self._state = LaneState.TAP_PENDING_RELEASE
        self._current_color = color
        self._tap_release_deadline = now + self.settings.tap_release_ms / 1000.0
        self._hold_deadline = None
        self._tail_signal_active = False
        self.keyboard_controller.set_lane_keys(
            self.lane_idx, self.settings.key_mapping[color]
        )

    def _enter_hold(self, color: str, now: float) -> None:
        self._state = LaneState.WAITING_FOR_TAIL
        self._current_color = color
        self._tap_release_deadline = None
        self._hold_deadline = now + self.settings.hold_timeout_ms / 1000.0
        self._hold_start_time = now
        self._tail_signal_active = False
        self.keyboard_controller.set_lane_keys(
            self.lane_idx, self.settings.key_mapping[color]
        )

    def _check_tail_signal(self, tail_image: MatLike, now: float) -> None:
        if self._current_color is None:
            return

        tail_hsv = cv2.cvtColor(tail_image, cv2.COLOR_RGB2HSV)
        tail_ratio = self._mask_ratio(
            tail_hsv, self.settings.tail_hsv[self._current_color]
        )
        self._last_tail_ratio = tail_ratio
        tail_present = tail_ratio >= self.settings.tail_min_ratio
        edge_mode = self.settings.tail_edge_mode.lower()
        hold_elapsed_ms = (
            (now - self._hold_start_time) * 1000.0
            if self._hold_start_time is not None
            else 0.0
        )
        if hold_elapsed_ms < self.settings.tail_guard_ms:
            self._tail_signal_active = False
            return

        if edge_mode == "leave":
            if self._tail_signal_active and not tail_present:
                self._release_note()
            self._tail_signal_active = tail_present
            return

        if tail_present and not self._tail_signal_active:
            self._release_note()
        self._tail_signal_active = tail_present

    def _process_timers(self, now: float) -> None:
        if (
            self._state == LaneState.TAP_PENDING_RELEASE
            and self._tap_release_deadline is not None
            and now >= self._tap_release_deadline
        ):
            self._release_note()

        if (
            self._state == LaneState.WAITING_FOR_TAIL
            and self._hold_deadline is not None
        ):
            if now >= self._hold_deadline:
                if self.settings.debug_dump_unknown:
                    self._save_debug_pair(
                        self._last_anchor_image,
                        self._last_tail_image,
                        "hold_timeout",
                        now,
                    )
                self._release_note()

    def _release_note(self) -> None:
        self.keyboard_controller.clear_lane(self.lane_idx)
        self._state = LaneState.IDLE
        self._current_color = None
        self._tap_release_deadline = None
        self._hold_deadline = None
        self._hold_start_time = None
        self._tail_signal_active = False
        self._last_hold_ratio = 0.0
        self._last_tail_ratio = 0.0

    def _reset_state(self) -> None:
        self._state = LaneState.IDLE
        self._armed = True
        self._absence_frames = 0
        self._current_color = None
        self._tap_release_deadline = None
        self._hold_deadline = None
        self._hold_start_time = None
        self._tail_signal_active = False
        self._last_anchor_image = None
        self._last_tail_image = None
        self._last_hold_ratio = 0.0
        self._last_tail_ratio = 0.0

    def _flush_queue(self) -> None:
        while True:
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                return

    def _collect_ratios(
        self, hsv_image: MatLike, hsv_ranges: dict[str, HsvRange]
    ) -> dict[str, float]:
        return {
            color: self._mask_ratio(hsv_image, hsv_range)
            for color, hsv_range in hsv_ranges.items()
        }

    def _pick_best_ratio(self, ratios: dict[str, float]) -> tuple[str | None, float]:
        best_color: str | None = None
        best_ratio = 0.0
        for color, ratio in ratios.items():
            if ratio > best_ratio:
                best_ratio = ratio
                best_color = color
        return best_color, best_ratio

    def _mask_ratio(self, hsv_image: MatLike, hsv_range: HsvRange) -> float:
        mask = cv2.inRange(hsv_image, hsv_range.lower, hsv_range.upper)
        return float(np.count_nonzero(mask)) / float(mask.size)

    def _maybe_dump_unknown_anchor(
        self,
        anchor_image: MatLike,
        head_color: str | None,
        head_ratio: float,
        head_ratios: dict[str, float],
        now: float,
    ) -> None:
        if not self.settings.debug_dump_unknown:
            return
        if not self._armed or self._state != LaneState.IDLE:
            return
        if head_ratio < self.settings.head_min_ratio * 0.85:
            return
        if not self._can_dump_debug("head_unknown", now):
            return
        self._save_debug_pair(
            anchor_image, None, "head_unknown", now, skip_rate_limit=True
        )

    def _save_debug_pair(
        self,
        anchor_image: MatLike | None,
        tail_image: MatLike | None,
        reason: str,
        now: float,
        skip_rate_limit: bool = False,
    ) -> None:
        if anchor_image is None and tail_image is None:
            return
        if not skip_rate_limit and not self._can_dump_debug(reason, now):
            return

        if anchor_image is None:
            image_to_save = tail_image
        elif tail_image is None:
            image_to_save = anchor_image
        else:
            image_to_save = self._compose_debug_image(anchor_image, tail_image)

        debug_utils.save_debug_image(
            image=image_to_save,
            prefix=f"music_game_26_lane{self.lane_idx + 1}_{reason}",
        )

    def _can_dump_debug(self, reason: str, now: float) -> bool:
        last_time = self._last_debug_dump_time.get(reason, 0.0)
        if now - last_time < 2.0:
            return False
        self._last_debug_dump_time[reason] = now
        return True

    def _compose_debug_image(
        self, anchor_image: MatLike, tail_image: MatLike
    ) -> MatLike:
        height = max(anchor_image.shape[0], tail_image.shape[0])
        width = anchor_image.shape[1] + tail_image.shape[1]
        canvas = np.zeros((height, width, 3), dtype=np.uint8)
        canvas[: anchor_image.shape[0], : anchor_image.shape[1]] = anchor_image
        canvas[
            : tail_image.shape[0],
            anchor_image.shape[1] : anchor_image.shape[1] + tail_image.shape[1],
        ] = tail_image
        return canvas

    def _maybe_log_anchor_confidence(
        self,
        head_color: str | None,
        head_ratio: float,
        head_ratios: dict[str, float],
        now: float,
    ) -> None:
        if self.settings.roi_mode.lower() != "dual" or self.lane_idx != 1:
            return
        if now - self._last_anchor_confidence_log_time < 0.25:
            return
        self._last_anchor_confidence_log_time = now
        log.info(
            "音游（2.6）dual-A-2 置信度 best=%s ratio=%.3f threshold=%.3f ratios=%s state=%s armed=%s",
            head_color,
            head_ratio,
            self.settings.head_min_ratio,
            {key: round(val, 3) for key, val in head_ratios.items()},
            self._state.value,
            self._armed,
        )

    def _should_retrigger_from_waiting_tail(self, head_ratio: float, now: float) -> bool:
        if self._state != LaneState.WAITING_FOR_TAIL:
            return False
        if head_ratio < self.settings.hold_retrigger_head_ratio:
            return False
        if self._hold_start_time is None:
            return True
        hold_elapsed_ms = (now - self._hold_start_time) * 1000.0
        return hold_elapsed_ms >= self.settings.hold_retrigger_guard_ms

