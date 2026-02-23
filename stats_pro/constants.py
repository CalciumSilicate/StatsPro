# -*- coding: utf-8 -*-
"""常量定义模块"""

from enum import Enum
from typing import Final

PLUGIN_ID: Final[str] = "stats_pro"
PLUGIN_VERSION: Final[str] = "2.0.0"
PLUGIN_AUTHOR: Final[str] = "CalciumSilicate"

COMMAND_PREFIX: Final[str] = "!!sp"
LEGACY_PREFIXES: Final[tuple[str, ...]] = ("!!stats",)

SCOREBOARD_NAME: Final[str] = "StatsPro"
MINECRAFT_PREFIX: Final[str] = "minecraft:"


class Permission(Enum):
    GUEST = 0
    USER = 1
    HELPER = 2
    ADMIN = 3
    OWNER = 4


class StatCategory(Enum):
    KILLED_BY = "killed_by"
    KILLED = "killed"
    CUSTOM = "custom"
    MINED = "mined"
    USED = "used"
    DROPPED = "dropped"
    BROKEN = "broken"
    PICKED_UP = "picked_up"
    CRAFTED = "crafted"


class GenMode(Enum):
    SUM = "sum"
    RECORD = "record"
    MINUS = "minus"


NETHERITE_TOOLS: Final[tuple[str, ...]] = (
    "netherite_pickaxe",
    "netherite_axe",
    "netherite_sword",
    "netherite_shovel",
    "netherite_hoe",
)

DEFAULT_TOOLS: Final[tuple[str, ...]] = (
    "diamond_axe",
    "diamond_sword",
    "diamond_pickaxe",
    "diamond_shovel",
    "diamond_hoe",
    "iron_axe",
    "iron_sword",
    "iron_pickaxe",
    "iron_shovel",
    "iron_hoe",
    "golden_axe",
    "golden_sword",
    "golden_pickaxe",
    "golden_shovel",
    "golden_hoe",
    "wooden_axe",
    "wooden_sword",
    "wooden_pickaxe",
    "wooden_shovel",
    "wooden_hoe",
    "stone_axe",
    "stone_sword",
    "stone_pickaxe",
    "stone_shovel",
    "stone_hoe",
    "shears",
)

BOT_KEYWORDS: Final[tuple[str, ...]] = ("bot", "b_", "steve", "alex", "dig")
