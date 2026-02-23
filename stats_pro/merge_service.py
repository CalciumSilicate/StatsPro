# -*- coding: utf-8 -*-
"""玩家数据合并服务"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .config import PluginConfig
from .constants import PLUGIN_ID
from .models import PlayerStats
from .stats_service import StatsService

if TYPE_CHECKING:
    pass

logger = logging.getLogger(PLUGIN_ID)


class MergeService:
    """玩家数据合并服务"""

    def __init__(self, config: PluginConfig, stats_service: StatsService):
        self.config = config
        self.stats_service = stats_service

    @property
    def merge_config(self):
        return self.config.merge_config

    def add_input_player(self, player: str) -> bool:
        """添加输入玩家"""
        if player in self.merge_config.input_players:
            return False
        self.merge_config.add_input(player)
        self.config.save()
        return True

    def remove_input_player(self, player: str) -> bool:
        """移除输入玩家"""
        if player == "all":
            self.merge_config.clear_inputs()
            self.config.save()
            return True
        
        result = self.merge_config.remove_input(player)
        if result:
            self.config.save()
        return result

    def set_output_player(self, player: str) -> None:
        """设置输出玩家"""
        self.merge_config.set_output(player)
        self.config.save()

    def get_input_players(self) -> list[str]:
        """获取输入玩家列表"""
        return list(self.merge_config.input_players)

    def get_output_player(self) -> str:
        """获取输出玩家"""
        return self.merge_config.output_player

    def execute_merge(self) -> tuple[bool, str]:
        """执行合并操作"""
        if not self.merge_config.is_valid():
            return False, "输入列表或输出玩家为空"

        input_players = list(set(self.merge_config.input_players))
        output_player = self.merge_config.output_player

        all_stats = self.stats_service.get_all_stats(reload=True)

        players_to_merge = input_players.copy()
        if output_player not in players_to_merge:
            players_to_merge.append(output_player)

        stats_to_merge = []
        for player in players_to_merge:
            if player in all_stats:
                stats_to_merge.append(all_stats[player])

        if not stats_to_merge:
            return False, "未找到任何玩家的统计数据"

        merged = self._merge_player_stats(stats_to_merge)

        output_uuid = self.stats_service.get_uuid(output_player)
        if output_uuid is None:
            return False, f"未找到玩家 {output_player} 的 UUID"

        merged_player = PlayerStats(
            name=output_player,
            uuid=output_uuid,
            data_version=merged.get("DataVersion"),
            stats=merged.get("stats", {}),
        )

        if not self.stats_service.save_player_stats(merged_player):
            return False, "保存合并数据失败"

        for player in input_players:
            if player != output_player:
                self.stats_service.delete_player_stats(player)

        return True, f"成功将 {', '.join(input_players)} 的数据合并到 {output_player}"

    def _merge_player_stats(
        self, stats_list: list[PlayerStats]
    ) -> dict:
        """合并多个玩家的统计数据"""
        merged_stats: dict[str, dict[str, int]] = {}
        data_version = None

        for player_stats in stats_list:
            if player_stats.data_version is not None:
                data_version = player_stats.data_version

            for category, items in player_stats.stats.items():
                if category not in merged_stats:
                    merged_stats[category] = {}
                for item, value in items.items():
                    merged_stats[category][item] = (
                        merged_stats[category].get(item, 0) + value
                    )

        result = {"stats": merged_stats}
        if data_version is not None:
            result["DataVersion"] = data_version
        return result
