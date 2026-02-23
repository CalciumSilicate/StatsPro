# -*- coding: utf-8 -*-
"""命令处理模块 - 使用 MCDR 命令树"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from mcdreforged.api.command import (
    CommandSource,
    GreedyText,
    Integer,
    Literal,
    Number,
    QuotableText,
    Text,
)
from mcdreforged.api.rtext import RAction, RText, RTextList

from .constants import COMMAND_PREFIX, LEGACY_PREFIXES, PLUGIN_ID, Permission
from .i18n import t
from .utils import MessageBuilder, clickable_text, strip_prefix

if TYPE_CHECKING:
    from mcdreforged.api.all import Info, PluginServerInterface, ServerInterface

    from .plugin import StatsProPlugin


class CommandHandler:
    """命令处理器"""

    def __init__(self, plugin: StatsProPlugin):
        self.plugin = plugin
        self.msg = MessageBuilder()

    @property
    def config(self):
        return self.plugin.config

    @property
    def stats_service(self):
        return self.plugin.stats_service

    @property
    def scoreboard_service(self):
        return self.plugin.scoreboard_service

    @property
    def gen_service(self):
        return self.plugin.gen_service

    @property
    def merge_service(self):
        return self.plugin.merge_service

    def register_commands(self, server: PluginServerInterface) -> None:
        """注册所有命令"""
        server.register_command(self._build_command_tree())

        for legacy_prefix in LEGACY_PREFIXES:
            server.register_command(
                Literal(legacy_prefix).runs(self._legacy_redirect)
            )

    def _build_command_tree(self) -> Literal:
        """构建命令树"""
        return (
            Literal(COMMAND_PREFIX)
            .runs(self.cmd_help)
            # help
            .then(
                Literal("help")
                .runs(self.cmd_help)
                .then(Integer("page").runs(self.cmd_help))
            )
            # scoreboard
            .then(
                Literal("scoreboard")
                .then(
                    Text("category")
                    .then(
                        Text("item")
                        .runs(self.cmd_scoreboard)
                        .then(
                            GreedyText("display_name").runs(self.cmd_scoreboard)
                        )
                    )
                )
            )
            # save
            .then(Literal("save").runs(self.cmd_save))
            # set_display
            .then(
                Literal("set_display")
                .runs(self.cmd_set_display)
                .then(Text("name").runs(self.cmd_set_display))
            )
            # query
            .then(self._build_query_tree())
            # rank
            .then(self._build_rank_tree())
            # sum
            .then(self._build_sum_tree())
            # gen
            .then(self._build_gen_tree())
            # merge
            .then(self._build_merge_tree())
            # change
            .then(
                Literal("change")
                .then(
                    Text("cls1").then(
                        Text("item1").then(
                            Text("cls2").then(
                                Text("item2").runs(self.cmd_change)
                            )
                        )
                    )
                )
            )
        )

    def _build_query_tree(self) -> Literal:
        """构建 query 子命令树"""
        return (
            Literal("query")
            .then(
                Literal("query")
                .then(
                    Text("player")
                    .then(
                        Text("category")
                        .then(Text("item").runs(self.cmd_query))
                    )
                )
            )
            .then(
                Literal("cls")
                .then(
                    Text("player")
                    .then(
                        Text("category")
                        .runs(self.cmd_query_cls)
                        .then(Integer("limit").runs(self.cmd_query_cls))
                    )
                )
            )
            .then(
                Literal("item")
                .then(
                    Text("player")
                    .then(
                        Text("item")
                        .runs(self.cmd_query_item)
                        .then(Integer("limit").runs(self.cmd_query_item))
                    )
                )
            )
            .then(
                Text("player")
                .then(
                    Text("category")
                    .then(Text("item").runs(self.cmd_query))
                )
            )
        )

    def _build_rank_tree(self) -> Literal:
        """构建 rank 子命令树"""
        return (
            Literal("rank")
            .then(
                Literal("query")
                .then(
                    Text("category")
                    .then(
                        Text("item")
                        .runs(self.cmd_rank)
                        .then(Integer("limit").runs(self.cmd_rank))
                    )
                )
            )
            .then(
                Literal("cls")
                .then(
                    Text("category")
                    .runs(self.cmd_rank_cls)
                    .then(Integer("limit").runs(self.cmd_rank_cls))
                )
            )
            .then(
                Literal("item")
                .then(
                    Text("item")
                    .runs(self.cmd_rank_item)
                    .then(Integer("limit").runs(self.cmd_rank_item))
                )
            )
            .then(
                Text("category")
                .then(
                    Text("item")
                    .runs(self.cmd_rank)
                    .then(Integer("limit").runs(self.cmd_rank))
                )
            )
        )

    def _build_sum_tree(self) -> Literal:
        """构建 sum 子命令树"""
        return (
            Literal("sum")
            .then(
                Literal("make")
                .runs(self.cmd_sum_make)
                .then(Text("preset").runs(self.cmd_sum_make))
            )
            .then(
                Literal("clear")
                .runs(self.cmd_sum_clear)
                .then(Text("preset").runs(self.cmd_sum_clear))
            )
            .then(
                Literal("create")
                .then(
                    Text("preset")
                    .runs(self.cmd_sum_create)
                    .then(
                        Text("prefix_true")
                        .runs(self.cmd_sum_create)
                        .then(
                            Text("prefix_dummy")
                            .runs(self.cmd_sum_create)
                            .then(GreedyText("display_name").runs(self.cmd_sum_create))
                        )
                    )
                )
            )
            .then(Literal("remove").then(Text("preset").runs(self.cmd_sum_remove)))
            .then(
                Literal("add")
                .then(
                    Text("preset")
                    .then(Text("category").then(Text("item").runs(self.cmd_sum_add)))
                )
            )
            .then(
                Literal("del")
                .then(
                    Text("preset")
                    .then(Text("category").then(Text("item").runs(self.cmd_sum_del)))
                )
            )
            .then(Literal("del_all").then(Text("preset").runs(self.cmd_sum_del_all)))
            .then(Literal("remove_all").runs(self.cmd_sum_remove_all))
            .then(Literal("list").runs(self.cmd_sum_list))
            .then(
                Literal("view")
                .runs(self.cmd_sum_view)
                .then(Text("preset").runs(self.cmd_sum_view))
            )
        )

    def _build_gen_tree(self) -> Literal:
        """构建 gen 子命令树"""
        return (
            Literal("gen")
            .then(
                Literal("sum")
                .runs(self.cmd_gen_sum)
                .then(GreedyText("note").runs(self.cmd_gen_sum))
            )
            .then(
                Literal("record")
                .runs(self.cmd_gen_record)
                .then(GreedyText("note").runs(self.cmd_gen_record))
            )
            .then(
                Literal("minus")
                .then(
                    Text("mode")
                    .then(Text("time1").then(Text("time2").runs(self.cmd_gen_minus)))
                )
            )
            .then(
                Literal("list")
                .runs(self.cmd_gen_list)
                .then(Text("mode").runs(self.cmd_gen_list))
            )
            .then(
                Literal("del")
                .then(
                    Text("mode")
                    .runs(self.cmd_gen_del)
                    .then(Text("time").runs(self.cmd_gen_del))
                )
            )
        )

    def _build_merge_tree(self) -> Literal:
        """构建 merge 子命令树"""
        return (
            Literal("merge")
            .then(Literal("add").then(Text("player").runs(self.cmd_merge_add)))
            .then(Literal("del").then(Text("player").runs(self.cmd_merge_del)))
            .then(Literal("set").then(Text("player").runs(self.cmd_merge_set)))
            .then(Literal("list").runs(self.cmd_merge_list))
            .then(Literal("exec").runs(self.cmd_merge_exec))
        )

    def _legacy_redirect(self, source: CommandSource) -> None:
        """处理旧命令前缀"""
        self._reply(source, t("legacy.redirect", prefix=COMMAND_PREFIX))

    def _reply(self, source: CommandSource, message: str, prefix: str = "") -> None:
        """回复消息"""
        if prefix == "":
            prefix = f"§r[§b{PLUGIN_ID}§r]"
        source.reply(f"{prefix}{message}")

    def _broadcast(self, source: CommandSource, message: str) -> None:
        """广播消息"""
        source.get_server().say(f"§r[§b{PLUGIN_ID}§r]{message}")

    def _check_permission(self, source: CommandSource, level: Permission) -> bool:
        """检查权限"""
        if source.get_permission_level() < level.value:
            self._reply(source, t("error.permission_denied"))
            return False
        return True

    def _save_server(self, source: CommandSource, reload: bool = True) -> None:
        """保存服务器"""
        server = source.get_server()
        if reload:
            server.execute("reload")
        server.execute("save-off")
        server.execute("save-all")
        server.execute("save-on")
        self.stats_service.reload_all_stats()

    def cmd_help(self, source: CommandSource, context: dict = None) -> None:
        """显示帮助信息"""
        context = context or {}
        page = context.get("page", 1)

        help_pages = self._get_help_pages()
        if page < 1 or page > len(help_pages):
            self._reply(source, t("help.page_not_found", page=page))
            return

        self._reply(source, help_pages[page - 1], "")
        self._show_page_navigation(source, page, len(help_pages))

    def _get_help_pages(self) -> list[str]:
        """获取帮助页面"""
        p = COMMAND_PREFIX
        return [
            f"""------§rStatsPro v2.0.0 第§c§l1§r页------
§d§l{p}§r§b help§r §8[页码]§r 查看帮助信息
§d§l{p}§r§b scoreboard§r §5<类别>§r §6<物品>§r §7[显示名]§r 创建计分板
§d§l{p}§r§b save§r 保存服务器
§d§l{p}§r§b set_display§r §7[计分板名]§r 设置侧边栏显示
§d§l{p}§r§b query§r 查询玩家数据
  {p} query §c<玩家>§r §5<类别>§r §6<物品>§r 查询分数
  {p} query cls §c<玩家>§r §5<类别>§r §7[数量]§r 查询类别排行
  {p} query item §c<玩家>§r §6<物品>§r §7[数量]§r 查询物品排行""",
            f"""------§rStatsPro v2.0.0 第§c§l2§r页------
§d§l{p}§r§b rank§r 查看排行榜
  {p} rank §5<类别>§r §6<物品>§r §7[数量]§r 查询排行
  {p} rank cls §5<类别>§r §7[数量]§r 类别排行
  {p} rank item §6<物品>§r §7[数量]§r 物品排行
§d§l{p}§r§b sum§r 加和计分板
  {p} sum make/clear §a[预设名]§r 创建/清除
  {p} sum create §a<预设名>§r 创建预设
  {p} sum add/del §a<预设名>§r §5<类别>§r §6<物品>§r 添加/删除
  {p} sum list / view §a[预设名]§r 列表/详情""",
            f"""------§rStatsPro v2.0.0 第§c§l3§r页------
§d§l{p}§r§b gen§r 生成文件
  {p} gen sum/record §7[备注]§r 生成汇总/记录
  {p} gen minus §e<模式>§r §6<时间1>§r §6<时间2>§r 差值
  {p} gen list §e[模式]§r 列表
  {p} gen del §e<模式>§r §6[时间]§r 删除
§d§l{p}§r§c merge§r 合并玩家数据 §8(需要helper权限)
  {p} merge add/del §c<玩家>§r 添加/删除输入
  {p} merge set §c<玩家>§r 设置输出
  {p} merge list / exec 列表/执行
§d§l{p}§r§c change§r §5<类别1>§r §6<物品1>§r §5<类别2>§r §6<物品2>§r 转移数据""",
        ]

    def _show_page_navigation(
        self, source: CommandSource, current: int, total: int
    ) -> None:
        """显示分页导航"""
        nav = RTextList()
        if current > 1:
            nav.append(
                clickable_text(
                    t("help.prev_page"),
                    hover=f"{COMMAND_PREFIX} help {current - 1}",
                    command=f"{COMMAND_PREFIX} help {current - 1}",
                )
            )
        if current < total:
            if current > 1:
                nav.append("   ")
            nav.append(
                clickable_text(
                    t("help.next_page"),
                    hover=f"{COMMAND_PREFIX} help {current + 1}",
                    command=f"{COMMAND_PREFIX} help {current + 1}",
                )
            )
        source.reply(nav)

    def cmd_scoreboard(self, source: CommandSource, context: dict) -> None:
        """创建计分板"""
        self._save_server(source, reload=False)

        category = context["category"]
        item = context["item"]
        display_name = context.get("display_name")

        self.scoreboard_service.create_scoreboard(
            source.get_server(),
            category=category,
            item=item,
            display_name=display_name,
        )
        self.scoreboard_service.set_display(source.get_server())

        display = display_name or f"§e{category}§r.§b{item}§r"
        self._reply(source, t("scoreboard.created", name=display))

    def cmd_save(self, source: CommandSource) -> None:
        """保存服务器"""
        self._save_server(source)
        self._reply(source, t("save.success"))

    def cmd_set_display(self, source: CommandSource, context: dict = None) -> None:
        """设置计分板显示"""
        context = context or {}
        name = context.get("name", "")

        self.scoreboard_service.set_display(source.get_server(), name)
        if name:
            self._reply(source, t("scoreboard.display_set", name=name))
        else:
            self._reply(source, t("scoreboard.display_off"))

    def cmd_query(self, source: CommandSource, context: dict) -> None:
        """查询玩家分数"""
        self._save_server(source)

        player = context["player"]
        category = context["category"]
        item = context["item"]

        score = self.stats_service.get_score(player, category, item)
        name = self.stats_service.convert_to_name(player)

        self._broadcast(
            source,
            f"{name}的[§e{category}§r.§b{item}§r]的值为: {score}",
        )

    def cmd_query_cls(self, source: CommandSource, context: dict) -> None:
        """查询玩家类别排行"""
        self._save_server(source)

        player = context["player"]
        category = context["category"]
        limit = context.get("limit", 99)

        scores = self.stats_service.get_category_scores(player, category)
        if scores is None:
            self._reply(source, t("query.not_found", player=player))
            return

        self._print_ranking(source, scores, f"{player}的[§e{category}§r]", limit)

    def cmd_query_item(self, source: CommandSource, context: dict) -> None:
        """查询玩家物品排行"""
        self._save_server(source)

        player = context["player"]
        item = context["item"]
        limit = context.get("limit", 99)

        scores = self.stats_service.get_item_scores(player, item)
        if scores is None:
            self._reply(source, t("query.not_found", player=player))
            return

        self._print_ranking(source, scores, f"{player}的[§b{item}§r]", limit)

    def cmd_rank(self, source: CommandSource, context: dict) -> None:
        """查看排行榜"""
        self._save_server(source)

        category = context["category"]
        item = context["item"]
        limit = context.get("limit", 15)

        ranking = self.stats_service.get_ranking(
            category=category,
            item=item,
            limit=limit,
        )
        self._print_ranking(
            source, ranking, f"[§e{category}§r.§b{item}§r]", limit
        )

    def cmd_rank_cls(self, source: CommandSource, context: dict) -> None:
        """查看类别排行"""
        self._save_server(source)

        category = context["category"]
        limit = context.get("limit", 99)

        ranking = self.stats_service.get_ranking(category=category, limit=limit)
        self._print_ranking(source, ranking, f"[§e{category}§r]", limit)

    def cmd_rank_item(self, source: CommandSource, context: dict) -> None:
        """查看物品排行"""
        self._save_server(source)

        item = context["item"]
        limit = context.get("limit", 99)

        ranking = self.stats_service.get_ranking(item=item, limit=limit)
        self._print_ranking(source, ranking, f"[§b{item}§r]", limit)

    def _print_ranking(
        self,
        source: CommandSource,
        ranking: dict[str, int],
        title: str,
        limit: int,
    ) -> None:
        """打印排行榜"""
        if not ranking:
            self._reply(source, t("query.no_data"))
            return

        sorted_ranking = dict(
            sorted(ranking.items(), key=lambda x: x[1], reverse=True)[:limit]
        )
        total = sum(ranking.values())

        self._broadcast(source, f"{title}的总和为{total}, 前{len(sorted_ranking)}名如下:")

        colors = ["§6", "§b", "§3"]
        max_name_len = max(len(strip_prefix(k)) for k in sorted_ranking.keys())

        for i, (name, value) in enumerate(sorted_ranking.items(), 1):
            color = colors[i - 1] if i <= len(colors) else ""
            name = strip_prefix(name)
            padding = " " * (max_name_len - len(name))
            self._broadcast(source, f"{color}#{i} {name}{padding}  {value}")

    def cmd_sum_make(self, source: CommandSource, context: dict = None) -> None:
        """创建加和计分板"""
        context = context or {}
        preset_name = context.get("preset", "default")

        preset = self.config.get_preset(preset_name)
        if preset is None:
            self._reply(source, t("preset.not_found", name=preset_name))
            return

        self._save_server(source)
        self.scoreboard_service.create_sum_scoreboard(source.get_server(), preset)
        self._reply(source, t("sum.created", preset=preset_name))

    def cmd_sum_clear(self, source: CommandSource, context: dict = None) -> None:
        """清除加和计分板"""
        context = context or {}
        preset_name = context.get("preset", "default")

        preset = self.config.get_preset(preset_name)
        if preset is None:
            self._reply(source, t("preset.not_found", name=preset_name))
            return

        self.scoreboard_service.remove_sum_scoreboard(source.get_server(), preset)
        self.scoreboard_service.set_display(source.get_server())
        self._reply(source, t("sum.cleared", preset=preset_name))

    def cmd_sum_create(self, source: CommandSource, context: dict) -> None:
        """创建预设"""
        preset_name = context["preset"]
        prefix_true = context.get("prefix_true", f"{preset_name[0]}t")
        prefix_dummy = context.get("prefix_dummy", preset_name[0])
        display_name = context.get("display_name", preset_name)

        if preset_name == "default":
            self._reply(source, t("preset.cannot_modify_default"))
            return

        preset = self.config.add_preset(
            preset_name, display_name, prefix_dummy, prefix_true
        )
        if preset is None:
            self._reply(source, t("preset.exists", name=preset_name))
            return

        self.config.save()
        self._reply(
            source,
            t("preset.created", name=preset_name, prefix_true=prefix_true, prefix_dummy=prefix_dummy),
        )

    def cmd_sum_remove(self, source: CommandSource, context: dict) -> None:
        """移除预设"""
        preset_name = context["preset"]

        if preset_name == "default":
            self._reply(source, t("preset.cannot_modify_default"))
            return

        if self.config.remove_preset(preset_name):
            self.config.save()
            self._reply(source, t("preset.removed", name=preset_name))
        else:
            self._reply(source, t("preset.not_found", name=preset_name))

    def cmd_sum_add(self, source: CommandSource, context: dict) -> None:
        """添加计分项到预设"""
        preset_name = context["preset"]
        category = context["category"]
        item = context["item"]

        if preset_name == "default":
            self._reply(source, t("preset.cannot_modify_default"))
            return

        preset = self.config.get_preset(preset_name)
        if preset is None:
            self._reply(source, t("preset.not_found", name=preset_name))
            return

        if preset.add_item(category, item):
            self.config.save()
            self._reply(source, t("preset.item_added", category=category, item=item, preset=preset_name))
        else:
            self._reply(source, t("preset.item_exists", category=category, item=item, preset=preset_name))

    def cmd_sum_del(self, source: CommandSource, context: dict) -> None:
        """从预设删除计分项"""
        preset_name = context["preset"]
        category = context["category"]
        item = context["item"]

        if preset_name == "default":
            self._reply(source, t("preset.cannot_modify_default"))
            return

        preset = self.config.get_preset(preset_name)
        if preset is None:
            self._reply(source, t("preset.not_found", name=preset_name))
            return

        if preset.remove_item(category, item):
            self.config.save()
            self._reply(source, t("preset.item_removed", category=category, item=item, preset=preset_name))
        else:
            self._reply(source, t("preset.item_not_found", category=category, item=item, preset=preset_name))

    def cmd_sum_del_all(self, source: CommandSource, context: dict) -> None:
        """清空预设所有计分项"""
        preset_name = context["preset"]

        if preset_name == "default":
            self._reply(source, t("preset.cannot_modify_default"))
            return

        preset = self.config.get_preset(preset_name)
        if preset is None:
            self._reply(source, t("preset.not_found", name=preset_name))
            return

        preset.clear_items()
        self.config.save()
        self._reply(source, t("preset.cleared", name=preset_name))

    def cmd_sum_remove_all(self, source: CommandSource) -> None:
        """删除所有自定义预设"""
        self._save_server(source)

        removed = []
        for name in list(self.config.presets.keys()):
            if name != "default":
                preset = self.config.get_preset(name)
                if preset:
                    self.scoreboard_service.remove_sum_scoreboard(
                        source.get_server(), preset
                    )
                self.config.remove_preset(name)
                removed.append(name)

        self.config.save()
        if removed:
            self._reply(source, t("sum.all_removed", names=", ".join(removed)))
        else:
            self._reply(source, t("preset.list_empty"))

    def cmd_sum_list(self, source: CommandSource) -> None:
        """列出所有预设"""
        self._reply(source, t("preset.list_title"), "")

        for name, preset in self.config.presets.items():
            item_count = sum(len(items) for items in preset.items.values())
            line = RTextList(
                clickable_text(
                    f"§b{name}§r: {preset.display_name} ",
                    hover="点击查看详情",
                    command=f"{COMMAND_PREFIX} sum view {name}",
                ),
                f"(§e{preset.prefix_true}§r/§c{preset.prefix_dummy}§r) ",
                f"§7{item_count}项§r",
            )
            source.reply(line)

    def cmd_sum_view(self, source: CommandSource, context: dict = None) -> None:
        """查看预设详情"""
        context = context or {}
        preset_name = context.get("preset", "default")

        preset = self.config.get_preset(preset_name)
        if preset is None:
            self._reply(source, t("preset.not_found", name=preset_name))
            return

        self._reply(source, f"------预设 {preset_name} 详情------", "")

        for category, items in preset.items.items():
            self._reply(source, f"§l{category}§r: §b{len(items)}项§r", "")
            for item, abbr in items.items():
                self._reply(source, f"  - {item} : {abbr}", "")

    def cmd_gen_sum(self, source: CommandSource, context: dict = None) -> None:
        """生成汇总文件"""
        context = context or {}
        note = context.get("note", "")

        self._save_server(source)
        record = self.gen_service.generate_sum(note)
        self._reply(
            source,
            t("gen.success", mode="sum", time=record.time, path=record.path),
            "",
        )

    def cmd_gen_record(self, source: CommandSource, context: dict = None) -> None:
        """生成记录"""
        context = context or {}
        note = context.get("note", "")

        self._save_server(source)
        record = self.gen_service.generate_record(note)
        self._reply(
            source,
            t("gen.success", mode="record", time=record.time, path=record.path),
            "",
        )

    def cmd_gen_minus(self, source: CommandSource, context: dict) -> None:
        """生成差值文件"""
        mode = context["mode"]
        time1 = context["time1"]
        time2 = context["time2"]

        record = self.gen_service.generate_minus(mode, time1, time2)
        if record is None:
            self._reply(source, t("gen.minus_failed"))
            return

        self._reply(
            source,
            t("gen.success", mode="minus", time=record.time, path=record.path),
            "",
        )

    def cmd_gen_list(self, source: CommandSource, context: dict = None) -> None:
        """列出生成记录"""
        context = context or {}
        mode = context.get("mode", "all")

        records = self.gen_service.list_records(mode)
        if not records:
            self._reply(source, t("gen.list_empty", mode=mode), "")
            return

        self._reply(source, t("gen.list_title", mode=mode), "")

        for record in records.values():
            line = RTextList(
                clickable_text(
                    f"§b{record.time}§r",
                    hover="点击复制",
                    command=record.time,
                    action=RAction.suggest_command,
                ),
                f" {record.name} ",
                clickable_text(
                    "[§c删除§r]",
                    hover="点击删除",
                    command=f"{COMMAND_PREFIX} gen del {mode} {record.time}",
                ),
            )
            source.reply(line)

    def cmd_gen_del(self, source: CommandSource, context: dict) -> None:
        """删除生成记录"""
        if not self._check_permission(source, Permission.HELPER):
            return

        mode = context["mode"]
        time = context.get("time", "all")

        deleted = self.gen_service.delete_record(mode, time)
        if deleted:
            self._reply(source, t("gen.deleted", count=len(deleted)))
        else:
            self._reply(source, t("gen.delete_not_found"))

    def cmd_merge_add(self, source: CommandSource, context: dict) -> None:
        """添加合并输入玩家"""
        if not self._check_permission(source, Permission.HELPER):
            return

        player = context["player"]
        if self.merge_service.add_input_player(player):
            self._reply(source, t("merge.input_added", player=player))
        else:
            self._reply(source, t("merge.input_exists", player=player))

    def cmd_merge_del(self, source: CommandSource, context: dict) -> None:
        """删除合并输入玩家"""
        if not self._check_permission(source, Permission.HELPER):
            return

        player = context["player"]
        if self.merge_service.remove_input_player(player):
            if player == "all":
                self._reply(source, t("merge.input_cleared"))
            else:
                self._reply(source, t("merge.input_removed", player=player))
        else:
            self._reply(source, t("merge.input_not_found", player=player))

    def cmd_merge_set(self, source: CommandSource, context: dict) -> None:
        """设置合并输出玩家"""
        if not self._check_permission(source, Permission.HELPER):
            return

        player = context["player"]
        self.merge_service.set_output_player(player)
        self._reply(source, t("merge.output_set", player=player))

    def cmd_merge_list(self, source: CommandSource) -> None:
        """列出合并配置"""
        if not self._check_permission(source, Permission.HELPER):
            return

        inputs = self.merge_service.get_input_players()
        output = self.merge_service.get_output_player()

        self._reply(source, t("merge.list_input_title"), "")
        for player in inputs:
            line = RTextList(
                f"  {player} ",
                clickable_text(
                    "[§c×§r]",
                    hover="点击删除",
                    command=f"{COMMAND_PREFIX} merge del {player}",
                ),
            )
            source.reply(line)

        if output:
            self._reply(source, t("merge.list_output_title", player=output), "")
        else:
            self._reply(source, t("merge.list_output_empty"), "")

    def cmd_merge_exec(self, source: CommandSource) -> None:
        """执行合并"""
        if not self._check_permission(source, Permission.HELPER):
            return

        self._save_server(source)
        success, message = self.merge_service.execute_merge()
        self._save_server(source)

        if success:
            self._reply(source, message)
        else:
            self._reply(source, t("merge.failed", reason=message))

    def cmd_change(self, source: CommandSource, context: dict) -> None:
        """转移统计数据"""
        if not self._check_permission(source, Permission.HELPER):
            return

        cls1 = context["cls1"]
        item1 = context["item1"]
        cls2 = context["cls2"]
        item2 = context["item2"]

        self._reply(
            source,
            f"此功能需要直接修改玩家数据文件，请谨慎操作。"
            f"\n将 {cls1}.{item1} 转移到 {cls2}.{item2}",
        )
