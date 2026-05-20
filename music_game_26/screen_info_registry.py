from __future__ import annotations

from pathlib import Path

from one_dragon.base.screen.screen_info import ScreenInfo
from one_dragon.base.screen.screen_loader import ScreenContext
from one_dragon.utils import yaml_utils


def register_music_game_26_screen_info(screen_loader: ScreenContext) -> None:
    """将插件内置的音游画面区域注册到当前 ScreenLoader。"""
    file_path = Path(__file__).parent / "assets" / "screen_info" / "music_game_26.yml"
    with file_path.open("r", encoding="utf-8") as file:
        data = yaml_utils.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError(f"音游（2.6）画面配置格式错误: {file_path}")

    screen_info = ScreenInfo(data)
    screen_loader.screen_info_list = [
        item
        for item in screen_loader.screen_info_list
        if item.screen_id != screen_info.screen_id
    ]
    screen_loader.screen_info_list.append(screen_info)
    screen_loader.screen_info_map[screen_info.screen_name] = screen_info
    screen_loader._id_2_screen[screen_info.screen_id] = screen_info

    for screen_area in screen_info.area_list:
        key = f"{screen_info.screen_name}.{screen_area.area_name}"
        screen_loader._screen_area_map[key] = screen_area

    screen_loader.init_screen_route()
