from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import FluentIcon

from one_dragon.base.operation.application import application_const
from one_dragon_qt.utils.config_utils import get_prop_adapter
from one_dragon_qt.view.app_run_interface import AppRunInterface
from one_dragon_qt.widgets.row import Row
from one_dragon_qt.widgets.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon_qt.widgets.setting_card.help_card import HelpCard
from one_dragon_qt.widgets.setting_card.spin_box_setting_card import SpinBoxSettingCard
from one_dragon_qt.widgets.setting_card.switch_setting_card import SwitchSettingCard

from . import music_game_26_const
from .music_game_26_config import ROI_MODE_OPTIONS, MusicGame26Config


class MusicGame26Interface(AppRunInterface):
    """音游（2.6）运行和设置界面。"""

    def __init__(self, ctx, parent=None):
        self.ctx = ctx
        self.config: Optional[MusicGame26Config] = None
        AppRunInterface.__init__(
            self,
            ctx=ctx,
            app_id=music_game_26_const.APP_ID,
            object_name="music_game_26_interface",
            nav_text_cn=music_game_26_const.APP_NAME,
            parent=parent,
        )

    def get_widget_at_top(self) -> QWidget:
        content = Row()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        content.h_layout.addLayout(left_layout)
        content.h_layout.addLayout(right_layout)

        left_layout.addWidget(
            HelpCard(
                url="",
                title="使用说明",
                content="只支持前台键盘模式。开始前先手动进入音游界面，蓝按 F，粉按 J，绿按 F+J。",
            )
        )
        self.frame_interval_opt = SpinBoxSettingCard(
            icon=FluentIcon.CAMERA,
            title="截图间隔(ms)",
            content="建议先用 8-12ms。先看是否漏按再调。",
            minimum=4,
            maximum=40,
            step=1,
            min_width=120,
        )
        left_layout.addWidget(self.frame_interval_opt)
        self.roi_mode_opt = ComboBoxSettingCard(
            icon=FluentIcon.SEARCH,
            title="监测点模式",
            content="切换三组监测点或两组监测点。修改后重启音游（2.6）应用生效。",
            options_list=ROI_MODE_OPTIONS,
        )
        left_layout.addWidget(self.roi_mode_opt)

        right_layout.addWidget(
            HelpCard(
                url="",
                title="配置文件",
                content="HSV 和判定阈值在 config/{实例}/one_dragon/music_game_26.yml。\nROI 在插件包 music_game_26/assets/screen_info/music_game_26.yml。",
            )
        )
        self.debug_dump_opt = SwitchSettingCard(
            icon=FluentIcon.DEVELOPER_TOOLS,
            title="调试截图",
            content="默认关闭。只在排查漏判时临时开启。",
        )
        right_layout.addWidget(self.debug_dump_opt)
        return content

    def on_interface_shown(self) -> None:
        AppRunInterface.on_interface_shown(self)
        self.config = self.ctx.run_context.get_config(
            app_id=music_game_26_const.APP_ID,
            instance_idx=self.ctx.current_instance_idx,
            group_id=application_const.DEFAULT_GROUP_ID,
        )
        self.frame_interval_opt.init_with_adapter(
            get_prop_adapter(self.config, "frame_interval_ms")
        )
        self.roi_mode_opt.init_with_adapter(get_prop_adapter(self.config, "roi_mode"))
        self.debug_dump_opt.init_with_adapter(
            get_prop_adapter(self.config, "debug_dump_unknown")
        )
