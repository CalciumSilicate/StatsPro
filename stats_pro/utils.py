# -*- coding: utf-8 -*-
"""工具函数模块"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import TYPE_CHECKING

from mcdreforged.api.rtext import RAction, RText, RTextList

from .constants import BOT_KEYWORDS, MINECRAFT_PREFIX

if TYPE_CHECKING:
    from mcdreforged.api.all import Info, ServerInterface


def get_timestamp() -> str:
    """获取当前时间戳字符串"""
    return time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())


def ensure_prefix(value: str) -> str:
    """确保值带有 minecraft: 前缀"""
    if value.startswith(MINECRAFT_PREFIX):
        return value
    return f"{MINECRAFT_PREFIX}{value}"


def strip_prefix(value: str) -> str:
    """移除 minecraft: 前缀"""
    if value.startswith(MINECRAFT_PREFIX):
        return value[len(MINECRAFT_PREFIX) :]
    return value


def is_bot_player(name: str) -> bool:
    """判断是否为机器人玩家"""
    name_lower = name.lower()
    return any(keyword in name_lower for keyword in BOT_KEYWORDS)


def normalize_uuid(value: str) -> str:
    """标准化 UUID，便于比较不同格式的 UUID。"""
    return value.replace("-", "").lower()


def is_uuid_fallback_name(name: str, uuid: str) -> bool:
    """判断名称是否为自动生成的 UUID 前 8 位临时名。"""
    return name.lower() == normalize_uuid(uuid)[:8]


def generate_abbreviation(item: str) -> str:
    """生成物品缩写"""
    if "_" in item:
        return "".join(word[0] for word in item.split("_"))[:6]
    return item[:6]


def generate_unique_abbreviations(*items: str) -> list[str]:
    """生成唯一的缩写列表"""
    items = tuple(sorted(items))
    abbrs = [generate_abbreviation(item) for item in items]

    if len(abbrs) == len(set(abbrs)):
        return abbrs

    chars = "abcdefghijklmnopqrstuvwxyz" * 2
    for i in range(len(abbrs) - 1):
        if abbrs[i] == abbrs[i + 1]:
            last_char = abbrs[i + 1][-1]
            next_char_idx = chars.index(last_char.lower()) + 1
            abbrs[i + 1] = abbrs[i + 1][:-1] + chars[next_char_idx]

    return generate_unique_abbreviations(*abbrs)


class MessageBuilder:
    """消息构建器"""

    def __init__(self, plugin_name: str = "StatsPro"):
        self.plugin_name = plugin_name
        self.prefix = f"§r[§b{plugin_name}§r]"

    def send(
        self,
        server: ServerInterface,
        info: Info,
        message: str | RTextList,
        prefix: str | None = None,
        broadcast: bool = False,
    ) -> None:
        """发送消息给玩家或控制台"""
        if not info.is_user:
            return

        msg_prefix = prefix if prefix is not None else self.prefix

        if isinstance(message, RTextList):
            lines = [message]
        else:
            lines = str(message).splitlines()

        for line in lines:
            full_msg = f"{msg_prefix}{line}" if msg_prefix else line

            if info.is_player:
                if broadcast:
                    server.say(full_msg)
                else:
                    server.tell(info.player, full_msg)
            else:
                server.reply(info, full_msg)

    def broadcast(
        self,
        server: ServerInterface,
        info: Info,
        message: str | RTextList,
        prefix: str | None = None,
    ) -> None:
        """广播消息"""
        self.send(server, info, message, prefix, broadcast=True)


def clickable_text(
    text: str,
    hover: str = "",
    command: str = "",
    action: RAction = RAction.run_command,
) -> RText:
    """创建可点击的文本"""
    rtext = RText(text)
    if hover:
        rtext.set_hover_text(hover)
    if command:
        rtext.set_click_event(action, command)
    return rtext


def load_uuid_mapping(uuid_file: Path) -> dict[str, str]:
    """加载 UUID 映射 {name: uuid}"""
    if not uuid_file.exists():
        return {}
    try:
        with open(uuid_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def load_usercache(usercache_file: Path) -> dict[str, str]:
    """
    从服务器的 usercache.json 加载 UUID 映射
    usercache.json 格式: [{"name": "PlayerName", "uuid": "xxx-xxx", "expiresOn": "..."}, ...]
    返回: {name: uuid}
    """
    if not usercache_file.exists():
        return {}
    try:
        with open(usercache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        mapping = {}
        for entry in data:
            if "name" in entry and "uuid" in entry:
                mapping[entry["name"]] = entry["uuid"]
        return mapping
    except (json.JSONDecodeError, OSError):
        return {}


def build_uuid_mapping_from_stats(stats_path: Path, usercache_file: Path) -> dict[str, str]:
    """
    构建 UUID 映射，优先使用 usercache.json，
    对于 usercache 中没有的 UUID，使用 UUID 本身作为临时名称
    
    Args:
        stats_path: stats 文件夹路径
        usercache_file: usercache.json 文件路径
    
    Returns:
        {name: uuid} 映射
    """
    mapping = {}
    
    # 首先从 usercache.json 加载
    usercache_mapping = load_usercache(usercache_file)
    # 反转为 {uuid: name}，比较时忽略横线与大小写差异
    uuid_to_name_map = {normalize_uuid(v): k for k, v in usercache_mapping.items()}
    
    # 遍历 stats 文件夹中的所有 json 文件
    if stats_path.exists():
        for stats_file in stats_path.glob("*.json"):
            uuid = stats_file.stem  # 文件名（不含扩展名）就是 UUID
            
            if normalize_uuid(uuid) in uuid_to_name_map:
                # usercache 中有这个 UUID 的名称
                name = uuid_to_name_map[normalize_uuid(uuid)]
            else:
                # usercache 中没有，使用 UUID 作为临时名称
                # 去掉 UUID 中的横线，取前8位作为显示名
                name = normalize_uuid(uuid)[:8]
            
            mapping[name] = uuid
    
    return mapping


def merge_uuid_mappings(
    auto_mapping: dict[str, str],
    manual_mapping: dict[str, str],
) -> dict[str, str]:
    """
    合并 UUID 映射并按 UUID 去重。

    手动配置优先，但自动生成的 UUID 前 8 位临时名不会覆盖真实名称。
    这样用户补全真实名称后，旧的短 ID 条目会被自动清理。
    """
    selected: dict[str, tuple[str, str, bool]] = {}

    def put(name: str, uuid: str, is_manual: bool) -> None:
        uuid_key = normalize_uuid(uuid)
        if not uuid_key:
            return

        current = selected.get(uuid_key)
        candidate_is_fallback = is_uuid_fallback_name(name, uuid)
        if current is None:
            selected[uuid_key] = (name, uuid, is_manual)
            return

        current_name, current_uuid, current_is_manual = current
        current_is_fallback = is_uuid_fallback_name(current_name, current_uuid)

        if current_is_fallback and not candidate_is_fallback:
            selected[uuid_key] = (name, uuid, is_manual)
            return

        if candidate_is_fallback and not current_is_fallback:
            return

        if is_manual and not current_is_manual:
            selected[uuid_key] = (name, uuid, is_manual)

    for name, uuid in auto_mapping.items():
        put(name, uuid, False)

    for name, uuid in manual_mapping.items():
        put(name, uuid, True)

    return {name: uuid for name, uuid, _ in selected.values()}


def save_uuid_mapping(uuid_file: Path, mapping: dict[str, str]) -> None:
    """保存 UUID 映射"""
    uuid_file.parent.mkdir(parents=True, exist_ok=True)
    with open(uuid_file, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)


def name_to_uuid(mapping: dict[str, str], name: str) -> str | None:
    """根据名称获取 UUID"""
    return mapping.get(name)


def uuid_to_name(mapping: dict[str, str], uuid: str) -> str | None:
    """根据 UUID 获取名称"""
    for name, uid in mapping.items():
        if uid == uuid:
            return name
    return None
