# -*- coding: utf-8 -*-
"""数据模型定义"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PlayerStats:
    """玩家统计数据模型"""

    name: str
    uuid: str
    data_version: int | None = None
    stats: dict[str, dict[str, int]] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: Path, name: str, uuid: str) -> PlayerStats:
        """从 JSON 文件加载玩家统计数据"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls(
            name=name,
            uuid=uuid,
            data_version=data.get("DataVersion"),
            stats=data.get("stats", {}),
        )

    def get_score(self, category: str, item: str) -> int | None:
        """获取指定类别和物品的分数"""
        cat_key = _ensure_prefix(category)
        item_key = _ensure_prefix(item)
        try:
            return self.stats[cat_key][item_key]
        except KeyError:
            return None

    def get_category_scores(self, category: str) -> dict[str, int]:
        """获取某类别下所有物品的分数"""
        cat_key = _ensure_prefix(category)
        return dict(self.stats.get(cat_key, {}))

    def get_item_scores(self, item: str) -> dict[str, int]:
        """获取某物品在所有类别中的分数"""
        item_key = _ensure_prefix(item)
        result = {}
        for cat, items in self.stats.items():
            if item_key in items:
                result[cat] = items[item_key]
        return result

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        result: dict[str, Any] = {"stats": self.stats}
        if self.data_version is not None:
            result["DataVersion"] = self.data_version
        return result


@dataclass
class Preset:
    """预设配置模型"""

    name: str
    display_name: str
    prefix_dummy: str
    prefix_true: str
    items: dict[str, dict[str, str]] = field(default_factory=dict)

    def add_item(self, category: str, item: str) -> bool:
        """添加计分项到预设"""
        if category not in self.items:
            self.items[category] = {}
        if item in self.items[category]:
            return False
        self.items[category][item] = ""
        return True

    def remove_item(self, category: str, item: str) -> bool:
        """从预设移除计分项"""
        if category in self.items and item in self.items[category]:
            del self.items[category][item]
            if not self.items[category]:
                del self.items[category]
            return True
        return False

    def clear_items(self) -> None:
        """清空所有计分项"""
        self.items.clear()

    def get_all_items(self) -> list[tuple[str, str]]:
        """获取所有计分项列表 [(category, item), ...]"""
        result = []
        for cat, items in self.items.items():
            for item in items:
                result.append((cat, item))
        return result

    def to_dict(self) -> dict[str, Any]:
        """转换为配置字典格式"""
        return {
            "name": self.display_name,
            "prefix_dummy": self.prefix_dummy,
            "prefix_true": self.prefix_true,
            "list": self.items,
        }

    @classmethod
    def from_dict(cls, key: str, data: dict[str, Any]) -> Preset:
        """从配置字典创建预设"""
        return cls(
            name=key,
            display_name=data.get("name", key),
            prefix_dummy=data.get("prefix_dummy", key[0]),
            prefix_true=data.get("prefix_true", key[0] + "t"),
            items=data.get("list", {}),
        )


@dataclass
class GenRecord:
    """生成记录模型"""

    time: str
    name: str
    note: str | None
    path: str
    abs_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "time": self.time,
            "name": self.name,
            "note": self.note,
            "path": self.path,
            "abs_path": self.abs_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GenRecord:
        return cls(
            time=data["time"],
            name=data["name"],
            note=data.get("note"),
            path=data["path"],
            abs_path=data["abs_path"],
        )


@dataclass
class MergeConfig:
    """合并配置模型"""

    input_players: list[str] = field(default_factory=list)
    output_player: str = ""

    def add_input(self, player: str) -> None:
        if player not in self.input_players:
            self.input_players.append(player)

    def remove_input(self, player: str) -> bool:
        if player in self.input_players:
            self.input_players.remove(player)
            return True
        return False

    def clear_inputs(self) -> None:
        self.input_players.clear()

    def set_output(self, player: str) -> None:
        self.output_player = player

    def is_valid(self) -> bool:
        return bool(self.input_players and self.output_player)


def _ensure_prefix(value: str) -> str:
    """确保值带有 minecraft: 前缀"""
    if value.startswith("minecraft:"):
        return value
    return f"minecraft:{value}"


def strip_prefix(value: str) -> str:
    """移除 minecraft: 前缀"""
    if value.startswith("minecraft:"):
        return value[10:]
    return value
