from __future__ import annotations

import copy

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.operation.application.application_config import ApplicationConfig
from . import music_game_26_const

DEFAULT_CONFIG: dict = {
    "roi_mode": "triple",
    "frame_interval_sec": 0.008,
    "worker_poll_timeout_ms": 3,
    "tap_release_ms": 30,
    "enable_hold": False,
    "rearm_absence_frames": 2,
    "head_min_ratio": 0.04,
    "hold_retrigger_head_ratio": 0.20,
    "hold_retrigger_guard_ms": 180,
    "hold_start_min_ratio": 0.12,
    "tail_min_ratio": 0.04,
    "tail_guard_ms": 120,
    "tail_edge_mode": "leave",
    "hold_timeout_ms": 5000,
    "debug_dump_unknown": False,
    "key_mapping": {
        "blue": ["f"],
        "pink": ["j"],
        "green": ["f", "j"],
    },
    "head_hsv": {
        "blue": {"lower": [96, 155, 220], "upper": [108, 255, 255]},
        "pink": {"lower": [159, 90, 220], "upper": [170, 190, 255]},
        "green": {"lower": [53, 115, 180], "upper": [66, 220, 255]},
    },
    "hold_start_hsv": {
        "blue": {"lower": [94, 170, 160], "upper": [104, 255, 235]},
        "pink": {"lower": [151, 70, 150], "upper": [161, 155, 225]},
        "green": {"lower": [44, 90, 145], "upper": [56, 175, 225]},
    },
    "tail_hsv": {
        "blue": {"lower": [91, 170, 160], "upper": [104, 255, 255]},
        "pink": {"lower": [151, 70, 150], "upper": [166, 170, 255]},
        "green": {"lower": [43, 90, 145], "upper": [56, 195, 255]},
    },
}

ROI_MODE_OPTIONS: list[ConfigItem] = [
    ConfigItem("三组监测点", value="triple", desc="使用 3 条轨道的 A/B 检测点。"),
    ConfigItem("两组监测点", value="dual", desc="使用 2 条轨道的 dual-A/B 检测点。"),
]


class MusicGame26Config(ApplicationConfig):

    def __init__(self, instance_idx: int, group_id: str):
        ApplicationConfig.__init__(
            self,
            app_id=music_game_26_const.APP_ID,
            instance_idx=instance_idx,
            group_id=group_id,
        )

    def _get_copy(self, key: str):
        return copy.deepcopy(DEFAULT_CONFIG[key])

    @property
    def roi_mode(self) -> str:
        return str(self.get("roi_mode", DEFAULT_CONFIG["roi_mode"]))

    @roi_mode.setter
    def roi_mode(self, new_value: str) -> None:
        self.update("roi_mode", str(new_value))

    @property
    def frame_interval_sec(self) -> float:
        return float(self.get("frame_interval_sec", DEFAULT_CONFIG["frame_interval_sec"]))

    @frame_interval_sec.setter
    def frame_interval_sec(self, new_value: float) -> None:
        self.update("frame_interval_sec", float(new_value))

    @property
    def frame_interval_ms(self) -> int:
        return int(round(self.frame_interval_sec * 1000))

    @frame_interval_ms.setter
    def frame_interval_ms(self, new_value: int) -> None:
        self.frame_interval_sec = max(0.001, int(new_value) / 1000.0)

    @property
    def worker_poll_timeout_ms(self) -> int:
        return int(
            self.get("worker_poll_timeout_ms", DEFAULT_CONFIG["worker_poll_timeout_ms"])
        )

    @property
    def tap_release_ms(self) -> int:
        return int(self.get("tap_release_ms", DEFAULT_CONFIG["tap_release_ms"]))

    @property
    def enable_hold(self) -> bool:
        return bool(self.get("enable_hold", DEFAULT_CONFIG["enable_hold"]))

    @property
    def rearm_absence_frames(self) -> int:
        return int(
            self.get("rearm_absence_frames", DEFAULT_CONFIG["rearm_absence_frames"])
        )

    @property
    def head_min_ratio(self) -> float:
        return float(self.get("head_min_ratio", DEFAULT_CONFIG["head_min_ratio"]))

    @property
    def hold_retrigger_head_ratio(self) -> float:
        return float(
            self.get(
                "hold_retrigger_head_ratio",
                DEFAULT_CONFIG["hold_retrigger_head_ratio"],
            )
        )

    @property
    def hold_retrigger_guard_ms(self) -> int:
        return int(
            self.get(
                "hold_retrigger_guard_ms",
                DEFAULT_CONFIG["hold_retrigger_guard_ms"],
            )
        )

    @property
    def hold_start_min_ratio(self) -> float:
        return float(
            self.get("hold_start_min_ratio", DEFAULT_CONFIG["hold_start_min_ratio"])
        )

    @property
    def tail_min_ratio(self) -> float:
        return float(self.get("tail_min_ratio", DEFAULT_CONFIG["tail_min_ratio"]))

    @property
    def tail_guard_ms(self) -> int:
        return int(self.get("tail_guard_ms", DEFAULT_CONFIG["tail_guard_ms"]))

    @property
    def tail_edge_mode(self) -> str:
        return str(self.get("tail_edge_mode", DEFAULT_CONFIG["tail_edge_mode"]))

    @property
    def hold_timeout_ms(self) -> int:
        return int(self.get("hold_timeout_ms", DEFAULT_CONFIG["hold_timeout_ms"]))

    @property
    def debug_dump_unknown(self) -> bool:
        return bool(
            self.get("debug_dump_unknown", DEFAULT_CONFIG["debug_dump_unknown"])
        )

    @debug_dump_unknown.setter
    def debug_dump_unknown(self, new_value: bool) -> None:
        self.update("debug_dump_unknown", bool(new_value))

    @property
    def key_mapping(self) -> dict[str, list[str]]:
        return self.get("key_mapping", self._get_copy("key_mapping"))

    @property
    def head_hsv(self) -> dict[str, dict[str, list[int]]]:
        return self.get("head_hsv", self._get_copy("head_hsv"))

    @property
    def hold_start_hsv(self) -> dict[str, dict[str, list[int]]]:
        return self.get("hold_start_hsv", self._get_copy("hold_start_hsv"))

    @property
    def tail_hsv(self) -> dict[str, dict[str, list[int]]]:
        return self.get("tail_hsv", self._get_copy("tail_hsv"))

