from __future__ import annotations

from one_dragon.base.operation.application import application_const
from one_dragon.base.operation.operation_base import OperationResult
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.log_utils import log
from . import music_game_26_const
from .engine import MusicGame26Engine
from .music_game_26_config import MusicGame26Config
from .screen_info_registry import register_music_game_26_screen_info
from zzz_od.application.zzz_application import ZApplication


class MusicGame26App(ZApplication):

    def __init__(self, ctx):
        ZApplication.__init__(
            self,
            ctx=ctx,
            app_id=music_game_26_const.APP_ID,
            op_name=music_game_26_const.APP_NAME,
        )
        self.config: MusicGame26Config = self.ctx.run_context.get_config(
            app_id=music_game_26_const.APP_ID,
            instance_idx=self.ctx.current_instance_idx,
            group_id=application_const.DEFAULT_GROUP_ID,
        )
        self.engine = MusicGame26Engine(self.ctx, self.config)

    def handle_init(self) -> None:
        ZApplication.handle_init(self)
        register_music_game_26_screen_info(self.ctx.screen_loader)
        self.config = MusicGame26Config(
            instance_idx=self.ctx.current_instance_idx,
            group_id=application_const.DEFAULT_GROUP_ID,
        )
        self.engine = MusicGame26Engine(self.ctx, self.config)
        self.engine.stop()

    @operation_node(name="初始化音游（2.6）", is_start_node=True, screenshot_before_round=False)
    def init_game_assistant(self) -> OperationRoundResult:
        try:
            self.ctx.controller.enable_foreground_mode()
            self.ctx.controller.enable_keyboard()
            self.ctx.controller.active_window()
            self.engine.start()
        except Exception:
            log.error("音游（2.6）初始化失败", exc_info=True)
            self.engine.stop()
            return self.round_fail(status="初始化失败")
        return self.round_success(status="音游识别已启动")

    @node_from(from_name="初始化音游（2.6）")
    @operation_node(name="持续识别音符", mute=True)
    def run_music_loop(self) -> OperationRoundResult:
        self.engine.submit_frame(self.last_screenshot)
        return self.round_wait(wait_round_time=self.config.frame_interval_sec)

    def handle_pause(self, e=None):
        self.engine.pause()

    def handle_resume(self, e=None):
        self.ctx.controller.enable_foreground_mode()
        self.ctx.controller.enable_keyboard()
        ZApplication.handle_resume(self)
        self.engine.resume()

    def after_operation_done(self, result: OperationResult):
        self.engine.stop()
        ZApplication.after_operation_done(self, result)

