# -*- coding: utf-8 -*-
"""
StatsPro - Minecraft 统计数据管理插件

为 MCDReforged 提供完整的玩家统计数据管理功能，包括：
- 计分板创建和管理
- 玩家数据查询和排行
- 预设加和计分板
- 数据记录和差值分析
- 多玩家数据合并

作者: CalciumSilicate
版本: 2.0.0
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .commands import CommandHandler
from .constants import PLUGIN_AUTHOR, PLUGIN_ID, PLUGIN_VERSION
from .plugin import StatsProPlugin

if TYPE_CHECKING:
    from mcdreforged.api.all import Info, PluginServerInterface, ServerInterface

__all__ = [
    "PLUGIN_ID",
    "PLUGIN_VERSION",
    "PLUGIN_AUTHOR",
    "StatsProPlugin",
    "on_load",
    "on_unload",
]

PLUGIN_METADATA = {
    "id": PLUGIN_ID,
    "version": PLUGIN_VERSION,
    "name": "StatsPro",
    "description": "Minecraft player statistics management plugin",
    "author": PLUGIN_AUTHOR,
    "link": "https://github.com/CalciumSilicate/StatsPro",
    "dependencies": {},
}

logging.basicConfig(
    level=logging.INFO,
    format="[%(name)s] %(levelname)s: %(message)s",
)

_plugin_instance: StatsProPlugin | None = None
_command_handler: CommandHandler | None = None


def on_load(server: PluginServerInterface, prev_module) -> None:
    """插件加载时调用"""
    global _plugin_instance, _command_handler

    _plugin_instance = StatsProPlugin()
    _plugin_instance.initialize(server)

    _command_handler = CommandHandler(_plugin_instance)
    _command_handler.register_commands(server)

    server.logger.info(f"StatsPro v{PLUGIN_VERSION} loaded successfully")


def on_unload(server: PluginServerInterface) -> None:
    """插件卸载时调用"""
    global _plugin_instance

    if _plugin_instance:
        _plugin_instance.shutdown()
        _plugin_instance = None

    server.logger.info("StatsPro unloaded")


def on_info(server: ServerInterface, info: Info) -> None:
    """兼容旧版本的消息处理（实际上已被命令树取代）"""
    pass
