# ZZZ OD Plugin Template

第三方插件模板。Fork 后替换插件 ID、元数据和源码，运行脚本生成兼容常量文件，再发布 GitHub Release 并提交到 Plugin Registry。

## 快速开始

1. Fork 本仓库。
2. 将 `sample_plugin` 改成你的插件 ID。
3. 更新根目录 `plugin.json`。
4. 运行同步、生成和校验命令。
5. 把插件包复制到主程序 `plugins/<plugin_package>/` 调试。
6. 发布 `v*` tag 和 GitHub Release。
7. 到 `plugin-registry` 提交收录 Issue。

## 改名清单

假设插件 ID 为 `coffee_route_plus`：

```text
sample_plugin/ -> coffee_route_plus/
sample_plugin/sample_plugin_const.py -> coffee_route_plus/coffee_route_plus_const.py
sample_plugin/sample_plugin_factory.py -> coffee_route_plus/coffee_route_plus_factory.py
sample_plugin/sample_plugin.py -> coffee_route_plus/coffee_route_plus.py
sample_plugin/sample_plugin_app_setting.py -> coffee_route_plus/coffee_route_plus_app_setting.py
```

同步修改 Python 导入、类名和 `plugin.json.id`。

插件 ID 规则：

```text
^[a-z][a-z0-9_]*$
```

统一约束：

```text
plugin.json.id == plugin_package == APP_ID
```

## 常用命令

同步根 manifest 到插件包内：

```shell
python scripts/sync_manifest.py
```

生成 const 文件：

```shell
python scripts/generate_const.py
```

校验模板：

```shell
python scripts/validate_plugin.py --strict
```

CI 检查模式：

```shell
python scripts/sync_manifest.py --check
python scripts/generate_const.py --check
python scripts/validate_plugin.py --strict
```

## Manifest

根目录和插件包内各有一份 manifest：

```text
plugin.json
sample_plugin/plugin.json
```

两份内容保持一致。根目录 manifest 供 Registry CI 和 Release 工作流读取，包内 manifest 供客户端安装后校验。

关键字段：

```json
{
  "id": "sample_plugin",
  "name": "示例插件",
  "summary": "展示第三方插件模板的最小结构。",
  "version": "0.1.0",
  "versionCode": 1,
  "defaultGroup": false,
  "needNotify": false,
  "author": {
    "name": "Your Name",
    "url": "https://github.com/your-name"
  },
  "homepage": "https://github.com/your-name/sample-plugin",
  "risk": ["automation"],
  "compatibility": {
    "minAppVersion": "0.0.0",
    "minCoreApiVersion": 1,
    "python": ">=3.11"
  },
  "apps": []
}
```

## 本地调试

将插件包复制到主程序目录：

```text
ZenlessZoneZero-OneDragon/plugins/sample_plugin/
```

启动主程序后刷新插件注册。加载失败时查看插件管理页或 `factory_manager.scan_failures` 报告。

## 设置页

`sample_plugin_app_setting.py` 提供 `AppSettingProvider` 示例。作者接入真实设置界面时，把 `get_setting_cls()` 中的占位导入替换为自己的 `BaseInterface` 或 `AppSettingFlyout` 类。

## 发布 Release

发布前执行：

```shell
python scripts/sync_manifest.py
python scripts/generate_const.py
python scripts/validate_plugin.py --strict
```

推荐 tag：

```text
v0.1.0
```

Registry 使用 GitHub Release 自动源码包作为下载源，并记录 tag、commit、sha256、发布时间、`version` 和 `versionCode`。

## 提交 Registry

提交 Issue 字段：

```text
plugin_id
repo_url
summary
tags
risk
notes
```

示例：

```text
plugin_id: sample_plugin
repo_url: https://github.com/your-name/sample-plugin
summary: 展示第三方插件模板的最小结构。
tags: sample, automation
risk: automation
notes: 首版提交。
```
