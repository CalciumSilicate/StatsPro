# -*- coding: utf-8 -*-
"""计分板服务"""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from .config import PluginConfig
from .constants import PLUGIN_ID, SCOREBOARD_NAME
from .models import Preset
from .stats_service import StatsService
from .utils import generate_unique_abbreviations

if TYPE_CHECKING:
    from mcdreforged.api.all import ServerInterface

logger = logging.getLogger(PLUGIN_ID)


class ScoreboardService:
    """计分板服务"""

    def __init__(self, config: PluginConfig, stats_service: StatsService):
        self.config = config
        self.stats_service = stats_service
        self.current_display: str = SCOREBOARD_NAME

    def create_scoreboard(
        self,
        server: ServerInterface,
        category: str,
        item: str,
        display_name: str | None = None,
        inner_name: str | None = None,
        include_bots: bool = False,
    ) -> dict[str, int]:
        """创建计分板"""
        inner_name = inner_name or SCOREBOARD_NAME
        display_name = display_name or f"§e{category}§r.§b{item}§r"

        ranking = self.stats_service.get_ranking(
            category=category,
            item=item,
            include_bots=include_bots,
        )

        server.execute(f"scoreboard objectives remove {inner_name}")

        display_json = json.dumps({"text": display_name})
        server.execute(
            f"scoreboard objectives add {inner_name} "
            f"minecraft.{category}:minecraft.{item} {display_json}"
        )

        for name, value in ranking.items():
            server.execute(
                f"scoreboard players set {name} {inner_name} {value}"
            )

        return ranking

    def set_display(
        self, server: ServerInterface, scoreboard_name: str = ""
    ) -> None:
        """设置侧边栏显示的计分板"""
        if scoreboard_name:
            server.execute(f"scoreboard objectives setdisplay sidebar {scoreboard_name}")
            self.current_display = scoreboard_name
        else:
            server.execute("scoreboard objectives setdisplay sidebar")
            self.current_display = ""

    def remove_scoreboard(
        self, server: ServerInterface, inner_name: str
    ) -> None:
        """移除计分板"""
        server.execute(f"scoreboard objectives remove {inner_name}")

    def create_sum_scoreboard(
        self,
        server: ServerInterface,
        preset: Preset,
        include_bots: bool = False,
    ) -> dict[str, int]:
        """创建加和计分板"""
        self._init_preset_abbreviations(preset)

        commands = self._generate_scoreboard_commands(preset)
        all_scores: dict[str, int] = {}

        for category, items in preset.items.items():
            for item, abbr in items.items():
                inner_name = f"{preset.prefix_true}_{abbr}"
                scores = self.create_scoreboard(
                    server,
                    category=category,
                    item=item,
                    inner_name=inner_name,
                    include_bots=include_bots,
                )
                for player, score in scores.items():
                    all_scores[player] = all_scores.get(player, 0) + score

        for cmd in commands["creating"]:
            server.execute(cmd)

        for player, total in all_scores.items():
            server.execute(
                f"scoreboard players set {player} "
                f"{preset.prefix_dummy}_total {total}"
            )

        self._create_datapack(preset)
        server.execute("reload")

        return all_scores

    def remove_sum_scoreboard(
        self, server: ServerInterface, preset: Preset
    ) -> None:
        """移除加和计分板"""
        commands = self._generate_scoreboard_commands(preset)

        for cmd in commands["removing"]:
            server.execute(cmd)

        datapack_path = self._get_datapack_path(preset)
        if datapack_path.exists():
            shutil.rmtree(datapack_path)

        server.execute("reload")

    def _init_preset_abbreviations(self, preset: Preset) -> None:
        """初始化预设的缩写"""
        all_items = []
        for category, items in preset.items.items():
            for item in items:
                all_items.append(item)

        if not all_items:
            return

        abbrs = generate_unique_abbreviations(*all_items)
        item_abbr_map = dict(zip(sorted(all_items), abbrs))

        for category in preset.items:
            for item in preset.items[category]:
                preset.items[category][item] = item_abbr_map.get(item, item[:6])

    def _generate_scoreboard_commands(
        self, preset: Preset
    ) -> dict[str, list[str]]:
        """生成计分板相关命令"""
        commands: dict[str, list[str]] = {
            "creating": [],
            "removing": [],
            "true_names": [],
            "dummy_names": [],
        }

        abbr_list = []
        for category, items in preset.items.items():
            for item, abbr in items.items():
                true_name = f"{preset.prefix_true}_{abbr}"
                commands["removing"].append(
                    f"scoreboard objectives remove {true_name}"
                )
                commands["true_names"].append(true_name)
                abbr_list.append(abbr)

        abbr_list_sorted = sorted(abbr_list)
        dummy_abbrs = []
        for i in range(len(abbr_list_sorted) - 1):
            dummy_abbrs.append(abbr_list_sorted[i] + abbr_list_sorted[i + 1])
        dummy_abbrs.extend(["minor", "total"])

        for abbr in dummy_abbrs:
            dummy_name = f"{preset.prefix_dummy}_{abbr}"
            commands["creating"].append(
                f"scoreboard objectives add {dummy_name} dummy"
            )
            commands["removing"].append(
                f"scoreboard objectives remove {dummy_name}"
            )
            commands["dummy_names"].append(dummy_name)

        total_name = f"{preset.prefix_dummy}_total"
        commands["creating"].append(
            f"scoreboard objectives setdisplay sidebar {total_name}"
        )
        display_json = json.dumps({"text": preset.display_name})
        commands["creating"].append(
            f"scoreboard objectives modify {total_name} displayname {display_json}"
        )

        return commands

    def _generate_datapack_commands(self, preset: Preset) -> list[str]:
        """生成数据包命令"""
        commands = self._generate_scoreboard_commands(preset)
        true_names = commands["true_names"]
        dummy_names = commands["dummy_names"]

        if not true_names or not dummy_names:
            return []

        total = dummy_names.pop()
        minor = dummy_names.pop()

        def cmd(target: str, operation: str, source: str) -> str:
            return (
                f"execute as @a run scoreboard players operation "
                f"@s {target} {operation} @s {source}"
            )

        result = []
        for i, dummy in enumerate(dummy_names):
            if i == 0:
                result.append(cmd(dummy, "=", true_names[i]))
                if len(true_names) > 1:
                    result.append(cmd(dummy, "+=", true_names[i + 1]))
            else:
                result.append(cmd(dummy, "=", dummy_names[i - 1]))
                if i + 1 < len(true_names):
                    result.append(cmd(dummy, "+=", true_names[i + 1]))

        if dummy_names:
            result.append(cmd(minor, "=", dummy_names[-1]))
        result.append(cmd(total, "=", minor))

        return result

    def _get_datapack_path(self, preset: Preset) -> Path:
        """获取数据包路径"""
        datapack_name = f"statspro_{preset.name}"
        return self.config.paths.datapacks_path / datapack_name

    def _create_datapack(self, preset: Preset) -> None:
        """创建数据包"""
        datapack_path = self._get_datapack_path(preset)
        # DataVersion > 3953 使用 function，否则使用 functions
        folder_name = "function" if self.config.use_function_folder else "functions"
        function_path = datapack_path / "data" / "statspro" / folder_name
        tags_path = datapack_path / "data" / "minecraft" / "tags" / folder_name

        if datapack_path.exists():
            shutil.rmtree(datapack_path)

        function_path.mkdir(parents=True, exist_ok=True)
        tags_path.mkdir(parents=True, exist_ok=True)

        commands = self._generate_datapack_commands(preset)
        tick_file = function_path / "tick.mcfunction"
        tick_file.write_text("\n".join(commands), encoding="utf-8")

        tick_json = tags_path / "tick.json"
        tick_json.write_text(
            json.dumps({"values": ["statspro:tick"]}, indent=4),
            encoding="utf-8",
        )

        pack_mcmeta = datapack_path / "pack.mcmeta"
        pack_mcmeta.write_text(
            json.dumps({"pack": {"pack_format": 4, "description": "StatsPro"}}, indent=4),
            encoding="utf-8",
        )
