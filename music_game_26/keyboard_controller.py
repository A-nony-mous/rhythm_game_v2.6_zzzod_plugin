from __future__ import annotations

import threading
from collections.abc import Iterable
from typing import Any

from one_dragon.utils.log_utils import log


class MusicGame26KeyboardController:

    VALID_KEYS = frozenset({"f", "j"})

    def __init__(self, controller: Any, lane_count: int = 3):
        self.controller: Any = controller
        self._lane_keys: list[frozenset[str]] = [frozenset() for _ in range(lane_count)]
        self._physical_keys: set[str] = set()
        self._condition = threading.Condition()
        self._stop_event = threading.Event()
        self._dirty: bool = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._dirty = True
        self._thread = threading.Thread(
            target=self._run,
            name="music_game_26_keyboard_controller",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        with self._condition:
            self._dirty = True
            self._condition.notify_all()
        if self._thread is not None:
            self._thread.join(timeout=1)
            self._thread = None
        with self._condition:
            self._lane_keys = [frozenset() for _ in self._lane_keys]
        self._sync_physical_keys(set())

    def set_lane_keys(self, lane_idx: int, keys: Iterable[str]) -> None:
        normalized = self._normalize_keys(keys)
        with self._condition:
            if self._lane_keys[lane_idx] == normalized:
                return
            self._lane_keys[lane_idx] = normalized
            self._dirty = True
            self._condition.notify_all()

    def clear_lane(self, lane_idx: int) -> None:
        self.set_lane_keys(lane_idx, ())

    def clear_all_requests(self) -> None:
        with self._condition:
            if all(len(keys) == 0 for keys in self._lane_keys):
                return
            self._lane_keys = [frozenset() for _ in self._lane_keys]
            self._dirty = True
            self._condition.notify_all()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            with self._condition:
                while not self._dirty and not self._stop_event.is_set():
                    self._condition.wait(timeout=0.05)
                if self._stop_event.is_set():
                    break
                aggregate_keys = set().union(*self._lane_keys)
                self._dirty = False
            self._sync_physical_keys(aggregate_keys)

        self._sync_physical_keys(set())

    def _sync_physical_keys(self, target_keys: set[str]) -> None:
        to_release = sorted(self._physical_keys - target_keys)
        to_press = sorted(target_keys - self._physical_keys)

        for key in to_release:
            try:
                self.controller.btn_release(key)
            except Exception:
                log.error("音游（2.6）释放按键失败 %s", key, exc_info=True)
            finally:
                self._physical_keys.discard(key)

        for key in to_press:
            try:
                self.controller.btn_press(key)
            except Exception:
                log.error("音游（2.6）按下按键失败 %s", key, exc_info=True)
            else:
                self._physical_keys.add(key)

    def _normalize_keys(self, keys: Iterable[str]) -> frozenset[str]:
        normalized = {str(key).lower() for key in keys if key}
        invalid = normalized - self.VALID_KEYS
        if invalid:
            log.warning("音游（2.6）忽略未知按键映射 %s", sorted(invalid))
        return frozenset(normalized & self.VALID_KEYS)

