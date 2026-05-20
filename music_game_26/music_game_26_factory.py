from __future__ import annotations

from typing import TYPE_CHECKING

from one_dragon.base.operation.application.application_config import ApplicationConfig
from one_dragon.base.operation.application.application_factory import ApplicationFactory
from one_dragon.base.operation.application_base import Application
from . import music_game_26_const
from .music_game_26 import MusicGame26App
from .music_game_26_config import MusicGame26Config

if TYPE_CHECKING:
    from zzz_od.context.zzz_context import ZContext


class MusicGame26AppFactory(ApplicationFactory):

    def __init__(self, ctx: "ZContext"):
        ApplicationFactory.__init__(self, music_game_26_const)
        self.ctx: ZContext = ctx

    def create_application(self, instance_idx: int, group_id: str) -> Application:
        return MusicGame26App(self.ctx)

    def create_config(
        self, instance_idx: int, group_id: str
    ) -> ApplicationConfig:
        return MusicGame26Config(instance_idx=instance_idx, group_id=group_id)

