# -*- coding: utf-8 -*-
import json
import time
import os
import shutil
from mcdreforged.api.all import ServerInterface, Info
from mcdreforged.api.rtext import RText, RTextList, RAction
from mcdreforged.api.decorator import new_thread
import copy
import os
import subprocess

PLUGIN_METADATA = {"id": "stats_pro_high_mc_version", "version": "1.5.1h", "author": "CalciumSilicate"}

is_1_16 = True  # change it to True if your gamer version is 1.16 or above.
permissions_needed = "helper"  # Could be guest, user, helper, admin, owner.

scoreboard_name = plugin_name = "StatsPro"
prefix = "!!sp"
alert_prefixes = ["!!stats"]
mcdr_path = os.path.join(".")
server_path = os.path.join(mcdr_path, "server")
plugin_path = os.path.join(mcdr_path, "plugins")
world_path = os.path.join(server_path, "world")
stats_path = os.path.join(world_path, "stats")
datapacks_path = os.path.join(world_path, "datapacks")
config_folder_path = os.path.join(mcdr_path, "config", plugin_name)
config_path = os.path.join(config_folder_path, "config.json")
uuid_path = os.path.join(config_folder_path, "uuid.json")
usercache_path = os.path.join(server_path, "usercache.json")
players_stats = {}
permissions_needed_num = ["guest", "user", "helper", "admin", "owner"].index(
    permissions_needed
)
default_config = {
    "gen_list": {"sum": {}, "record": {}, "minus": {}},
    "merge_list": {"input": [], "output": ""},
    "presuppositions": {
        "default": {
            "list": {
                "used": [
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
                ]
            },
            "name": "§c§l挖掘总榜§r",
            "prefix_dummy": "d",
            "prefix_true": "dt",
        }
    },
}
try:
    try:
        with open(config_path, "r") as cfg_file:
            cfg = json.load(cfg_file)
    except FileNotFoundError:
        cfg = default_config
except json.decoder.JSONDecodeError:
    cfg = default_config
    os.remove(config_path)
presuppositions: dict = cfg["presuppositions"]
help_message = """------§rMCDR {0}插件 v{2} 第§c§l1§r§r页§r------§r
{3}§b help§r §8[页码] §r查看帮助信息§r
{3}§b scoreboard§r §5<统计类别>§r §6<统计内容>§r §7[计分板显示名称] §8[-bot] §r创建一个计分板，并从stats文件中读取数据§r
{3}§b save§r 保存一次服务器§r
{3}§b set_display§r §7[计分板内部名称] §r修改在右侧显示的榜单，名称必须为§7§l内部名称§r，如: {0}§r
{3}§b query§r 查看单一玩家的数据
 1. {1} query§r [§bquery§r] §c<玩家名>§r §5<统计类别>§r §6<统计内容>§r 查看某玩家的某计分项的数值§r
 2. {1} query§r§b cls§r §c<玩家名>§r §5<统计类别>§r §7[列表最大长度]§r 查看某玩家的某§5统计类别§r下所有统计项的排行§r
 3. {1} query§r§b item§r §c<玩家名>§r §6<统计内容>§r §7[列表最大长度]§r 查看某玩家的某§6统计内容§r在所有§5统计类别§r中的排行§r
说明：
1. query的第1个用法中的第2个[§bquery§r]可加可不加，第2、3个用法中§7列表最大长度§r默认为15
2. §5<统计类别>§r可以是：§b killed_by, killed, custom, mined, used, dropped, broken, picked_up, crafted§r
3. §5<统计类别>§r和§6<统计内容>§r都不用带“minecraft:”前缀§r
4. §c<参数>§r是必选参数，§b[参数]§r是可选参数
""".format(
    plugin_name,
    "§l" + prefix + "§r",
    PLUGIN_METADATA["version"],
    "§d§l" + prefix + "§r",
)
help_message_2 = """------§rMCDR {0}插件 v{2} 第§c§l2§r§r页§r------
{3}§b rank§r 查看排行榜
 1. {1} rank§r [§bquery§r] §5<统计类别>§r §6<统计内容>§r §7[列表最大长度]§r §8[-bot]§r 查看某计分项的排行
 2. {1} rank§r§b cls§r §5<统计类别>§r §7[列表最大长度]§r §8[-bot]§r 查看某§5统计类别§r下所有统计项的排行
 3. {1} rank§r§b item§r §6<统计内容>§r §7[列表最大长度]§r §8[-bot]§r 查看某§6统计内容§r在所有§5统计类别§r中的排行
{3}§b sum§r 生成加和的计分板（如本插件自带的全工具计分板）
 1. {1} sum§b make§r §a[预设名]§r 生成加和计分板
 2. {1} sum§b clear§r §a[预设名]§r 移除加和计分板
 3. {1} sum§b create§r §a<预设名>§r 创建新的预设
 4. {1} sum§b remove§r §a<预设名>§r 移除现有的预设
 5. {1} sum§b add§r §a<预设名>§r §5<统计类别>§r §6<统计内容>§r 添加计分项至现有的预设中
 6. {1} sum§b del§r §a<预设名>§r §5<统计类别>§r §6<统计内容>§r 移除预设中现有的计分项
 7. {1} sum§b del_all§r §a<预设名>§r 移除预设中所有的计分项
 8. {1} sum§b remove_all§r 移除所有预设
 9. {1} sum§b list§r 列出预设列表
10. {1} sum§b view§r §a<预设名>§r 显示预设的详细信息
说明：
1. rank中的第1个用法的§7列表最大长度§r默认为15，第2、3个用法默认为99
2. rank的第1个用法中的第2个[§bquery§r]可加可不加
""".format(
    plugin_name,
    "§l" + prefix + "§r",
    PLUGIN_METADATA["version"],
    "§d§l" + prefix + "§r",
)
help_message_3 = """------§rMCDR {0}插件 v{2} 第§c§l3§r§r页§r------
§c§l红色§r的指令需要{4}以上的权限
{3}§c change§r §5<统计类别1>§r §6<统计内容1>§r §5<统计类别2>§r §6<统计内容2> §r将统计项1的分数赋值给统计项2并清空统计项1§r
{3}§b gen§r 生成文件
 1. {1} gen§b sum§r §7[备注]§r 生成加和全服玩家数据的json文件 
 2. {1} gen§b record§r §7[备注]§r 记录全服玩家数据
 3. {1} gen§b minus§r §e<sum/record>§r §6<时间1> <时间2>§r 对两次sum或record数据进行作差
 4. {1} gen§b list§r §e<sum/record/minus/all>§r 列出文件列表
 5. {1} gen§c del§r §e<sum/record/minus/all>§r §6<时间/all>§r 删除sum、record或minus文件
{3}§c merge§r 合并多个玩家的数据文件
 1. {1} merge§c add§r §c<玩家>§r 在输入玩家列表内添加玩家
 2. {1} merge§c del§r §c<玩家/all>§r 删除输入玩家列表
 3. {1} merge§c set§r §c<玩家>§r 设置输出玩家
 4. {1} merge§c list§r 列出上述指令设置的玩家
 5. {1} merge§c exec§r 执行合并操作
说明：
1. §6<时间>§r必须为{1}§b gen list§r中查询到的19位标准格式，如1145-14-19-19-81-00
""".format(
    plugin_name,
    "§l" + prefix + "§r",
    PLUGIN_METADATA["version"],
    "§d§l" + prefix + "§r",
    permissions_needed,
)
help_messages = [help_message, help_message_2, help_message_3]
flag_auto = False


def simple_text(message, text="", command="", action=RAction.run_command):
    r_text = (
        RText(message).set_hover_text(text).set_click_event(RAction.suggest_command, "")
    )
    if command:
        r_text.set_click_event(action, command)
        if not text:
            r_text.set_hover_text(text)
    return r_text


def get_time():  #
    return time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())


def abbr_set(*args):
    args = sorted(args)
    abbr = []
    for arg in args:
        abbr.append(("".join(x[0] for x in arg.split("_")) if "_" in arg else arg)[:6])
    if len(abbr) == len(list(set(abbr))):
        return abbr
    else:
        words = "AbCdEfGhIjKlMnOpQrStUvWxYz".lower() * 2
        for x in range(len(abbr) - 1):
            if abbr[x] == abbr[x + 1]:
                abbr[x + 1] = abbr[x + 1][:-1] + words[words.index(abbr[x + 1][-1]) + 1]
        return abbr_set(*abbr)


def init_presuppositions_abbr():
    global presuppositions
    temp = dict(presuppositions.items())
    for pre_name, pre_value in temp.items():
        whole_list = []
        item_list = []
        if is_1_16 and pre_name == "default":
            for i in [
                "netherite_pickaxe",
                "netherite_axe",
                "netherite_sword",
                "netherite_shovel",
                "netherite_hoe",
            ]:
                if "used." + i not in whole_list:
                    whole_list.append("used." + i)
        for key, value in pre_value["list"].items():
            for i in value:
                whole_list.append("{}.{}".format(key, i))
            presuppositions[pre_name]["list"][key] = {}
        whole_list = sorted(whole_list)
        for item in whole_list:
            item_list.append(item[item.index(".") + 1 :])
        abbr_list = abbr_set(*item_list)
        for x in range(len(abbr_list)):
            presuppositions[pre_name]["list"][
                whole_list[x][: whole_list[x].index(".")]
            ][item_list[x]] = abbr_list[x]


def write_config():
    with open(config_path, "w") as cfg_f:
        cfg_f.write(json.dumps(cfg, indent=4))


def get_uuid(name=None, uuid=None) -> dict or str or None:
    uuid_list = []
    output_list = {}
    if os.path.exists(usercache_path) and False:
        with open(usercache_path, "r") as usercache:
            for i in json.load(usercache):
                uuid_list.append([i["name"], i["uuid"], i["expiresOn"]])
        uuid_list = list(sorted(uuid_list, key=lambda a: a[2]))
        for i in uuid_list:
            if name and i[0] == name:
                return i[1]
            elif uuid and i[1] == uuid:
                return i[0]
            elif not (name or uuid):
                for x in uuid_list:
                    output_list[x[0]] = x[1]
                break
        return output_list if not (name or uuid) else None

    with open(uuid_path, "r") as uuid_file:
        uuid_list = json.load(uuid_file)
    if name is None and uuid is None:
        return uuid_list
    elif name is not None:
        return uuid_list[name]
    elif uuid is not None:
        for k, v in uuid_list.items():
            if v == uuid:
                return k
            else:
                continue


def init() -> None:
    for i in ["minus", "record", "sum"]:
        try:
            os.makedirs(os.path.join(config_folder_path, i))
        except FileExistsError:
            ...
    if not os.path.exists(config_path):
        with open(config_path, "w") as config:
            config.write(json.dumps(default_config, indent=4))
    d_uuid = get_uuid()
    # if d_uuid is not None:
    #     with open(uuid_path, 'w') as uuid:
    #         uuid.write(json.dumps(d_uuid, indent=4))


init()
init_presuppositions_abbr()
write_config()
player_uuid = get_uuid()


def convert_uuid_name(arg: str, is_to_uuid: bool = False):
    uuid_list = get_uuid()
    name_list = dict((value, key) for key, value in uuid_list.items())
    if is_to_uuid:
        return uuid_list[arg] if arg in uuid_list else arg
    else:
        return name_list[arg] if arg in name_list else arg


def is_bot(arg: str) -> bool:
    for i in ["bot", "b_", "steve", "alex", "dig"]:
        if i in arg.lower():
            return True
    return False


def print_msg(
    server: ServerInterface,
    info: Info,
    msg,
    msg_prefix: str = "§r[§b{}§r]".format(plugin_name),
    is_tell=True,
) -> None:
    if msg_prefix is None:
        msg_prefix = ""
    if not info.is_user:
        return
    if not isinstance(msg, RTextList):
        msg: str = str(msg)
        msg_list = msg.splitlines()
    else:
        msg_list = [msg]
    for line in msg_list:
        if server is None and info is None:
            print(msg_prefix + line)
        else:
            if info.is_player:
                if is_tell:
                    server.tell(info.player, msg_prefix + line)
                else:
                    server.say(msg_prefix + line)
            else:
                server.reply(info, msg_prefix + line)


def con_prefix(arg: str) -> str:
    return arg if arg.startswith("minecraft:") else "minecraft:" + arg


def del_prefix(arg: str) -> str:
    return arg if not arg.startswith("minecraft:") else arg[arg.index(":") + 1 :]


def get_players_stats() -> dict:
    global players_stats
    players_stats = {}
    for uid in player_uuid.values():
        path = os.path.join(stats_path, uid + ".json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as stats_file:
                players_stats[get_uuid(uuid=uid)] = json.load(stats_file)
    return players_stats


def get_player_stats(arg: str, is_refresh: bool = False) -> dict or None:
    if is_refresh:
        get_players_stats()
        return get_player_stats(arg)
    else:
        if players_stats:
            try:
                return (
                    players_stats[arg]
                    if arg in list(players_stats.keys())
                    else players_stats[get_uuid(uuid=arg)]
                )
            except KeyError:
                return None
        else:
            return get_player_stats(arg, is_refresh=True)


def get_player_score(arg: str, cls: str = None, item: str = None) -> int or None:
    arg = convert_uuid_name(arg, is_to_uuid=False)
    try:
        if cls and not item:
            return get_player_stats(arg)["stats"][con_prefix(cls)]
        elif item and not cls:
            output_list = {}
            for key, value in get_player_stats(arg)["stats"].items():
                for k, v in value.items():
                    if k == con_prefix(item):
                        output_list[key] = v
            return output_list if output_list else None
        else:
            return get_player_stats(arg)["stats"][con_prefix(cls)][con_prefix(item)]
    except (TypeError, KeyError):
        return None


def print_rank(server, info, rank_list: dict, title: str = None, rank_amount: int = 15):
    i = 0
    sorted_list = dict(
        list(sorted(rank_list.items(), key=lambda x: x[1], reverse=True))[:rank_amount]
    )
    max_len = max(len(x) for x in sorted_list.keys())
    if title is not None:
        print_msg(
            server,
            info,
            title.replace("%s", str(sum(rank_list.values()))),
            "",
            is_tell=False,
        )
    color_list = ["§6", "§b", "§3"]
    for name, value in sorted_list.items():
        i += 1
        name = name.replace("minecraft:", "")
        print_msg(
            server,
            info,
            "{}#{}{} {}{}{}{}".format(
                color_list[i - 1] if i <= len(color_list) else "",
                i,
                " " * (len(str(rank_amount)) - len(str(i))),
                name,
                " " * (max_len - len(name)),
                " " * (10 - len(str(value))),
                value,
            ),
            "",
            is_tell=False,
        )


def query(server, info, arg: str, cls: str = None, item: str = None, rank_amount=100):
    t_cls, t_item = con_prefix(cls) if cls else "", con_prefix(item) if item else ""
    if arg != "*":
        scores = get_player_score(arg, cls, item)
    else:
        get_players_stats()
        scores = sum_stats(*list(value for value in players_stats.values()))["stats"]
        if cls and item:
            scores = scores[t_cls][t_item]
        elif cls and not item:
            scores = scores[t_cls]
        elif item and not cls:
            scores = dict(
                ((k, v[t_item]) if t_item in v else ...) for k, v in scores.items()
            )
    arg = convert_uuid_name(arg)
    if (cls and not item) or (item and not cls):
        try:
            print_rank(
                server,
                info,
                rank_list=scores,
                title="{}的[{}§r]前{}名如下, 总和为%s".format(
                    arg,
                    "§e" + cls if cls else "§b" + item,
                    len(scores) if len(scores) < rank_amount else rank_amount,
                ),
                rank_amount=rank_amount,
            )
            f.write(json.dumps(scores))
        except TypeError:
            print_msg(server, info, "出错了")
            print_msg(
                server,
                info,
                "可能的原因:\n1. 不存在名为{0}的玩家\n2. {0}的{1}为空\n3. {1}拼写错误{2}".format(
                    arg,
                    cls if cls else item,
                    ""
                    if cls and item
                    else "\n4. {}不属于{}".format(
                        cls if cls else item, "cls" if cls else "item"
                    ),
                ),
                "",
            )
    else:
        print_msg(
            server,
            info,
            "{}的[§e{}§r.§b{}§r]的值为: {}".format(
                convert_uuid_name(arg), cls, item, scores
            ),
            "",
            is_tell=False,
        )


def get_list(cls: str = None, item: str = None, bot=False):
    output_list = {}
    for name, stats in players_stats.items():
        if bot or not is_bot(name):
            try:
                if cls and not item:
                    for i, v in stats["stats"][con_prefix(cls)].items():
                        output_list["{}.{}".format(name, i)] = v
                elif item and not cls:
                    for i, v in stats["stats"].items():
                        try:
                            output_list[
                                "{}.{}".format(name, i.replace("minecraft:", ""))
                            ] = v[con_prefix(item)]
                        except KeyError:
                            continue
                else:
                    output_list[name] = stats["stats"][con_prefix(cls)][
                        con_prefix(item)
                    ]
            except KeyError:
                continue
    return output_list


def rank(
    server,
    info,
    cls: str = None,
    item: str = None,
    rank_amount=15,
    bot=False,
    is_refresh=False,
):
    if is_refresh or not players_stats:
        get_players_stats()
        return rank(server, info, cls, item, rank_amount, bot, False)
    rank_list = get_list(cls, item, bot)
    try:
        print_rank(
            server,
            info,
            rank_list,
            title="[{}§r]的总和为%s, 前{}名如下:".format(
                "§e{}§r.§b{}§r".format(cls, item)
                if cls and item
                else ("§e" + cls if cls else "§b" + item),
                len(rank_list) if len(rank_list) < rank_amount else rank_amount,
            ),
            rank_amount=rank_amount,
        )
    except ValueError:
        print_msg(server, info, "出错了")
        print_msg(
            server,
            info,
            "可能的原因:\n1. {0}拼写错误\n2. {0}为空{1}".format(
                "{}.{}".format(cls, item) if cls and item else (cls if cls else item),
                ""
                if cls and item
                else "\n3. {}不属于{}".format(
                    cls if cls else item, "cls" if cls else "item"
                ),
            ),
            "",
        )


def set_display(server, arg=scoreboard_name):
    return server.execute(
        "scoreboard objectives setdisplay sidebar{}".format((" " + arg) if arg else arg)
    )


def scoreboard_builder(
    server,
    info,
    cls,
    item,
    title: str = None,
    inner_name: str or None = None,
    bot=False,
):
    inner_name = scoreboard_name if inner_name is None else inner_name
    value_list = get_list(cls, item, bot)
    if server is None or info is None:
        raise ValueError("Server or Info can't be None!")
    server.execute("scoreboard objectives remove {}".format(inner_name))
    if title is None:
        title = "§e{}§r.§b{}§r".format(cls, item)
    server.execute(
        "scoreboard objectives add {} minecraft.{}:minecraft.{} {}".format(
            inner_name, cls, item, json.dumps({"text": title})
        )
    )
    for name, value in value_list.items():
        server.execute(
            "scoreboard players set {} {} {}".format(name, inner_name, value)
        )
    return value_list


def save(server, is_reload=True):
    global player_uuid
    if server is None:
        return
    if is_reload:
        server.execute("reload")
    server.execute("save-off")
    server.execute("save-all")
    server.execute("save-on")
    time.sleep(0.1)
    player_uuid = get_uuid()
    init()
    init_presuppositions_abbr()
    get_players_stats()
    write_config()


def sum_stats(*args):
    stats_list = []
    output_stats = {}
    data_version = None
    for stats in args:
        if "DataVersion" in stats:
            data_version = stats["DataVersion"]
        stats_list.append(stats if "stats" not in stats else stats["stats"])
    for stats in stats_list:
        for key, value in stats.items():
            if key not in output_stats:
                output_stats[key] = {}
            for item, v in value.items():
                if item not in output_stats[key]:
                    output_stats[key][item] = v
    for key, value in output_stats.items():
        for item in value.keys():
            output_stats[key][item] = sum(
                (stats[key][item] if key in stats and item in stats[key] else 0)
                for stats in stats_list
            )
    return (
        output_stats
        if data_version is None
        else {"stats": output_stats, "DataVersion": data_version}
    )


def minus_stats(*args):
    if len(args) != 2:
        return None
    if args[0] is None:
        return args[1]
    elif args[1] is None:
        return args[0]
    first_stats = args[0] if "stats" not in args[0] else args[0]["stats"]
    second_stats = args[1] if "stats" not in args[1] else args[1]["stats"]
    output_stats = {}
    flag = True
    for stats in [first_stats, second_stats]:
        for key, value in stats.items():
            if key not in output_stats.items():
                output_stats[key] = {}
            for item, v in value.items():
                output_stats[key][item] = 0 if flag else v
        flag = False
    for key, value in first_stats.items():
        for item, v in value.items():
            output_stats[key][item] = abs(output_stats[key][item] - v)
    for key, value in dict(output_stats.items()).items():
        for item, v in dict(value.items()).items():
            if not v:
                del output_stats[key][item]
        if not output_stats[key]:
            del output_stats[key]
    return output_stats


def sum_scoreboard_command(presupposition="default"):
    pre = presuppositions[presupposition]
    abbr_list = []
    commands = {"creating": [], "removing": [], "names": {"true": [], "dummy": []}}
    for cls, value in pre["list"].items():
        for item, abbr in value.items():
            commands["removing"].append(
                "scoreboard objectives remove {}_{}".format(pre["prefix_true"], abbr)
            )
            commands["names"]["true"].append("{}_{}".format(pre["prefix_true"], abbr))
        abbr_list.extend(list(value.values()))
    temp = abbr_list[:]
    abbr_list = []
    for x in range(len(temp) - 1):
        abbr_list.append(temp[x] + temp[x + 1])
    abbr_list.extend(["minor", "total"])
    for abbr in abbr_list:
        commands["creating"].append(
            "scoreboard objectives add {}_{} dummy".format(pre["prefix_dummy"], abbr)
        )
        commands["removing"].append(
            "scoreboard objectives remove {}_{}".format(pre["prefix_dummy"], abbr)
        )
        commands["names"]["dummy"].append("{}_{}".format(pre["prefix_dummy"], abbr))
    commands["creating"].append(
        "scoreboard objectives setdisplay sidebar {}_total".format(pre["prefix_dummy"])
    )
    commands["creating"].append(
        "scoreboard objectives modify {}_total displayname {}".format(
            pre["prefix_dummy"], json.dumps({"text": pre["name"]})
        )
    )
    return commands


def datapacks_command(presupposition="default"):
    sum_command = sum_scoreboard_command(presupposition)
    true_list, dummy_list = sum_command["names"]["true"], sum_command["names"]["dummy"]
    total = dummy_list.pop(-1)
    minor = dummy_list.pop(-1)
    if len(dummy_list) - len(true_list) != -1:
        return None

    def cmd(target, operation, source):
        return "execute as @a run scoreboard players operation @s {} {} @s {}".format(
            target, operation, source
        )

    command_list = []
    flag = True
    for x in range(len(dummy_list)):
        if flag:
            command_list.append(cmd(dummy_list[x], "=", true_list[x]))
            command_list.append(cmd(dummy_list[x], "+=", true_list[x + 1]))
            flag = False
        else:
            command_list.append(cmd(dummy_list[x], "=", dummy_list[x - 1]))
            command_list.append(cmd(dummy_list[x], "+=", true_list[x + 1]))
    command_list.append(cmd(minor, "=", dummy_list[-1]))
    command_list.append(cmd(total, "=", minor))
    return command_list


def switch_sum_scoreboard(
    server,
    info,
    presupposition="default",
    is_opening=True,
    bot=False,
    is_call=False,
    i_flag=True,
):
    pre: dict = presuppositions[presupposition]
    command: dict = sum_scoreboard_command(presupposition)
    datapack_name = plugin_name.lower() + "_" + presupposition
    datapack_path = os.path.join(datapacks_path, datapack_name)
    function_path: str = os.path.join(
        datapack_path, "data", plugin_name.lower(), "function"
    )
    tags_path: str = os.path.join(
        datapack_path, "data", "minecraft", "tags", "function"
    )
    if os.path.exists(datapack_path):
        if not i_flag:
            shutil.rmtree(datapack_path)
            for cmd in command["removing"]:
                server.execute(cmd)
            return
        for i in presuppositions.keys():
            switch_sum_scoreboard(server, info, i, False, i_flag=False)
        server.execute("reload")
        if is_opening:
            return switch_sum_scoreboard(server, info, presupposition, is_opening, bot)
        else:
            if not is_call:
                print_msg(
                    server, info, "已成功关闭加和计分板({})".format(presupposition)
                )
    elif is_opening:
        value_list = {}
        for cls, value in pre["list"].items():
            if cls not in value_list:
                value_list[cls] = {}
            for item, abbr in value.items():
                value_list[cls][item] = scoreboard_builder(
                    server,
                    info,
                    cls=cls,
                    item=item,
                    bot=bot,
                    inner_name="{}_{}".format(pre["prefix_true"], abbr),
                )
        out_list = {}
        for cls, value in value_list.items():
            for item, v in value.items():
                for player, score in v.items():
                    if player in out_list:
                        out_list[player] += score
                    else:
                        out_list[player] = score
        for cmd in command["creating"]:
            server.execute(cmd)
        for player, value in out_list.items():
            server.execute(
                "scoreboard players set {} {}_{} {}".format(
                    player, pre["prefix_dummy"], "total", value
                )
            )
        os.makedirs(function_path)
        os.makedirs(tags_path)
        with open(os.path.join(function_path, "tick.mcfunction"), "w") as func:
            func.write("\n".join(datapacks_command(presupposition)))
        with open(os.path.join(tags_path, "tick.json"), "w") as tick:
            tick.write(
                json.dumps(
                    {"values": ["{}:tick".format(plugin_name.lower())]}, indent=4
                )
            )
        with open(os.path.join(datapack_path, "pack.mcmeta"), "w") as meta:
            meta.write(
                json.dumps({"pack": {"pack_format": 4, "description": ""}}, indent=4)
            )
        server.execute("reload")
        if not is_call:
            print_msg(server, info, "已成功创建加和计分板({})".format(presupposition))
    elif not is_call:
        print_msg(server, info, "加和计分板已关闭({})".format(presupposition))


def presupposition_control(server, info, presupposition, is_creating=True, **kwargs):
    global presuppositions
    if presupposition == "default":
        print_msg(server, info, "不能对default预设进行操作")
        return
    elif presupposition in presuppositions and is_creating:
        print_msg(server, info, "已经存在名为{}的预设".format(presupposition))
        return
    if is_creating:
        for pre in presuppositions.values():
            if kwargs["prefix_dummy"] in [pre["prefix_dummy"], pre["prefix_true"]]:
                print_msg(
                    server,
                    info,
                    "无实义计分板前缀({}_)与名为{}的预设重名".format(
                        kwargs["prefix_dummy"], pre["name"]
                    ),
                )
                return
            elif kwargs["prefix_dummy"] in [pre["prefix_dummy"], pre["prefix_true"]]:
                print_msg(
                    server,
                    info,
                    "实义计分板前缀({}_)与名为{}的预设重名".format(
                        kwargs["prefix_true"], pre["name"]
                    ),
                )
                return
        presuppositions[presupposition] = {
            "list": {},
            "name": kwargs["name"],
            "prefix_dummy": kwargs["prefix_dummy"],
            "prefix_true": kwargs["prefix_true"],
        }
        print_msg(
            server,
            info,
            "成功创建名为{}的预设，无实义计分板、实义计分板的前缀分别为{}_、{}_".format(
                *list(presuppositions[presupposition].values())[1:]
            ),
        )
    else:
        del presuppositions[presupposition]
    init_presuppositions_abbr()
    write_config()


def presupposition_clear(server, info):
    global presuppositions
    for pre_name in dict(presuppositions.items()):
        if pre_name != "default":
            del presuppositions[pre_name]
            print_msg(server, info, "成功删除{}".format(pre_name))
    init_presuppositions_abbr()
    write_config()


def presupposition_change(
    server, info, presupposition, cls="", item="", is_adding=True, is_del_all=False
):
    global presuppositions
    cls, item = del_prefix(cls), del_prefix(item)
    pre = presuppositions[presupposition]["list"]
    if presupposition == "default":
        print_msg(server, info, "不能对default预设进行操作")
        return
    if is_del_all:
        presuppositions[presupposition]["list"] = {}
        print_msg(
            server, info, "成功删除名为{}的预设中所有计分项".format(presupposition)
        )
    else:
        for pre_cls, pre_items in pre.items():
            for i in pre_items:
                if pre_cls == cls and i == item:
                    if is_adding:
                        print_msg(
                            server,
                            info,
                            "预设{}中已有{}.{}计分项".format(presupposition, cls, item),
                        )
                        return None
                    else:
                        del pre[pre_cls][pre_items]
                        print_msg(
                            server,
                            info,
                            "成功删除预设{}中的{}.{}".format(presupposition, cls, item),
                        )
                        return True
        if is_adding:
            if cls not in pre:
                pre[cls] = {}
            pre[cls][item] = ""
            print_msg(
                server,
                info,
                "成功在{}预设中添加{}.{}".format(presupposition, cls, item),
            )
    init_presuppositions_abbr()
    write_config()


def gen_file(server, info: Info = None, **kwargs):
    global cfg
    mode = kwargs["mode"]
    note = "#" + kwargs["note"] if "note" in kwargs and kwargs["note"] else ""
    players = kwargs["players"] if "players" in kwargs else None
    time_now = get_time()
    output_list = {}
    if mode == "sum":
        get_players_stats()
        path = os.path.join(config_folder_path, mode, time_now + note + ".json")
        output_list[path] = json.dumps(
            sum_stats(
                *list(
                    (value if players is None or name in players else {})
                    for name, value in players_stats.items()
                )
            ),
            indent=4,
        )
    else:
        path = os.path.join(config_folder_path, mode, time_now + note)
    if mode == "record":
        if os.path.exists(path):
            os.rmdir(path)
        shutil.copytree(stats_path, path)
    elif mode == "minus":
        mode = kwargs["minus_mode"]
        first = cfg["gen_list"][mode][kwargs["first"]]["abs_path"]
        second = cfg["gen_list"][mode][kwargs["second"]]["abs_path"]
        if mode == "sum":
            path = os.path.join(config_folder_path, mode, time_now + note + ".json")
            with open(first, "r") as f:
                with open(second, "r") as s:
                    output_list[path] = json.dumps(
                        minus_stats(json.load(f), json.load(s))
                    )
        elif mode == "record":
            path_list = {}
            for x in [first, second]:
                x = os.listdir(x)
                for i in x:
                    i = os.path.join(path, i)
                    if i not in path_list:
                        path_list[i] = [None, None]
            for p, index in [(first, 0), (second, 1)]:
                for i in os.listdir(p):
                    with open(os.path.join(p, i), "r") as f:
                        path_list[os.path.join(path, i)][index] = json.load(f)
            for i, value in dict(path_list.items()).items():
                path_list[i] = json.dumps(minus_stats(*value), indent=4)
                if not path_list[i]:
                    del path_list[i]
            output_list = path_list
    path = path.replace("\\", "/")
    cfg["gen_list"][kwargs["mode"]][time_now] = {
        "time": time_now,
        "name": time_now + note,
        "note": note.replace("#", ""),
        "path": path,
        "abs_path": os.path.abspath(path).replace("\\", "/"),
    }
    cfg["gen_list"][kwargs["mode"]][time_now]["note"] = None if not note else note
    if not os.path.exists(path) and path.split(".")[-1] != "json":
        os.makedirs(path)
    for path, value in output_list.items():
        with open(path, "w") as file:
            file.write(value)
    write_config()
    if info is None:
        return
    print_msg(
        server,
        info,
        "成功生成{}文件：\n时间： {}，\n名称： {}， \n注释： {}，\n路径： {}，\n绝对路径： {}".format(
            kwargs["mode"],
            *(
                "§b" + str(x).replace("\\", "/") + "§r"
                for x in list(cfg["gen_list"][kwargs["mode"]][time_now].values())
            ),
        ).replace("时间： §b", "§l时间： §c§l"),
        "",
    )


def gen_del(server, info, mode="all", del_time="all"):
    global cfg
    if mode == "all":
        for x in ["minus", "sum", "record"]:
            gen_del(server, info, x, del_time)
        return
    for t, value in dict(cfg["gen_list"][mode].items()).items():
        if del_time == "all" or t == del_time:
            print_msg(server, info, "成功删除{}文件：{}".format(mode, value["path"]))
            if os.path.isdir(value["abs_path"]):
                shutil.rmtree(value["abs_path"])
            else:
                os.remove(value["abs_path"])
            del cfg["gen_list"][mode][t]
    write_config()


def change_stats(server, info, cls1, item1, cls2, item2):
    global players_stats
    raw_list = (cls1, item1, cls2, item2)
    cls1, item1, cls2, item2 = (con_prefix(x) for x in raw_list)
    for name, stats in players_stats.items():
        stats = stats["stats"]
        flag1 = cls1 in stats and item1 in stats[cls1]
        flag2 = cls2 in stats
        if flag1:
            value = players_stats[name]["stats"][cls1][item1]
            if flag2:
                players_stats[name]["stats"][cls2][item2] = value
            else:
                players_stats[name]["stats"][cls2] = {cls2: value}
            del players_stats[name]["stats"][cls1][item1]
        else:
            if flag2 and item2 in stats[cls2]:
                del players_stats[name]["stats"][cls2][item2]
    for name, stats in players_stats.items():
        file_path = get_uuid(name=name) + ".json"
        with open(os.path.join(stats_path, file_path), "w") as file:
            file.write(json.load(stats))
    print_msg(server, info, "成功将{}.{}转移到{}.{}".format(*raw_list))


def merge(server, info, **kwargs):
    global cfg
    mode = kwargs["mode"]
    name = kwargs["name"]
    if mode == "add":
        cfg["merge_list"]["input"].append(name)
        print_msg(server, info, "成功将{}添加至输入列表中".format(name))
    elif mode == "del":
        if name == "all":
            cfg["merge_list"]["input"] = []
            print_msg(server, info, "成功清空输入列表")
        else:
            try:
                cfg["merge_list"]["input"].remove(name)
                print_msg(server, info, "成功将列表中的{}删除".format(name))
            except ValueError:
                print_msg(server, info, "列表中不存在{}".format(name))
                return
    elif mode == "set":
        cfg["merge_list"]["output"] = name
        print_msg(server, info, "成功将输出玩家设置为{}".format(name))
    elif mode == "list":
        ...
    elif mode == "exec":
        input_list = list(set(cfg["merge_list"]["input"]))
        output_player = cfg["merge_list"]["output"]
        if not input_list or not output_player:
            print_msg(server, info, "输入列表或输出玩家为空")
            return
        stats = sum_stats(
            *list(
                players_stats[n]
                for n in (
                    input_list
                    if output_player in input_list
                    else [*input_list, output_player]
                )
            ),
        )
        with open(
            os.path.join(stats_path, get_uuid(name=output_player) + ".json"), "w"
        ) as file:
            file.write(json.dumps(stats))
        for x in input_list:
            if x != output_player:
                if get_uuid(name=x) + ".json" in os.listdir(stats_path):
                    os.remove(os.path.join(stats_path, get_uuid(name=x) + ".json"))
        print_msg(
            server,
            info,
            "成功将{}的数据信息合并到{}".format("，".join(input_list), output_player),
        )
    write_config()


def is_enough_permission(server: ServerInterface, info: Info):
    if server.get_permission_level(info) >= permissions_needed_num:
        return True
    else:
        print_msg(server, info, "§c权限不足.")
        return False


def view_list(server: ServerInterface, info: Info):
    global presuppositions
    print_msg(server, info, "------预设列表------", "")
    for pre_name, value in presuppositions.items():
        r_text_list = RTextList(
            simple_text(
                "预设名：§b{}§r， 实义/无实义计分板前缀：§e{}§r / §c{}§r，".format(
                    pre_name, value["prefix_true"], value["prefix_dummy"]
                )
                + "计分板显示名称：{}， 详情子计分项：".format(value["name"]),
                "点击查看详情",
                "{} sum view {}".format(prefix, pre_name),
            )
        )
        for cls, v in value["list"].items():
            r_text_list.append(" {}: §b{}§r项 ".format(cls.title(), len(v)))
        print_msg(server, info, r_text_list, "")


def view_list_detail(server: ServerInterface, info: Info, arg="default"):
    if arg not in presuppositions:
        return None
    value = presuppositions[arg]
    len_list = []
    for cls, v in value["list"].items():
        for item in v:
            len_list.append(len(item))
    max_len = max(len_list)
    for cls, v in value["list"].items():
        print_msg(
            server, info, "§l" + cls.title() + "§r" + ": §b{}§r项".format(len(v)), ""
        )
        for item, abbr in v.items():
            print_msg(
                server,
                info,
                " - {}{} : {}".format(item, " " * (max_len - len(item)), abbr),
                "",
            )


def gen_list(server: ServerInterface, info: Info, arg=""):
    if arg == "all":
        for i in ["sum", "record", "minus"]:
            gen_list(server, info, i)
    elif arg in ["sum", "record", "minus"]:
        if not cfg["gen_list"][arg]:
            print_msg(server, info, "{}列表为空".format(arg), "")
            return
        print_msg(server, info, "{}列表如下：".format(arg), "")
        for i in cfg["gen_list"][arg].values():
            print_msg(
                server,
                info,
                RTextList(
                    simple_text(
                        "时间（点击复制）: §b{}§r".format(i["time"]),
                        command=i["time"],
                        action=RAction.suggest_command,
                        text="点击复制",
                    ),
                    "， 名称：§c{}§r， 注释：§7{}§r， ".format(i["name"], i["note"]),
                    simple_text(
                        "§e[路径（悬浮查看或点击复制）§r]",
                        text=i["path"],
                        command=i["path"],
                        action=RAction.suggest_command,
                    ),
                    simple_text(
                        "[§c绝对路径（同上）§r]",
                        text=i["abs_path"],
                        command=i["abs_path"],
                        action=RAction.suggest_command,
                    ),
                    simple_text(
                        " [§c删除§r]",
                        command="{} gen del {} {}".format(prefix, arg, i["time"]),
                    ),
                ),
                "",
            )


def merge_list(server: ServerInterface, info: Info):
    print_msg(server, info, "input玩家列表如下：", "")
    for i in cfg["merge_list"]["input"]:
        print_msg(
            server,
            info,
            RTextList(
                i,
                simple_text("    [§c×§r]", command="{} merge del {}".format(prefix, i)),
            ),
            "",
        )
    print_msg(server, info, "output玩家是：", "")
    if cfg["merge_list"]["output"]:
        print_msg(
            server,
            info,
            RTextList(
                cfg["merge_list"]["output"],
                simple_text(
                    "    [§er§r]",
                    command="{} merge set ".format(prefix),
                    text="点击重设",
                    action=RAction.suggest_command,
                ),
            ),
            "",
        )


def on_user_info(server: ServerInterface, info: Info):
    global player_uuid
    if not info.content:
        return
    raw_cmd = info.content.split()
    if raw_cmd[0] in alert_prefixes:
        print_msg(server, info, "请使用§c§l{}§r!".format(prefix))
        return
    if raw_cmd[0] != prefix:
        return
    cmd = " ".join(raw_cmd).replace("&", "§")
    bot = True if "-bot" in cmd else False
    cmd = (
        cmd.replace("-bot", "")
        .replace("true", "True")
        .replace("false", "False")
        .split()
    )
    cmd[0] = cmd[0].replace("！", "!")
    len_cmd = len(cmd)
    child_cmd = cmd[1] if len_cmd > 1 else ""
    third_cmd = cmd[2] if len_cmd > 2 else ""
    init()
    # !!sp
    server.execute("gamerule sendCommandFeedback false")

    if len_cmd == 1:
        info2 = copy.deepcopy(info)
        info2.content = "{} help 1".format(prefix)
        return on_user_info(server, info2)

    # !!sp help [PageIndex]
    elif len_cmd in [2, 3] and child_cmd == "help":
        page_index = int(cmd[2]) if len_cmd == 3 else 1
        if page_index not in list(range(1, len(help_messages) + 1)):
            print_msg(server, info, "没有找到相应页码(第{}页)".format(page_index))
            return
        print_msg(server, info, help_messages[page_index - 1], "")
        r_text_list = RTextList()
        if page_index != 1:
            r_text_list.append(
                simple_text(
                    "[§b←上一页§r]",
                    text="{} help {}".format(prefix, page_index - 1),
                    command="{} help {}".format(prefix, page_index - 1),
                    action=RAction.run_command,
                )
            )
        if page_index != 3:
            r_text_list.append(
                simple_text(
                    "{}[§c下一页→§r]".format("   " if page_index != 1 else ""),
                    text="{} help {}".format(prefix, page_index + 1),
                    command="{} help {}".format(prefix, page_index + 1),
                    action=RAction.run_command,
                )
            )
        print_msg(server, info, r_text_list, "")

    # !!sp query
    elif len_cmd in [5, 6] and child_cmd == "query":
        third_list = ["query", "cls", "item"]
        player = cmd[3]
        if third_cmd in third_list:
            save(server)

            # !!sp query [query] <Player> <Cls> <Item>
            if len_cmd == 6 and third_cmd == third_list[0]:
                query(server, info, player, cmd[4], cmd[5])

            # !!sp query cls <Player> <Cls> [RankAmount]
            elif len_cmd in [5, 6] and third_cmd == third_list[1]:
                query(
                    server,
                    info,
                    player,
                    cls=cmd[4],
                    rank_amount=int(cmd[5]) if len_cmd == 6 else 99,
                )

            # !!sp query item <Player> <Item> [RankAmount]
            elif len_cmd in [5, 6] and third_cmd == third_list[2]:
                query(
                    server,
                    info,
                    player,
                    item=cmd[4],
                    rank_amount=int(cmd[5]) if len_cmd == 6 else 99,
                )

        # !!sp query <Player> <Cls> <Item>
        elif len_cmd == 5:
            info2 = copy.deepcopy(info)
            raw_cmd.insert(2, "query")
            info2.content = " ".join(raw_cmd)
            return on_user_info(server, info2)

        # !!sp query %$^#
        else:
            print_msg(server, info, "输入错误，请输入{}查看帮助".format(prefix))

    # !!sp rank
    elif len_cmd in [4, 5, 6] and child_cmd == "rank":
        third_list = ["query", "cls", "item"]
        if third_cmd in third_list:
            save(server)

            # !!sp rank [query] <Cls> <Item> [RankAmount] [-Bot]
            if len_cmd in [5, 6] and third_cmd == third_list[0]:
                rank(
                    server,
                    info,
                    cmd[3],
                    cmd[4],
                    rank_amount=int(cmd[5]) if len_cmd == 6 else 15,
                    bot=bot,
                )

            # !!sp rank cls <Cls> [RankAmount] [-Bot]
            elif len_cmd in [4, 5] and third_cmd == third_list[1]:
                rank(
                    server,
                    info,
                    cls=cmd[3],
                    rank_amount=int(cmd[4]) if len_cmd == 5 else 99,
                    bot=bot,
                )

            # !!sp rank item <Item> [RankAmount] [-Bot]
            elif len_cmd in [4, 5] and third_cmd == third_list[2]:
                rank(
                    server,
                    info,
                    item=cmd[3],
                    rank_amount=int(cmd[4]) if len_cmd == 5 else 99,
                    bot=bot,
                )

        # !!sp rank <Cls> <Item> [RankAmount] [-Bot]
        elif len_cmd in [4, 5]:
            info2 = copy.deepcopy(info)
            raw_cmd.insert(2, "query")
            info2.content = " ".join(raw_cmd)
            return on_user_info(server, info2)

        # !!sp rank %$^#
        else:
            print_msg(server, info, "输入错误，请输入{}查看帮助".format(prefix))

    # !!sp scoreboard <Cls> <Item> [DisplayName]
    elif len_cmd in [4, 5] and child_cmd == "scoreboard":
        save(server, False)
        scoreboard_builder(
            server, info, cmd[2], cmd[3], cmd[4] if len_cmd == 5 else None, bot=bot
        )
        set_display(server)
        print_msg(
            server,
            info,
            "已创建{}计分板，内部ID为{}".format(
                cmd[4] if len_cmd == 5 else "§e{}§r.§b{}§r".format(cmd[2], cmd[3]),
                scoreboard_name,
            ),
        )

    # !!sp save
    elif len_cmd == 2 and child_cmd == "save":
        save(server)
        print_msg(server, info, "已重载数据包并保存存档")

    # !!sp set_display [InnerName]
    elif len_cmd in [2, 3] and child_cmd == "set_display":
        set_display(server, arg=cmd[2] if len_cmd == 3 else "")
        if len_cmd == 3:
            print_msg(server, info, "已尝试显示内部ID为{}的计分板".format(cmd[2]))
        else:
            print_msg(server, info, "已关闭计分板")

    # !!sp sum
    elif len_cmd in [3, 4, 5, 6, 7] and child_cmd == "sum":
        third_list = [
            "make",
            "clear",
            "create",
            "remove",
            "add",
            "del",
            "del_all",
            "remove_all",
            "list",
            "view",
        ]
        if third_cmd in third_list:
            # !!sp sum remove/add/del/del_all [...]
            if len_cmd in [4, 6] and third_cmd in third_list[3:7]:
                save(server)
                switch_sum_scoreboard(
                    server, info, cmd[3], is_opening=False, is_call=True
                )

            # --------------------------------------------

            # !!sp sum make/clear [PresuppositionName]
            if len_cmd in [3, 4] and third_cmd in third_list[:2]:
                if cmd[2] == third_list[0]:
                    save(server)
                switch_sum_scoreboard(
                    server,
                    info,
                    cmd[3] if len_cmd == 4 else "default",
                    bot=bot,
                    is_opening=cmd[2] == third_list[0],
                )
                if cmd[2] != third_list[0]:
                    set_display(server)

            # !!sp sum create <PresuppositionName> [PrefixTrue] [PrefixDummy] [DisplayName]
            elif len_cmd in [4, 5, 6, 7] and third_cmd == third_list[2]:
                presupposition_name = cmd[3]
                prefix_true = cmd[4] if len_cmd > 4 else presupposition_name[0] + "t"
                prefix_dummy = cmd[5] if len_cmd > 5 else presupposition_name[0]
                display_name = cmd[6] if len_cmd > 6 else presupposition_name
                presupposition_control(
                    server,
                    info,
                    presupposition_name,
                    is_creating=True,
                    prefix_true=prefix_true,
                    prefix_dummy=prefix_dummy,
                    name=display_name,
                )

            # !!sp sum remove <PresuppositionName>
            elif len_cmd == 4 and third_cmd == third_list[3]:
                presupposition_control(server, info, cmd[3], is_creating=False)

            # !!sp sum add/del <PresuppositionName> <Cls> <Item>
            elif len_cmd == 6 and third_cmd in third_list[4:6]:
                presupposition_change(
                    server,
                    info,
                    cmd[3],
                    cmd[4],
                    cmd[5],
                    is_adding=third_cmd == third_list[4],
                )

            # !!sp sum del_all <PresuppositionName>
            elif len_cmd == 4 and third_cmd == third_list[6]:
                presupposition_change(server, info, cmd[3], is_del_all=True)

            # !!sp sum remove_all
            elif len_cmd == 3 and third_cmd == third_list[7]:
                save(server)
                for pre_name in presuppositions:
                    if pre_name != "default":
                        switch_sum_scoreboard(server, info, pre_name, is_opening=False)
                presupposition_clear(server, info)

            # !!sp sum list
            elif len_cmd == 3 and third_cmd == third_list[8]:
                view_list(server, info)

            # !!sp sum view [PresuppositionName]
            elif len_cmd in [3, 4] and third_cmd == third_list[9]:
                view_list_detail(server, info, cmd[3] if len_cmd == 4 else "default")

        # !!sp sum %$^#
        else:
            print_msg(server, info, "输入错误，请输入{}查看帮助".format(prefix))

    # !!sp gen
    elif len_cmd > 2 and child_cmd == "gen":
        third_list = ["sum", "record", "minus", "list", "del"]
        if third_cmd in third_list:
            # !!sp gen sum/record [Note]
            if len_cmd in [3, 4] and third_cmd in third_list[:2]:
                gen_file(
                    server, info, mode=third_cmd, note=cmd[3] if len_cmd == 4 else ""
                )

            # !!sp gen sum/record <Note> [Player1, [Player2, [Player3, ...]]]
            elif len_cmd > 4 and third_cmd in third_list[:2]:
                gen_file(server, info, mode=third_cmd, players=cmd[4:])

            # !!sp gen minus sum/record <Time1> <Time2>
            elif len_cmd == 6 and third_cmd == third_list[2]:
                gen_file(
                    server,
                    info,
                    mode=third_cmd,
                    minus_mode=cmd[3],
                    first=cmd[4],
                    second=cmd[5],
                )

            # !!sp gen list [Mode]
            elif len_cmd in [3, 4] and third_cmd == third_list[3]:
                gen_list(server, info, cmd[3] if len_cmd == 4 else "all")

            # !!sp gen del <Mode> <Time>
            elif len_cmd in [4, 5] and third_cmd == third_list[4]:
                if is_enough_permission(server, info):
                    gen_del(server, info, cmd[3], cmd[4] if len_cmd == 5 else "all")

        # !!sp gen %$^#
        else:
            print_msg(server, info, "输入错误，请输入{}查看帮助".format(prefix))

    # !!sp change <Cls1> <Item1> <Cls2> <Item2>
    elif len_cmd == 6 and child_cmd == "change":
        if is_enough_permission(server, info):
            change_stats(server, info, *cmd[2:])

    # !!sp merge
    elif len_cmd in [3, 4] and child_cmd == "merge":
        if is_enough_permission(server, info):
            third_list = ["add", "del", "set", "list", "exec"]
            if third_cmd in third_list:
                # !!sp merge add/del/set <PlayerName or All>
                if len_cmd == 4 and third_cmd in third_list[:3]:
                    merge(server, info, mode=third_cmd, name=cmd[3])

                # !!sp merge list
                elif len_cmd == 3 and third_cmd == third_list[3]:
                    merge_list(server, info)

                # !!sp merge exec
                elif len_cmd == 3 and third_cmd == third_list[4]:
                    save(server)
                    merge(server, info, mode=third_cmd, name="")
                    save(server)

            # !!sp merge %$^#
            else:
                print_msg(server, info, "输入错误，请输入{}查看帮助".format(prefix))

    elif len_cmd == 2 and child_cmd == "auto":
        auto(server)

    elif len_cmd >= 3 and child_cmd == "eval":
        if is_enough_permission(server, info):
            print(" ".join(cmd[2:]))
            print_msg(server, info, eval(" ".join(cmd[2:])), "§7", is_tell=False)

    elif len_cmd == 2 and child_cmd == "uuid":
        import requests

        with open("./server/usercache.json", "r") as rf:
            user_cache = json.load(rf)
        with open("./config/StatsPro/uuid.json", "r") as ru:
            existed_uuid = json.load(ru)

        def get_name_via_network(uuid):
            print_msg(server, info, "正在获取{}玩家名称".format(uuid), is_tell=True)
            content = json.loads(
                requests.get(
                    "https://sessionserver.mojang.com/session/minecraft/profile/{}".format(
                        uuid
                    )
                ).text
            )["name"]
            print_msg(
                server, info, "获取成功，玩家名称为{}".format(content), is_tell=True
            )
            return content

        copied_uuid = copy.deepcopy(existed_uuid)
        changed_list = []
        for user in user_cache:
            user_uuid = user["uuid"]
            try:
                user_name = get_name_via_network(uuid=user_uuid)
            except Exception:
                continue
            for n, u in copied_uuid.items():
                if u == user_uuid:
                    if n != user_name:
                        changed_list.append(n)
                    del existed_uuid[n]
                    break
            existed_uuid[user_name] = user_uuid
        with open("./config/StatsPro/uuid.json", "w") as wu:
            wu.write(json.dumps(existed_uuid, indent=2))
        print_msg(
            server=server,
            info=info,
            msg="玩家昵称列表更新完成，更新了{}个玩家：{}".format(
                len(changed_list), ", ".join(changed_list)
            ),
            is_tell=False,
        )

    # !!sp %$^#
    else:
        print_msg(server, info, "输入错误，请输入{}查看帮助".format(prefix))

    server.execute("gamerule sendCommandFeedback true")
