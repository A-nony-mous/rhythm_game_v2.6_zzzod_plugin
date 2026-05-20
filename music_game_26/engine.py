from __future__ import annotations

import threading
import time

import numpy as np
from cv2.typing import MatLike

from one_dragon.base.geometry.rectangle import Rect
from one_dragon.utils.log_utils import log
from .keyboard_controller import (
    MusicGame26KeyboardController,
)
from . import music_game_26_const
from .lane_worker import (
    HsvRange,
    LaneFramePacket,
    LaneWorkerSettings,
    MusicGame26LaneWorker,
)
from .music_game_26_config import MusicGame26Config


class MusicGame26Engine:

    def __init__(self, ctx, config: MusicGame26Config):
        self.ctx = ctx
        self.controller = ctx.controller
        self.config = config
        self._lock = threading.RLock()
        self._running: bool = False
        self._paused: bool = False
        self._anchor_rois: list[Rect] = []
        self._tail_rois: list[Rect] = []
        self._keyboard_controller: MusicGame26KeyboardController | None = None
        self._lane_workers: list[MusicGame26LaneWorker] = []

    def start(self) -> None:
        with self._lock:
            self.stop()
            anchor_area_names, tail_area_names = self._get_roi_mode_config()
            self._anchor_rois = self._load_rois(anchor_area_names)
            self._tail_rois = self._load_rois(tail_area_names)
            if len(self._anchor_rois) != len(self._tail_rois) or len(self._anchor_rois) == 0:
                raise ValueError("音游（2.6）ROI 配置数量不匹配")

            self._keyboard_controller = MusicGame26KeyboardController(
                controller=self.controller,
                lane_count=len(self._anchor_rois),
            )
            self._keyboard_controller.start()
            self._lane_workers = [
                MusicGame26LaneWorker(
                    settings=self._build_lane_settings(lane_idx),
                    keyboard_controller=self._keyboard_controller,
                )
                for lane_idx in range(len(self._anchor_rois))
            ]
            for worker in self._lane_workers:
                worker.start()

            self._paused = False
            self._running = True

    def pause(self) -> None:
        with self._lock:
            if not self._running:
                return
            self._paused = True
            for worker in self._lane_workers:
                worker.pause()
            if self._keyboard_controller is not None:
                self._keyboard_controller.clear_all_requests()

    def resume(self) -> None:
        with self._lock:
            if not self._running:
                return
            self._paused = False
            if self._keyboard_controller is not None:
                self._keyboard_controller.clear_all_requests()
            for worker in self._lane_workers:
                worker.resume()

    def stop(self) -> None:
        with self._lock:
            if not self._running and self._keyboard_controller is None:
                return
            lane_workers = self._lane_workers
            keyboard_controller = self._keyboard_controller
            self._lane_workers = []
            self._keyboard_controller = None
            self._running = False
            self._paused = False

        for worker in lane_workers:
            worker.stop()
        if keyboard_controller is not None:
            keyboard_controller.stop()

    def submit_frame(self, screen: MatLike | None) -> None:
        if screen is None:
            return
        with self._lock:
            if not self._running or self._paused:
                return
            lane_workers = list(self._lane_workers)
            anchor_rois = list(self._anchor_rois)
            tail_rois = list(self._tail_rois)

        now = time.perf_counter()
        for lane_idx, worker in enumerate(lane_workers):
            anchor_image = self._crop_roi(screen, anchor_rois[lane_idx])
            tail_image = self._crop_roi(screen, tail_rois[lane_idx])
            if anchor_image is None or tail_image is None:
                continue
            worker.submit_frame(
                LaneFramePacket(
                    anchor_image=anchor_image,
                    tail_image=tail_image,
                    frame_time=now,
                )
            )

    def _build_lane_settings(self, lane_idx: int) -> LaneWorkerSettings:
        return LaneWorkerSettings(
            lane_idx=lane_idx,
            roi_mode=self.config.roi_mode,
            worker_poll_timeout_ms=self.config.worker_poll_timeout_ms,
            tap_release_ms=self.config.tap_release_ms,
            enable_hold=self.config.enable_hold,
            rearm_absence_frames=self.config.rearm_absence_frames,
            head_min_ratio=self.config.head_min_ratio,
            hold_retrigger_head_ratio=self.config.hold_retrigger_head_ratio,
            hold_retrigger_guard_ms=self.config.hold_retrigger_guard_ms,
            hold_start_min_ratio=self.config.hold_start_min_ratio,
            tail_min_ratio=self.config.tail_min_ratio,
            tail_guard_ms=self.config.tail_guard_ms,
            tail_edge_mode=self.config.tail_edge_mode,
            hold_timeout_ms=self.config.hold_timeout_ms,
            debug_dump_unknown=self.config.debug_dump_unknown,
            key_mapping={
                color: frozenset(str(key).lower() for key in keys)
                for color, keys in self.config.key_mapping.items()
            },
            head_hsv=self._parse_hsv_dict(self.config.head_hsv),
            hold_start_hsv=self._parse_hsv_dict(self.config.hold_start_hsv),
            tail_hsv=self._parse_hsv_dict(self.config.tail_hsv),
        )

    def _parse_hsv_dict(
        self, hsv_dict: dict[str, dict[str, list[int]]]
    ) -> dict[str, HsvRange]:
        parsed: dict[str, HsvRange] = {}
        for color, raw_range in hsv_dict.items():
            parsed[color] = HsvRange(
                lower=np.array(raw_range["lower"], dtype=np.uint8),
                upper=np.array(raw_range["upper"], dtype=np.uint8),
            )
        return parsed

    def _crop_roi(self, screen: MatLike, rect: Rect) -> MatLike | None:
        height, width = screen.shape[:2]
        if rect.x1 < 0 or rect.y1 < 0 or rect.x2 > width or rect.y2 > height:
            log.warning("音游（2.6）ROI 越界 %s", rect)
            return None
        cropped = screen[rect.y1 : rect.y2, rect.x1 : rect.x2]
        if cropped.size == 0:
            log.warning("音游（2.6）ROI 空图 %s", rect)
            return None
        return np.ascontiguousarray(cropped.copy())

    def _get_roi_mode_config(
        self,
    ) -> tuple[list[str], list[str]]:
        mode = self.config.roi_mode.lower()
        if mode == "dual":
            return (
                ["dual-A-1", "dual-A-2"],
                ["dual-B-1", "dual-B-2"],
            )
        return (
            ["A点-1", "A点-2", "A点-3"],
            ["B点-1", "B点-2", "B点-3"],
        )

    def _load_rois(self, area_names: list[str]) -> list[Rect]:
        rois: list[Rect] = []
        for area_name in area_names:
            area = self.ctx.screen_loader.get_area(
                music_game_26_const.APP_NAME, area_name
            )
            if area is not None:
                rois.append(area.rect)
                continue

            raise ValueError(f"音游（2.6）缺少区域配置 {area_name}")
        return rois

