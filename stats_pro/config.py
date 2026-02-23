# -*- coding: utf-8 -*-
"""配置管理模块"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .constants import (
    COPPER_TOOLS,
    DATA_VERSION_COPPER,
    DATA_VERSION_FUNCTION_FOLDER,
    DATA_VERSION_GAMERULE_SNAKE,
    DATA_VERSION_NETHERITE,
    DEFAULT_TOOLS,
    NETHERITE_TOOLS,
    PLUGIN_ID,
    Permission,
)
from .models import GenRecord, MergeConfig, Preset

logger = logging.getLogger(PLUGIN_ID)


@dataclass
class PathConfig:
    """路径配置"""

    mcdr_root: Path = field(default_factory=lambda: Path("."))

    @property
    def server_path(self) -> Path:
        return self.mcdr_root / "server"

    @property
    def plugin_path(self) -> Path:
        return self.mcdr_root / "plugins"

    @property
    def world_path(self) -> Path:
        return self.server_path / "world"

    @property
    def stats_path(self) -> Path:
        return self.world_path / "stats"

    @property
    def datapacks_path(self) -> Path:
        return self.world_path / "datapacks"

    @property
    def config_folder(self) -> Path:
        return self.mcdr_root / "config" / "StatsPro"

    @property
    def config_file(self) -> Path:
        return self.config_folder / "config.json"

    @property
    def uuid_file(self) -> Path:
        return self.config_folder / "uuid.json"

    @property
    def usercache_file(self) -> Path:
        return self.server_path / "usercache.json"

    def gen_folder(self, mode: str) -> Path:
        return self.config_folder / mode


@dataclass
class PluginConfig:
    """插件配置"""

    paths: PathConfig = field(default_factory=PathConfig)
    permission_required: Permission = Permission.HELPER

    # 运行时数据
    presets: dict[str, Preset] = field(default_factory=dict)
    gen_records: dict[str, dict[str, GenRecord]] = field(default_factory=dict)
    merge_config: MergeConfig = field(default_factory=MergeConfig)
    _detected_data_version: int | None = None

    def __post_init__(self) -> None:
        self._init_gen_records()

    @property
    def has_netherite(self) -> bool:
        """是否支持下界合金工具 (DataVersion > 2504)"""
        if self._detected_data_version is None:
            return True  # 默认支持
        return self._detected_data_version > DATA_VERSION_NETHERITE

    @property
    def has_copper(self) -> bool:
        """是否支持铜工具 (DataVersion > 4534)"""
        if self._detected_data_version is None:
            return False
        return self._detected_data_version > DATA_VERSION_COPPER

    @property
    def use_function_folder(self) -> bool:
        """是否使用 function 文件夹名 (DataVersion > 3953)，否则用 functions"""
        if self._detected_data_version is None:
            return True  # 默认使用新版
        return self._detected_data_version > DATA_VERSION_FUNCTION_FOLDER

    @property
    def use_snake_case_gamerule(self) -> bool:
        """是否使用 send_command_feedback (DataVersion > 4659)，否则用 sendCommandFeedback"""
        if self._detected_data_version is None:
            return True  # 默认使用新版
        return self._detected_data_version > DATA_VERSION_GAMERULE_SNAKE

    def get_command_feedback_rule(self) -> str:
        """获取 gamerule 名称"""
        return "send_command_feedback" if self.use_snake_case_gamerule else "sendCommandFeedback"

    def update_data_version(self, version: int) -> None:
        """更新检测到的 DataVersion"""
        if self._detected_data_version is None or version > self._detected_data_version:
            self._detected_data_version = version
            logger.info(f"Detected DataVersion: {version} (netherite={self.has_netherite}, copper={self.has_copper})")

    def _init_gen_records(self) -> None:
        """初始化生成记录"""
        for mode in ("sum", "record", "minus"):
            if mode not in self.gen_records:
                self.gen_records[mode] = {}

    @classmethod
    def load(cls, config_path: Path | None = None) -> PluginConfig:
        """从文件加载配置"""
        paths = PathConfig()
        if config_path:
            paths = PathConfig(mcdr_root=config_path.parent.parent.parent)

        config = cls(paths=paths)
        config._ensure_directories()

        config_file = paths.config_file
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                config._load_from_dict(data)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load config: {e}, using defaults")
                config._load_defaults()
        else:
            config._load_defaults()

        return config

    def _load_from_dict(self, data: dict[str, Any]) -> None:
        """从字典加载配置"""
        # 加载预设
        presets_data = data.get("presuppositions", {})
        for key, preset_data in presets_data.items():
            self.presets[key] = Preset.from_dict(key, preset_data)

        # 加载生成记录
        gen_list = data.get("gen_list", {})
        for mode in ("sum", "record", "minus"):
            mode_data = gen_list.get(mode, {})
            self.gen_records[mode] = {
                k: GenRecord.from_dict(v) for k, v in mode_data.items()
            }

        # 加载合并配置
        merge_data = data.get("merge_list", {})
        self.merge_config = MergeConfig(
            input_players=merge_data.get("input", []),
            output_player=merge_data.get("output", ""),
        )

    def _load_defaults(self) -> None:
        """加载默认配置"""
        default_items: dict[str, dict[str, str]] = {"used": {}}
        tools = list(DEFAULT_TOOLS)

        for tool in tools:
            default_items["used"][tool] = ""

        self.presets["default"] = Preset(
            name="default",
            display_name="§c§l挖掘总榜§r",
            prefix_dummy="d",
            prefix_true="dt",
            items=default_items,
        )

    def update_default_preset_tools(self) -> None:
        """根据 DataVersion 更新默认预设的工具列表"""
        if "default" not in self.presets:
            return

        preset = self.presets["default"]
        if "used" not in preset.items:
            preset.items["used"] = {}

        # 添加下界合金工具
        if self.has_netherite:
            for tool in NETHERITE_TOOLS:
                if tool not in preset.items["used"]:
                    preset.items["used"][tool] = ""

        # 添加铜工具
        if self.has_copper:
            for tool in COPPER_TOOLS:
                if tool not in preset.items["used"]:
                    preset.items["used"][tool] = ""

    def _ensure_directories(self) -> None:
        """确保必要的目录存在"""
        for mode in ("sum", "record", "minus"):
            self.paths.gen_folder(mode).mkdir(parents=True, exist_ok=True)

    def save(self) -> None:
        """保存配置到文件"""
        self._ensure_directories()

        data = {
            "presuppositions": {
                key: preset.to_dict() for key, preset in self.presets.items()
            },
            "gen_list": {
                mode: {k: v.to_dict() for k, v in records.items()}
                for mode, records in self.gen_records.items()
            },
            "merge_list": {
                "input": self.merge_config.input_players,
                "output": self.merge_config.output_player,
            },
        }

        with open(self.paths.config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def get_preset(self, name: str) -> Preset | None:
        """获取预设"""
        return self.presets.get(name)

    def add_preset(
        self,
        name: str,
        display_name: str | None = None,
        prefix_dummy: str | None = None,
        prefix_true: str | None = None,
    ) -> Preset | None:
        """添加新预设"""
        if name in self.presets:
            return None

        preset = Preset(
            name=name,
            display_name=display_name or name,
            prefix_dummy=prefix_dummy or name[0],
            prefix_true=prefix_true or f"{name[0]}t",
        )
        self.presets[name] = preset
        return preset

    def remove_preset(self, name: str) -> bool:
        """移除预设"""
        if name == "default" or name not in self.presets:
            return False
        del self.presets[name]
        return True

    def add_gen_record(self, mode: str, record: GenRecord) -> None:
        """添加生成记录"""
        if mode not in self.gen_records:
            self.gen_records[mode] = {}
        self.gen_records[mode][record.time] = record

    def remove_gen_record(self, mode: str, time: str) -> GenRecord | None:
        """移除生成记录"""
        if mode in self.gen_records and time in self.gen_records[mode]:
            return self.gen_records[mode].pop(time)
        return None
