# -*- coding: utf-8 -*-
"""插件主类"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .config import PluginConfig
from .constants import PLUGIN_ID
from .gen_service import GenService
from .merge_service import MergeService
from .scoreboard_service import ScoreboardService
from .stats_service import StatsService

if TYPE_CHECKING:
    from mcdreforged.api.all import PluginServerInterface

logger = logging.getLogger(PLUGIN_ID)


class StatsProPlugin:
    """StatsPro 插件主类"""

    def __init__(self):
        self._config: PluginConfig | None = None
        self._stats_service: StatsService | None = None
        self._scoreboard_service: ScoreboardService | None = None
        self._gen_service: GenService | None = None
        self._merge_service: MergeService | None = None
        self._initialized = False

    @property
    def config(self) -> PluginConfig:
        if self._config is None:
            raise RuntimeError("Plugin not initialized")
        return self._config

    @property
    def stats_service(self) -> StatsService:
        if self._stats_service is None:
            raise RuntimeError("Plugin not initialized")
        return self._stats_service

    @property
    def scoreboard_service(self) -> ScoreboardService:
        if self._scoreboard_service is None:
            raise RuntimeError("Plugin not initialized")
        return self._scoreboard_service

    @property
    def gen_service(self) -> GenService:
        if self._gen_service is None:
            raise RuntimeError("Plugin not initialized")
        return self._gen_service

    @property
    def merge_service(self) -> MergeService:
        if self._merge_service is None:
            raise RuntimeError("Plugin not initialized")
        return self._merge_service

    def initialize(self, server: PluginServerInterface) -> None:
        """初始化插件"""
        if self._initialized:
            logger.warning("Plugin already initialized")
            return

        logger.info("Initializing StatsPro plugin...")

        self._config = PluginConfig.load()
        self._config.save()

        self._stats_service = StatsService(self._config)
        self._scoreboard_service = ScoreboardService(
            self._config, self._stats_service
        )
        self._gen_service = GenService(self._config, self._stats_service)
        self._merge_service = MergeService(self._config, self._stats_service)

        self._stats_service.reload_all_stats()

        self._initialized = True
        logger.info("StatsPro plugin initialized successfully")

    def shutdown(self) -> None:
        """关闭插件"""
        if not self._initialized:
            return

        logger.info("Shutting down StatsPro plugin...")

        if self._config:
            self._config.save()

        self._initialized = False
        logger.info("StatsPro plugin shut down")

    def reload(self) -> None:
        """重载插件配置"""
        if not self._initialized:
            logger.warning("Cannot reload: plugin not initialized")
            return

        logger.info("Reloading StatsPro configuration...")

        self._config = PluginConfig.load()
        self._stats_service = StatsService(self._config)
        self._scoreboard_service = ScoreboardService(
            self._config, self._stats_service
        )
        self._gen_service = GenService(self._config, self._stats_service)
        self._merge_service = MergeService(self._config, self._stats_service)

        self._stats_service.reload_all_stats()

        logger.info("StatsPro configuration reloaded")
