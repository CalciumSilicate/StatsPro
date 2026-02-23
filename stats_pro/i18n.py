# -*- coding: utf-8 -*-
"""国际化支持模块"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .constants import PLUGIN_ID

logger = logging.getLogger(PLUGIN_ID)


class Language(Enum):
    """支持的语言"""

    ZH_CN = "zh_cn"
    EN_US = "en_us"


@dataclass
class I18n:
    """国际化管理器"""

    current_language: Language = Language.ZH_CN
    _translations: dict[str, dict[str, str]] = field(default_factory=dict)
    _fallback_language: Language = Language.ZH_CN

    def __post_init__(self) -> None:
        self._load_builtin_translations()

    def _load_builtin_translations(self) -> None:
        """加载内置翻译"""
        self._translations = {
            Language.ZH_CN.value: ZH_CN_TRANSLATIONS,
            Language.EN_US.value: EN_US_TRANSLATIONS,
        }

    def load_from_file(self, path: Path) -> bool:
        """从文件加载额外翻译"""
        if not path.exists():
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for lang, translations in data.items():
                if lang in self._translations:
                    self._translations[lang].update(translations)
                else:
                    self._translations[lang] = translations
            return True
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load translations from {path}: {e}")
            return False

    def set_language(self, language: Language | str) -> None:
        """设置当前语言"""
        if isinstance(language, str):
            try:
                language = Language(language.lower())
            except ValueError:
                logger.warning(f"Unknown language: {language}, using default")
                return
        self.current_language = language

    def get(self, key: str, **kwargs: Any) -> str:
        """获取翻译文本"""
        lang = self.current_language.value
        fallback = self._fallback_language.value

        text = self._translations.get(lang, {}).get(key)
        if text is None:
            text = self._translations.get(fallback, {}).get(key)
        if text is None:
            logger.debug(f"Missing translation for key: {key}")
            return key

        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Missing format key {e} for translation: {key}")
                return text
        return text

    def t(self, key: str, **kwargs: Any) -> str:
        """get 的别名"""
        return self.get(key, **kwargs)


# 中文翻译
ZH_CN_TRANSLATIONS: dict[str, str] = {
    # 通用
    "plugin.loaded": "StatsPro v{version} 加载成功",
    "plugin.unloaded": "StatsPro 已卸载",
    "plugin.reloaded": "StatsPro 配置已重载",
    "error.permission_denied": "§c权限不足",
    "error.not_found": "未找到 {item}",
    "error.invalid_input": "输入错误，请输入 {prefix} help 查看帮助",
    # 帮助
    "help.title": "------§rStatsPro v{version} 第§c§l{page}§r页------",
    "help.page_not_found": "没有找到相应页码(第{page}页)",
    "help.prev_page": "[§b←上一页§r]",
    "help.next_page": "[§c下一页→§r]",
    # 计分板
    "scoreboard.created": "已创建 {name} 计分板",
    "scoreboard.display_set": "已尝试显示计分板: {name}",
    "scoreboard.display_off": "已关闭计分板显示",
    # 查询
    "query.result": "{player}的[§e{category}§r.§b{item}§r]的值为: {score}",
    "query.not_found": "未找到玩家 {player} 的数据",
    "query.no_data": "没有找到数据",
    # 排行榜
    "rank.title": "{title}的总和为{total}, 前{count}名如下:",
    "rank.empty": "排行榜为空",
    # 预设
    "preset.created": "成功创建预设 {name}, 前缀: {prefix_true}_ / {prefix_dummy}_",
    "preset.removed": "成功删除预设: {name}",
    "preset.not_found": "未找到预设: {name}",
    "preset.exists": "预设 {name} 已存在",
    "preset.cannot_modify_default": "不能修改 default 预设",
    "preset.item_added": "成功添加 {category}.{item} 到预设 {preset}",
    "preset.item_removed": "成功从预设 {preset} 删除 {category}.{item}",
    "preset.item_exists": "预设 {preset} 已包含 {category}.{item}",
    "preset.item_not_found": "预设 {preset} 不包含 {category}.{item}",
    "preset.cleared": "已清空预设 {name} 的所有计分项",
    "preset.list_title": "------预设列表------",
    "preset.list_empty": "没有自定义预设",
    # 加和计分板
    "sum.created": "已创建加和计分板 ({preset})",
    "sum.cleared": "已关闭加和计分板 ({preset})",
    "sum.all_removed": "已删除预设: {names}",
    # 生成
    "gen.success": "成功生成{mode}文件:\n时间: §b{time}§r\n路径: §c{path}§r",
    "gen.minus_failed": "生成差值文件失败，请检查时间戳是否正确",
    "gen.list_title": "{mode} 列表如下:",
    "gen.list_empty": "{mode} 列表为空",
    "gen.deleted": "成功删除 {count} 个记录",
    "gen.delete_not_found": "未找到要删除的记录",
    # 合并
    "merge.input_added": "成功添加 {player} 到输入列表",
    "merge.input_exists": "{player} 已在输入列表中",
    "merge.input_removed": "成功从输入列表删除 {player}",
    "merge.input_cleared": "成功清空输入列表",
    "merge.input_not_found": "输入列表中不存在 {player}",
    "merge.output_set": "成功将输出玩家设置为 {player}",
    "merge.list_input_title": "输入玩家列表:",
    "merge.list_output_title": "输出玩家: {player}",
    "merge.list_output_empty": "输出玩家: (未设置)",
    "merge.success": "成功将 {inputs} 的数据合并到 {output}",
    "merge.failed": "合并失败: {reason}",
    "merge.empty_config": "输入列表或输出玩家为空",
    # 保存
    "save.success": "已重载数据包并保存存档",
    # 旧命令提示
    "legacy.redirect": "请使用 §c§l{prefix}§r!",
}

# 英文翻译
EN_US_TRANSLATIONS: dict[str, str] = {
    # General
    "plugin.loaded": "StatsPro v{version} loaded successfully",
    "plugin.unloaded": "StatsPro unloaded",
    "plugin.reloaded": "StatsPro configuration reloaded",
    "error.permission_denied": "§cPermission denied",
    "error.not_found": "{item} not found",
    "error.invalid_input": "Invalid input, use {prefix} help for help",
    # Help
    "help.title": "------§rStatsPro v{version} Page §c§l{page}§r------",
    "help.page_not_found": "Page {page} not found",
    "help.prev_page": "[§b←Prev§r]",
    "help.next_page": "[§cNext→§r]",
    # Scoreboard
    "scoreboard.created": "Created scoreboard: {name}",
    "scoreboard.display_set": "Display set to: {name}",
    "scoreboard.display_off": "Scoreboard display turned off",
    # Query
    "query.result": "{player}'s [§e{category}§r.§b{item}§r] = {score}",
    "query.not_found": "No data found for player {player}",
    "query.no_data": "No data found",
    # Ranking
    "rank.title": "{title} total: {total}, top {count}:",
    "rank.empty": "Ranking is empty",
    # Preset
    "preset.created": "Created preset {name}, prefix: {prefix_true}_ / {prefix_dummy}_",
    "preset.removed": "Removed preset: {name}",
    "preset.not_found": "Preset not found: {name}",
    "preset.exists": "Preset {name} already exists",
    "preset.cannot_modify_default": "Cannot modify default preset",
    "preset.item_added": "Added {category}.{item} to preset {preset}",
    "preset.item_removed": "Removed {category}.{item} from preset {preset}",
    "preset.item_exists": "Preset {preset} already contains {category}.{item}",
    "preset.item_not_found": "Preset {preset} does not contain {category}.{item}",
    "preset.cleared": "Cleared all items in preset {name}",
    "preset.list_title": "------Preset List------",
    "preset.list_empty": "No custom presets",
    # Sum scoreboard
    "sum.created": "Created sum scoreboard ({preset})",
    "sum.cleared": "Cleared sum scoreboard ({preset})",
    "sum.all_removed": "Removed presets: {names}",
    # Generate
    "gen.success": "Generated {mode} file:\nTime: §b{time}§r\nPath: §c{path}§r",
    "gen.minus_failed": "Failed to generate diff file, check timestamps",
    "gen.list_title": "{mode} list:",
    "gen.list_empty": "{mode} list is empty",
    "gen.deleted": "Deleted {count} record(s)",
    "gen.delete_not_found": "No records found to delete",
    # Merge
    "merge.input_added": "Added {player} to input list",
    "merge.input_exists": "{player} is already in input list",
    "merge.input_removed": "Removed {player} from input list",
    "merge.input_cleared": "Cleared input list",
    "merge.input_not_found": "{player} not in input list",
    "merge.output_set": "Set output player to {player}",
    "merge.list_input_title": "Input players:",
    "merge.list_output_title": "Output player: {player}",
    "merge.list_output_empty": "Output player: (not set)",
    "merge.success": "Merged {inputs} data into {output}",
    "merge.failed": "Merge failed: {reason}",
    "merge.empty_config": "Input list or output player is empty",
    # Save
    "save.success": "Reloaded datapacks and saved world",
    # Legacy command
    "legacy.redirect": "Please use §c§l{prefix}§r!",
}


# 全局实例
_i18n_instance: I18n | None = None


def get_i18n() -> I18n:
    """获取全局 I18n 实例"""
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = I18n()
    return _i18n_instance


def t(key: str, **kwargs: Any) -> str:
    """便捷翻译函数"""
    return get_i18n().t(key, **kwargs)


def set_language(language: Language | str) -> None:
    """设置语言"""
    get_i18n().set_language(language)
