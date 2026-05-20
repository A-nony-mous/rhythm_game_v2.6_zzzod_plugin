from one_dragon_qt.services.app_setting.app_setting_provider import (
    AppSettingProvider,
    SettingType,
)

from .music_game_26_const import APP_ID


class MusicGame26AppSetting(AppSettingProvider):
    """音游（2.6）运行和设置入口。"""

    app_id = APP_ID
    setting_type = SettingType.INTERFACE

    @staticmethod
    def get_setting_cls() -> type:
        from .music_game_26_interface import MusicGame26Interface

        return MusicGame26Interface
