# -*- coding: utf-8 -*-
"""玩家统计数据服务"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .cache import StatsCache, get_stats_cache
from .config import PluginConfig
from .constants import PLUGIN_ID
from .models import PlayerStats
from .utils import ensure_prefix, is_bot_player, load_uuid_mapping, strip_prefix

if TYPE_CHECKING:
    pass

logger = logging.getLogger(PLUGIN_ID)


class StatsService:
    """玩家统计数据服务"""

    def __init__(self, config: PluginConfig, cache_ttl: float = 30.0):
        self.config = config
        self._uuid_mapping: dict[str, str] = {}
        self._players_stats: dict[str, PlayerStats] = {}
        self._cache: StatsCache = get_stats_cache(ttl=cache_ttl)
        self._reload_uuid_mapping()

    def _reload_uuid_mapping(self) -> None:
        """重新加载 UUID 映射"""
        self._uuid_mapping = load_uuid_mapping(self.config.paths.uuid_file)

    @property
    def uuid_mapping(self) -> dict[str, str]:
        """获取 UUID 映射"""
        return self._uuid_mapping

    def get_uuid(self, name: str) -> str | None:
        """根据玩家名获取 UUID"""
        return self._uuid_mapping.get(name)

    def get_name(self, uuid: str) -> str | None:
        """根据 UUID 获取玩家名"""
        for name, uid in self._uuid_mapping.items():
            if uid == uuid:
                return name
        return None

    def convert_to_name(self, identifier: str) -> str:
        """将标识符（名称或UUID）转换为名称"""
        if identifier in self._uuid_mapping:
            return identifier
        name = self.get_name(identifier)
        return name if name else identifier

    def reload_all_stats(self) -> dict[str, PlayerStats]:
        """重新加载所有玩家的统计数据"""
        self._reload_uuid_mapping()
        self._players_stats.clear()
        self._cache.invalidate_all()

        stats_path = self.config.paths.stats_path
        if not stats_path.exists():
            logger.warning(f"Stats path does not exist: {stats_path}")
            return self._players_stats

        for name, uuid in self._uuid_mapping.items():
            file_path = stats_path / f"{uuid}.json"
            if file_path.exists():
                try:
                    self._players_stats[name] = PlayerStats.from_file(
                        file_path, name, uuid
                    )
                    self._cache.set_player_stats(name, self._players_stats[name].stats)

                    # 检测并更新 DataVersion
                    if self._players_stats[name].data_version is not None:
                        self.config.update_data_version(self._players_stats[name].data_version)
                except (json.JSONDecodeError, OSError) as e:
                    logger.warning(f"Failed to load stats for {name}: {e}")

        # 根据检测到的版本更新默认预设工具
        self.config.update_default_preset_tools()

        return self._players_stats

    def get_player_stats(self, name: str, reload: bool = False) -> PlayerStats | None:
        """获取单个玩家的统计数据"""
        if reload or not self._players_stats:
            self.reload_all_stats()

        name = self.convert_to_name(name)
        return self._players_stats.get(name)

    def get_all_stats(self, reload: bool = False) -> dict[str, PlayerStats]:
        """获取所有玩家的统计数据"""
        if reload or not self._players_stats:
            self.reload_all_stats()
        return self._players_stats

    def get_score(
        self, player: str, category: str, item: str
    ) -> int | None:
        """获取玩家指定类别和物品的分数"""
        stats = self.get_player_stats(player)
        if stats is None:
            return None
        return stats.get_score(category, item)

    def get_category_scores(
        self, player: str, category: str
    ) -> dict[str, int] | None:
        """获取玩家某类别下所有物品的分数"""
        stats = self.get_player_stats(player)
        if stats is None:
            return None
        return stats.get_category_scores(category)

    def get_item_scores(
        self, player: str, item: str
    ) -> dict[str, int] | None:
        """获取玩家某物品在所有类别中的分数"""
        stats = self.get_player_stats(player)
        if stats is None:
            return None
        return stats.get_item_scores(item)

    def get_ranking(
        self,
        category: str | None = None,
        item: str | None = None,
        include_bots: bool = False,
        limit: int = 15,
    ) -> dict[str, int]:
        """获取排行榜数据"""
        cached = self._cache.get_ranking(category, item, include_bots)
        if cached is not None:
            return dict(sorted(cached.items(), key=lambda x: x[1], reverse=True)[:limit])

        self.reload_all_stats()
        result: dict[str, int] = {}

        for name, stats in self._players_stats.items():
            if not include_bots and is_bot_player(name):
                continue

            try:
                if category and item:
                    score = stats.get_score(category, item)
                    if score is not None:
                        result[name] = score
                elif category:
                    cat_scores = stats.get_category_scores(category)
                    for item_key, score in cat_scores.items():
                        key = f"{name}.{strip_prefix(item_key)}"
                        result[key] = score
                elif item:
                    item_scores = stats.get_item_scores(item)
                    for cat_key, score in item_scores.items():
                        key = f"{name}.{strip_prefix(cat_key)}"
                        result[key] = score
            except (KeyError, TypeError):
                continue

        self._cache.set_ranking(result, category, item, include_bots)

        sorted_result = dict(
            sorted(result.items(), key=lambda x: x[1], reverse=True)[:limit]
        )
        return sorted_result

    def sum_all_stats(
        self, players: list[str] | None = None
    ) -> dict[str, Any]:
        """汇总所有玩家的统计数据"""
        players_key = ",".join(sorted(players)) if players else "all"
        cached = self._cache.get_sum(players_key)
        if cached is not None:
            return cached

        self.reload_all_stats()

        stats_to_sum = []
        data_version = None

        for name, player_stats in self._players_stats.items():
            if players is not None and name not in players:
                continue
            stats_to_sum.append(player_stats.stats)
            if player_stats.data_version is not None:
                data_version = player_stats.data_version

        result = self._merge_stats(stats_to_sum, data_version)
        self._cache.set_sum(players_key, result)
        return result

    def _merge_stats(
        self, stats_list: list[dict[str, dict[str, int]]], data_version: int | None
    ) -> dict[str, Any]:
        """合并统计数据"""
        merged: dict[str, dict[str, int]] = {}

        for stats in stats_list:
            for category, items in stats.items():
                if category not in merged:
                    merged[category] = {}
                for item, value in items.items():
                    merged[category][item] = merged[category].get(item, 0) + value

        result: dict[str, Any] = {"stats": merged}
        if data_version is not None:
            result["DataVersion"] = data_version
        return result

    def diff_stats(
        self, first: dict[str, Any], second: dict[str, Any]
    ) -> dict[str, dict[str, int]]:
        """计算两个统计数据的差值"""
        first_stats = first.get("stats", first)
        second_stats = second.get("stats", second)

        result: dict[str, dict[str, int]] = {}

        all_categories = set(first_stats.keys()) | set(second_stats.keys())
        for category in all_categories:
            first_items = first_stats.get(category, {})
            second_items = second_stats.get(category, {})
            all_items = set(first_items.keys()) | set(second_items.keys())

            for item in all_items:
                diff = abs(
                    first_items.get(item, 0) - second_items.get(item, 0)
                )
                if diff > 0:
                    if category not in result:
                        result[category] = {}
                    result[category][item] = diff

        return result

    def save_player_stats(self, player_stats: PlayerStats) -> bool:
        """保存玩家统计数据到文件"""
        try:
            file_path = self.config.paths.stats_path / f"{player_stats.uuid}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(player_stats.to_dict(), f, indent=2)
            self._cache.invalidate_player(player_stats.name)
            return True
        except OSError as e:
            logger.error(f"Failed to save stats for {player_stats.name}: {e}")
            return False

    def delete_player_stats(self, name: str) -> bool:
        """删除玩家统计文件"""
        uuid = self.get_uuid(name)
        if uuid is None:
            return False

        file_path = self.config.paths.stats_path / f"{uuid}.json"
        if file_path.exists():
            try:
                file_path.unlink()
                self._cache.invalidate_player(name)
                return True
            except OSError as e:
                logger.error(f"Failed to delete stats for {name}: {e}")
        return False

    @property
    def cache_stats(self) -> dict:
        """获取缓存统计信息"""
        return self._cache.stats
