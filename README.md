# 音游（2.6）插件

绝区零一条龙第三方插件，用于 2.6 音游界面的轨道识别和自动按键。

## 功能

- 识别蓝、粉、绿三种音符颜色。
- 支持三组监测点和两组监测点模式。
- 默认按键映射：蓝色 `F`，粉色 `J`，绿色 `F+J`。
- 支持调试截图，用于排查漏判。

## 安装

将插件包目录放到主程序：

```text
ZenlessZoneZero-OneDragon/plugins/music_game_26/
```

目录结构：

```text
plugins/
└── music_game_26/
    ├── plugin.json
    ├── music_game_26_const.py
    ├── music_game_26_factory.py
    ├── music_game_26.py
    ├── engine.py
    ├── lane_worker.py
    ├── keyboard_controller.py
    ├── music_game_26_config.py
    ├── music_game_26_app_setting.py
    ├── music_game_26_interface.py
    └── assets/
        └── screen_info/
            └── music_game_26.yml
```

安装后刷新应用注册。插件 `DEFAULT_GROUP = True`，可以在“应用运行”中添加并启动。

## 使用

1. 手动进入游戏内 2.6 音游界面。
2. 在一条龙“应用运行”中添加 `音游（2.6）`。
3. 点击开始运行。
4. 需要停止时点击停止，插件会释放按键并结束识别线程。

## 配置

运行后会使用应用配置：

```text
config/{实例}/one_dragon/music_game_26.yml
```

常用配置：

- `roi_mode`：`triple` 或 `dual`。
- `frame_interval_sec`：截图间隔，默认 `0.008`。
- `debug_dump_unknown`：保存调试截图。
- `key_mapping`：颜色到按键映射。
- `head_hsv`、`hold_start_hsv`、`tail_hsv`：HSV 判定范围。

ROI 配置随插件发布：

```text
music_game_26/assets/screen_info/music_game_26.yml
```

插件启动时会把这份 ROI 注册到当前 `ScreenLoader` 内存，无需修改主程序 `assets/`。

## 开发命令

同步 manifest：

```shell
python scripts/sync_manifest.py
```

生成 const：

```shell
python scripts/generate_const.py
```

校验：

```shell
python scripts/validate_plugin.py --strict
```

## 发布

推送 `v*` tag 后，GitHub Actions 会校验插件并自动创建 Release：

```shell
git tag v0.1.0
git push origin v0.1.0
```

Registry 使用 GitHub Release 的源码包作为下载源。
