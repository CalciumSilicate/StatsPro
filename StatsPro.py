# -*- coding: utf-8 -*-
import json
import os
import time
import urllib
import pytz
import shutil

# --------------------------------------------------------------------------- #
#                                                                             #
is_netherite_exists = False  # False为无Netherite, True为有Netherite          #
mcdr_path = ''  # MCDR的路径,留空使用相对路径                                     #
prefix = '!!sp'  # 命令的前缀                                                   #
tip_prefix = ['!!stats']  # 如果用户输入了列表中的前缀, 将提示其使用prefix          #
#                                                                             #
# --------------------------------------------------------------------------- #


server_path = os.path.join(mcdr_path, 'server/')
world_path = os.path.join(server_path, 'world/')
plugin_name = 'StatsPro'
config_path = os.path.join(mcdr_path, 'config/{}'.format(plugin_name))
message_prefix = '§r[§d{}§r]'.format(plugin_name)
scoreboard_name = plugin_name
commandlist = {
    "permission_required": [  # 需要权限的命令
        'del', 'del_all', 'del_player', 'change', 'sumtoplayer', 'make_mined', 'clear_mined'
    ],
    "permission_not_required": [  # 不需要权限的命令
        'query', 'rank', 'scoreboard', 'save', 'set_display', 'make', 'clear', 'sum', 'record', 'minus', 'list', 'help'
    ]
}
permission = 3
permission_list = [
    'guest',
    'user',
    'helper',
    'admin',
    'owner'
]
tool_list = {
    'normal': {
        'sword': 'sw',
        'pickaxe': 'p',
        'axe': 'a',
        'shovel': 's'
    },
    'unusual': {
        'shears': 'sh'
    }
}
resource_list = {
    'diamond': 'd',
    'iron': 'i',
    'golden': 'g',
    'stone': 's',
    'wooden': 'w'
}
mined_item = {'minecraft:stone':'stn'}
if is_netherite_exists:
    resource_list['netherite'] = 'n'
total_stats_scoreboard_name = 'TotalDig'
total_mined_scorebaord_name = 'TotalMine'
version = '3.0'
help_message = ['''
------MCDR {0}插件 v{2}------
§c Page 1§r
§r 功能说明 : (以下功能不需要权限)§r
§r{1} help §r<页码> §r查看帮助消息§r
§r{1} query §r<玩家> §e<统计类别> §b<统计内容>§r
§r{1} rank §r§e<统计类别> §b<统计内容> §7[排行数(默认15)] [-bot]§r
§r{1} scoreboard §r§e<统计类别> §b<统计内容>§r §a[计分板名称] §7[-bot]§r
§r{1} save §r
§r{1} set_display §a[计分板ID] §r, §a[计分板ID]§r留空则关闭计分板显示
§r{1} make §r 开启全工具挖掘计分板(基于used:工具)
§r{1} clear §r 关闭全工具挖掘计分板(基于used:工具)
§r{1} sum §d [注释]§r 加和所有玩家的统计信息数据并保存
§r{1} record §d [注释]§r 记录所有玩家的统计信息数据并保存
§r{1} minus §3<sum/record> §6<时间1> <时间2>§r
§r 将两个总和或记录的文件进行作差并保存
§r{1} list §3<sum/record/all>§r查看总和或记录的文件列表
§r 参数说明 : §r
§e<统计类别>§r与§b<统计内容>§r无需带'minecraft:前缀'§r
§r{1} minus §3<sum/record> §6<时间1> <时间2>§r中
§6<时间1> <时间2>§r必须为§r{1} list §3<sum/record/all>§r中查询到的标准格式
'''.format(plugin_name, prefix, version),
'''
------MCDR {0}插件 v{3}------
§c Page 2§r
§r 功能说明 : (以下功能需要{1}以上的权限)§r
§r{2} help§r §r<页码> §r查看帮助消息§r
§r{2} §cdel§r §3<sum/record> §6<时间>§r
§r{2} §cmake_mine§r 开启全方块挖掘计分板(基于mined:方块)
§r{2} §cclear_mine§r 关闭全方块挖掘计分板(基于mined:方块)
§r{2} §cdel_all§r §r
§r{2} §cchange§r §e<统计类别1> §b<统计内容1>§r §e<统计类别2> §b<统计内容2>§r
§r{2} §csumtoplayer 
§l§r§l - §r{2} §csumtoplayer add_input§r <玩家id>§r
§l§r§l - §r{2} §csumtoplayer del_input§r <玩家id>§r
§l§r§l - §r{2} §csumtoplayer cleart§r
§l§r§l - §r{2} §csumtoplayer list§r
§l§r§l - §r{2} §csumtoplayer set_output§r <玩家id>§r
§l§r§l - §r{2} §csumtoplayer execute§r
§r 参数说明 : §r
§r{2} §cdel§r §3<sum/record> §6<时间>§r中§6<时间>§r必须为§r{1} list §3<sum/record/all>§r中查询到的标准格式
'''.format(plugin_name, permission_list[permission], prefix, version)
]
meaningful_scoreboard = {}
meaningless_scoreboard = {}
dummy_list = []


def getday():  #
    return time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime())


def suf(arg):  #
    return 'minecraft:{}'.format(arg) if arg.find('minecraft:') == -1 else arg


def is_bot(name):  #
    flag = False
    for block_key in ['bot', '_b_', 'Steve', 'Alex', 'loader', 'PCRC', 'FX_White']:
        if name.upper().find(block_key.upper()) != -1:
            flag = True
            break
    return flag


def print_message(server, info, message, is_say=False):  #
    for l in str(message).splitlines():
        if not info.is_player:
            server.reply(info, l)
        elif is_say:
            server.say(l)
        else:
            server.tell(info.player, l)


def print_plugin_message(server, info, message):  #
    print_message(server, info, '{}{}'.format(message_prefix, message))


def get_player_list(is_bot_in_list=True):  #
    global name_and_uuid_dict
    usercache = json.load(open(os.path.join(server_path, 'usercache.json'), 'r'))
    name_and_uuid_dict = {}
    for player in usercache:
        if is_bot(player['name']) == False or is_bot_in_list:
            name_and_uuid_dict[player['name']] = player['uuid']
    open(os.path.join(config_path, 'uuid.json'), 'w').write(json.dumps(name_and_uuid_dict, indent=4))
    return name_and_uuid_dict


def get_player_stats(name=None, uuid=None):  #
    if name == None and uuid == None:
        return None
    try:
        filename = 'stats/{}.json'.format(get_player_list()[name]) if uuid == None else 'stats/{}.json'.format(uuid)
    except KeyError:
        return None
    try:
        return json.load(open(os.path.join(world_path, filename), 'r'))['stats']
    except FileNotFoundError:
        return None


def query_stats(server, info, name, cls, target):  # query
    try:
        value = get_player_stats(name)[suf(cls)][suf(target)]
    except KeyError:
        value = None
    print_message(server, info, '玩家{}统计数据[§e{}§r.§b{}§r]的值为:{}'.format(name, cls, target, value))


def rank(server, info, cls, target, rank_amount=15, is_bot_in_rank=False):  # rank
    player_list = get_player_list(is_bot_in_rank)
    rank_list = {}
    flag = True
    for name, uuid in player_list.items():
        flag = False
        try:
            try:
                rank_list[get_player_stats(uuid=uuid)[suf(cls)][suf(target)]] = name
            except KeyError:
                None
        except TypeError:
            None
    if flag:
        print_plugin_message(server, info, '没有找到统计项[§e{}§r.§b{}§r]'.format(cls, target))
    rank_list = dict(sorted(rank_list.items(), key=lambda item: item[0], reverse=True))
    rank_amount = rank_amount if rank_amount <= len(rank_list) else len(rank_list)
    try:
        temp = max([len(name) for name in rank_list.values()])
    except ValueError:
        print_plugin_message(server, info, 'None')
        return
    color_list = ['§6', '§b', '§e']
    value_sum = sum(list(rank_list.keys()))
    print_message(server, info, '统计项[§e{}§r.§b{}§r]的总和为§c{}§r, 前{}名为'.format(cls, target, value_sum, rank_amount))
    for x in range(rank_amount):
        color = color_list[x] if x < len(color_list) else ''
        print_message(server, info, '{}#{}{}{}{}{}{}'.format(
            color,
            x + 1,
            ' ' * (4 - len(str(x + 1))),
            list(rank_list.values())[x],
            ' ' * (16 - len(list(rank_list.values())[x]) + 1),
            ' ' * (8 - len(str(list(rank_list.keys())[x]))),
            list(rank_list.keys())[x]
        )
                      )


def save_all(server):  # save
    server.execute('save-all')
    time.sleep(0.01)


def build_scoreboard(server, info, cls, target, is_bot_in_board=False, title=None, scbd_name=scoreboard_name, is_show=True):  # scoreboard
    player_list = get_player_list(is_bot_in_board)
    value_list = {}
    title = {"text": "§e{}§r.§b{}§r".format(cls, target)} if title == None else {"text": "{}".format(title)}
    title = json.dumps(title)
    server.execute('scoreboard objectives remove {}'.format(scbd_name))
    server.execute('scoreboard objectives add {} minecraft.{}:minecraft.{} {}'.format(scbd_name, cls, target, title))
    for name, uuid in player_list.items():
        flag = True
        try:
            try:
                value = gpsinoff(uuid=uuid)[suf(cls)][suf(target)]
            except KeyError:
                flag = False
        except TypeError:
            flag = False
        if flag:
            server.execute('scoreboard players set {} {} {}'.format(name, scbd_name, value))
    if is_show:
        server.execute('scoreboard objectives setdisplay sidebar {}'.format(scbd_name))


def set_display_scoreboard(server, info, to_show_scoreboard_name=''):  # set_display
    server.execute('scoreboard objectives setdisplay sidebar {}'.format(to_show_scoreboard_name))


def spawn_total_dig_dummy():  #
    global meaningful_scoreboard, meaningless_scoreboard, dummy_list
    meaningful_scoreboard = {}
    meaningless_scoreboard = {}
    dummy_list = []
    temp_v = ''
    time = 0
    for abb in tool_list['normal'].values():
        temp_v += abb
        time += 1
        if time > 1:
            dummy_list.append(temp_v)
    for abb in resource_list.values():
        meaningless_scoreboard[abb] = []
    for abb in resource_list.values():
        meaningful_scoreboard[abb] = {}
    for resource, resource_abb in resource_list.items():
        for tool, tool_abb in tool_list['normal'].items():
            meaningful_scoreboard[resource_abb]['{}{}'.format(resource_abb, tool_abb)] = '{}_{}'.format(resource, tool)
        for dummy in dummy_list:
            meaningless_scoreboard[resource_abb].append('{}{}'.format(resource_abb, dummy))
    for tool, tool_abb in tool_list['unusual'].items():
        meaningful_scoreboard[tool_abb] = {tool_abb: tool}
    dummy_list = []
    temp_v = ''
    time = 0
    for abb in resource_list.values():
        temp_v += abb
        time += 1
        if time > 1:
            dummy_list.append(temp_v)
    for abb in tool_list['unusual'].values():
        temp_v += abb
        time += 1
        if time > 1:
            dummy_list.append(temp_v)


def write_total_dig_datapacks():  #
    global datapack_command, meaningless_scoreboard
    datapack_command = [
        'scoreboard objectives modify d_' + total_stats_scoreboard_name + ' displayname [{"text":"挖掘总榜","color":"red","bold":true,"italic":false,"underlined":false,"strikethrough":false,"obfuscated":false}]'
    ]
    temp_meaningless_scoreboard = {}
    for key, value in meaningless_scoreboard.items():
        temp_meaningless_scoreboard[key] = 'd_{}'.format(value[-1])
    for item, abb in tool_list['unusual'].items():
        temp_meaningless_scoreboard[abb] = 't_{}'.format(abb)
    for resource_abb, value in meaningless_scoreboard.items():
        flag = True
        for x in range(len(value)):
            if flag:
                datapack_command.append('execute as @a at @s run scoreboard players operation @s d_{} = @s t_{}'.format(value[x], list(meaningful_scoreboard[resource_abb].keys())[x]))
                datapack_command.append('execute as @a at @s run scoreboard players operation @s d_{} += @s t_{}'.format(value[x], list(meaningful_scoreboard[resource_abb].keys())[x + 1]))
                flag = False
            else:
                datapack_command.append('execute as @a at @s run scoreboard players operation @s d_{} = @s d_{}'.format(value[x], value[x - 1]))
                datapack_command.append('execute as @a at @s run scoreboard players operation @s d_{} += @s t_{}'.format(value[x], list(meaningful_scoreboard[resource_abb].keys())[x + 1]))
    flag = True
    for x in range(len(dummy_list)):
        if flag:
            datapack_command.append('execute as @a at @s run scoreboard players operation @s d_{} = @s {}'.format(dummy_list[x], list(temp_meaningless_scoreboard.values())[x]))
            datapack_command.append('execute as @a at @s run scoreboard players operation @s d_{} += @s {}'.format(dummy_list[x], list(temp_meaningless_scoreboard.values())[x + 1]))
            flag = False
        else:
            datapack_command.append('execute as @a at @s run scoreboard players operation @s d_{} = @s d_{}'.format(dummy_list[x], dummy_list[x - 1]))
            datapack_command.append('execute as @a at @s run scoreboard players operation @s d_{} += @s {}'.format(dummy_list[x], list(temp_meaningless_scoreboard.values())[x + 1]))
    datapack_command.append('execute as @a at @s run scoreboard players operation @s d_{} = @s d_{}'.format(total_stats_scoreboard_name, dummy_list[x]))
    datapack_command.append('execute as @a[scores={d_' + total_stats_scoreboard_name + '=0}] at @s run scoreboard players reset @s d_' + total_stats_scoreboard_name)
    try:
        os.makedirs('{}datapacks/{}{}/data/example_pack/functions'.format(world_path, plugin_name, total_stats_scoreboard_name))
        os.makedirs('{}datapacks/{}{}/data/minecraft/tags/functions'.format(world_path, plugin_name, total_stats_scoreboard_name))
    except FileExistsError:
        None
    open('{}datapacks/{}{}/pack.mcmeta'.format(world_path, plugin_name, total_stats_scoreboard_name), 'w').write(json.dumps({"pack": {"pack_format": 4, "description": ""}}, indent=4))
    open('{}datapacks/{}{}/data/example_pack/functions/tick.mcfunction'.format(world_path, plugin_name, total_stats_scoreboard_name), 'w', encoding='utf-8').write('\n'.join(datapack_command))
    open('{}datapacks/{}{}/data/minecraft/tags/functions/tick.json'.format(world_path, plugin_name, total_stats_scoreboard_name), 'w').write(json.dumps({"values": ["example_pack:tick"]}, indent=4))
    time.sleep(0.01)


def gpsinoff(uuid):
    global pl_stats
    if uuid == None:
        return None
    return pl_stats[uuid]


def gpsinoffgeninst():
    global pl_stats
    pl_stats = {}
    for filename in os.listdir(os.path.join(world_path, 'stats')):
        with open(os.path.join(world_path, 'stats', filename), 'r') as st_f:
            js = json.load(st_f)['stats']
        pl_stats[filename.split('.')[0]] = js


def switch_total_dig_scoreboard(server, info, is_make, list_bot, is_called=False):  # make/ clear
    player_list = get_player_list(list_bot)
    save_all(server)
    gpsinoffgeninst()
    if is_make:
        switch_total_dig_scoreboard(server, info, False, list_bot, True)
        spawn_total_dig_dummy()
        write_total_dig_datapacks()
        server.execute('reload')
        server.execute('datapack enable "file/{}{}"'.format(plugin_name, total_stats_scoreboard_name))
        server.execute('scoreboard objectives add d_{} dummy'.format(total_stats_scoreboard_name))
        server.execute('scoreboard objectives setdisplay sidebar d_{}'.format(total_stats_scoreboard_name))
        for value in meaningful_scoreboard.values():
            for abb, tool in value.items():
                build_scoreboard(server, info, 'used', tool, scbd_name='t_{}'.format(abb), is_show=False)
        for name, uuid in player_list.items():
            sum = 0
            for value in meaningful_scoreboard.values():
                for abb, tool in value.items():
                    try:
                        value = gpsinoff(uuid=uuid)[suf('used')][suf(tool)]
                    except:
                        value = None
                    if value is not None:
                        sum += value
            if sum:
                server.execute('scoreboard players set {} d_{} {}'.format(name, total_stats_scoreboard_name, sum))
        for dummy in dummy_list:
            server.execute('scoreboard objectives add d_{} dummy'.format(dummy))
        for value in meaningless_scoreboard.values():
            for dummy in value:
                server.execute('scoreboard objectives add d_{} dummy'.format(dummy))
        time.sleep(0.01)
        print_plugin_message(server, info, '成功创建全工具计分板')
    else:
        server.execute('datapack disable "file/{}{}"'.format(plugin_name, total_stats_scoreboard_name))
        for value in meaningful_scoreboard.values():
            for abb, tool in value.items():
                server.execute('scoreboard objectives remove t_{}'.format(abb))
        for dummy in dummy_list:
            server.execute('scoreboard objectives remove d_{}'.format(dummy))
        for value in meaningless_scoreboard.values():
            for dummy in value:
                server.execute('scoreboard objectives remove d_{}'.format(dummy))
        server.execute('scoreboard objectives remove d_{}'.format(total_stats_scoreboard_name))
        if not is_called:
            print_plugin_message(server, info, '成功关闭全工具计分板')


def write_total_mine_datapacks():
    datapack_command = [
        'scoreboard objectives modify v_' + total_mined_scorebaord_name + ' displayname [{"text":"真·挖掘总榜","color":"red","bold":true,"italic":false,"underlined":false,"strikethrough":false,"obfuscated":false}]'
    ]
    abb_list = list(mined_item.values())
    flag = True
    for x in range(len(ant_list)):
        if flag:
            datapack_command.append('execute as @a at @s run scoreboard players operation @s v_{} = @s m_{}'.format(ant_list[x], abb_list[x]))
            datapack_command.append('execute as @a at @s run scoreboard players operation @s v_{} += @s m_{}'.format(ant_list[x], abb_list[x + 1]))
            flag = False
        else:
            datapack_command.append('execute as @a at @s run scoreboard players operation @s v_{} = @s v_{}'.format(ant_list[x], ant_list[x - 1]))
            datapack_command.append('execute as @a at @s run scoreboard players operation @s v_{} += @s m_{}'.format(ant_list[x], abb_list[x + 1]))
    datapack_command.append('execute as @a at @s run scoreboard players operation @s v_{} = @s v_{}'.format(total_mined_scorebaord_name, ant_list[x]))
    datapack_command.append('execute as @a[scores={v_' + total_mined_scorebaord_name + '=0}] at @s run scoreboard players reset @s v_' + total_mined_scorebaord_name)
    try:
        os.makedirs('{}datapacks/{}{}/data/example_pack/functions'.format(world_path, plugin_name, total_mined_scorebaord_name))
        os.makedirs('{}datapacks/{}{}/data/minecraft/tags/functions'.format(world_path, plugin_name, total_mined_scorebaord_name))
    except FileExistsError:
        None
    open('{}datapacks/{}{}/pack.mcmeta'.format(world_path, plugin_name, total_mined_scorebaord_name), 'w').write(json.dumps({"pack": {"pack_format": 4, "description": ""}}, indent=4))
    open('{}datapacks/{}{}/data/example_pack/functions/tick.mcfunction'.format(world_path, plugin_name, total_mined_scorebaord_name), 'w', encoding='utf-8').write('\n'.join(datapack_command))
    open('{}datapacks/{}{}/data/minecraft/tags/functions/tick.json'.format(world_path, plugin_name, total_mined_scorebaord_name), 'w').write(json.dumps({"values": ["example_pack:tick"]}, indent=4))
    time.sleep(0.01)


def switch_total_mine_scoreboard(server, info, is_make, list_bot, is_called=False):
    global ant_list
    player_list = get_player_list(list_bot)
    save_all(server)
    abb_list = list(mined_item.values())
    ant_list = []
    gpsinoffgeninst()
    for x in range(len(abb_list)):
        try:
            ant_list.append(abb_list[x] + abb_list[x + 1])
        except:
            None
    if is_make:
        # switch_total_mine_scoreboard(server, info, False, list_bot, True)
        write_total_mine_datapacks()
        server.execute('reload')
        server.execute('datapack enable "file/{}{}"'.format(plugin_name, total_mined_scorebaord_name))
        server.execute('scoreboard objectives add v_{} dummy'.format(total_mined_scorebaord_name))
        server.execute('scoreboard objectives setdisplay sidebar v_{}'.format(total_mined_scorebaord_name))
        for block, abb in mined_item.items():
            server.execute('scoreboard objectives add {} minecraft.{}:minecraft.{}'.format('m_{}'.format(abb), 'mined', block))
        for block, abb in mined_item.items():
            build_scoreboard(server, info, 'mined', block, scbd_name='m_{}'.format(abb), is_show=False)
        for name, uuid in player_list.items():
            sum = 0
            for block, abb in mined_item.items():
                try:
                    value = gpsinoff(uuid=uuid)[suf('mined')][suf(block)]
                except TypeError:
                    value = None
                except KeyError:
                    value = None
                if value is not None:
                    sum += value
            if sum:
                server.execute('scoreboard players set {} v_{} {}'.format(name, total_mined_scorebaord_name, sum))
        for dummy in ant_list:
            server.execute('scoreboard objectives add v_{} dummy'.format(dummy))
        time.sleep(0.01)
        print_plugin_message(server, info, '成功创建全工具计分板')
    else:
        server.execute('datapack disable "file/{}{}"'.format(plugin_name, total_mined_scorebaord_name))
        for block, abb in mined_item.items():
            server.execute('scoreboard objectives remove m_{}'.format(abb))
        for dummy in ant_list:
            server.execute('scoreboard objectives remove v_{}'.format(dummy))
        server.execute('scoreboard objectives remove v_{}'.format(total_mined_scorebaord_name))
        if not is_called:
            print_plugin_message(server, info, '成功关闭全工具计分板')


def sum_players(filelist=os.listdir(os.path.join(world_path, 'stats'))):  #
    for x in range(len(filelist)):
        if filelist[x].find('.json') == -1:
            filelist[x] += '.json'
    temp_dict = {}
    flag = True
    for x in range(2):
        for filename in filelist:
            try:
                for cls, target in json.load(open(os.path.join(world_path, 'stats', filename), 'r'))['stats'].items():
                    for item, value in target.items():
                        if flag:
                            temp_dict['{}.{}'.format(cls.replace('minecraft:', ''), item.replace('minecraft:', ''))] = 0
                        else:
                            temp_dict['{}.{}'.format(cls.replace('minecraft:', ''), item.replace('minecraft:', ''))] += value
            except json.decoder.JSONDecodeError:
                None
        flag = False
    output = {"stats": {}, "DataVersion": 2230}
    for key, value in temp_dict.items():
        output['stats'][suf(key.split('.')[0])] = {}
    for key, value in temp_dict.items():
        output['stats'][suf(key.split('.')[0])][suf(key.split('.')[1])] = value
    return output


def read_config(server, info):  #
    try:
        return json.load(open(os.path.join(config_path, 'config.json'), 'r'))
    except FileNotFoundError:
        print_plugin_message(server, info, '找不到配置文件')


def write_config(arg):  #
    open(os.path.join(config_path, 'config.json'), 'w').write(json.dumps(arg, indent=4))


def generate_sum_file(server, info, note=None):  # sum
    time = getday()
    open(os.path.join(config_path, 'sum', '{}{}.json'.format(time, '-{}'.format(note) if note != None else '')), 'w').write(json.dumps(sum_players(), indent=4))
    print_plugin_message(server, info, '成功生成sum文件, 文件路径:')
    print_message(server, info, os.path.join(config_path, 'sum', '{}{}.json'.format(time, '-{}'.format(note) if note != None else '')))
    config = read_config(server, info)
    config['sumlist'][time] = {'note': note, 'time': time, 'name': '{}{}.json'.format(time, '-{}'.format(note) if note != None else '')}
    write_config(config)


def generate_record_file(server, info, note=None):  # record
    time = getday()
    try:
        os.makedirs(os.path.join(config_path, 'record', '{}{}'.format(time, '-{}'.format(note) if note != None else '')))
    except FileExistsError:
        print_plugin_message(server, info, '创建record文件失败, 存在同名文件夹')
        return
    for filename in os.listdir(os.path.join(world_path, 'stats')):
        shutil.copyfile(os.path.join(world_path, 'stats', filename), os.path.join(config_path, 'record', '{}{}'.format(time, '-{}'.format(note) if note != None else ''), filename))
    print_plugin_message(server, info, '成功生成record文件, 文件路径')
    print_message(server, info, os.path.join(config_path, 'record', '{}{}'.format(time, '-{}'.format(note) if note != None else '')))
    config = read_config(server, info)
    config['recordlist'][time] = {'note': note, 'time': time, 'name': '{}{}'.format(time, '-{}'.format(note) if note != None else '')}
    write_config(config)


def del_file(server, info, is_sum_or_record, time, is_called=False):  # del
    config = read_config(server, info)
    if is_sum_or_record == 'sum':
        os.remove(os.path.join(config_path, is_sum_or_record, config['{}list'.format(is_sum_or_record)][time]['name']))
    else:
        shutil.rmtree(os.path.join(config_path, is_sum_or_record, config['{}list'.format(is_sum_or_record)][time]['name']))
    if not is_called: print_plugin_message(server, info, '成功删除{}'.format(os.path.join(config_path, is_sum_or_record, config['{}list'.format(is_sum_or_record)][time][name])))
    config['{}list'.format(is_sum_or_record)].pop(time)
    write_config(config)


def del_all_file(server, info):  # del_all
    for key in ['sumlist', 'recordlist']:
        for k, v in read_config(server, info)[key].items():
            del_file(server, info, key.replace('list', ''), v['time'], True)
            print_plugin_message(server, info, '成功删除{} ({})'.format(v['name'], k.replace('list', '')))


def del_player(server, info, name):  # del_player
    player_list = get_player_list()
    os.remove(os.path.join(world_path, 'stats', '{}.json'.format(player_list[name])))
    print_plugin_message(server, info, '成功删除{}的统计数据'.format(name))


def change_stats(server, info, cls1, target1, cls2, target2):  # change
    for filename in os.path.join(world_path, 'stats'):
        stats = json.load(open(os.path.join(world_path, 'stats', filename), 'r'))
        stats['stats'][suf(cls2)][suf(target2)] = stats['stats'][suf(cls1)][suf(target1)]
        stats['stats'][suf(cls1)].pop(suf(target1))
        open(os.path.join(world_path, 'stats', filename), 'w').write(json.dumps(stats))
    print_plugin_message(server, info, '成功将所有玩家统计数据中的{}:{}转移到{}:{}'.format(cls1, target1, cls2, target2))


def minus_stats_file(path1, path2):  #
    output = {"stats": {}, "DataVersion": 2230}
    temp_dict = {}
    try:
        sum1 = json.load(open(path1, 'r'))['stats']
        sum2 = json.load(open(path2, 'r'))['stats']
    except:
        return
    flag = False
    for sum_stats in [sum2, sum1]:
        for cls, target in sum_stats.items():
            for item, value in target.items():
                if not flag:
                    temp_dict['{}.{}'.format(cls.replace('minecraft:', ''), item.replace('minecraft:', ''))] = value
                else:
                    temp_dict['{}.{}'.format(cls.replace('minecraft:', ''), item.replace('minecraft:', ''))] -= value
                    if temp_dict['{}.{}'.format(cls.replace('minecraft:', ''), item.replace('minecraft:', ''))] < 0:
                        temp_dict['{}.{}'.format(cls.replace('minecraft:', ''), item.replace('minecraft:', ''))] = 0 - temp_dict[
                            '{}.{}'.format(cls.replace('minecraft:', ''), item.replace('minecraft:', ''))]
        flag = True
    temp_temp_dict = json.loads(json.dumps(temp_dict))
    for key, value in temp_temp_dict.items():
        if not value:
            temp_dict.pop(key)
    for key, value in temp_dict.items():
        output['stats'][suf(key.split('.')[0])] = {}
    for key, value in temp_dict.items():
        output['stats'][suf(key.split('.')[0])][suf(key.split('.')[1])] = value
    return output


def generate_minus_dict(server, info, is_sum_or_record, time1, time2):  #
    non_use_list = []
    if int(time1.replace('-', '')) > int(time2.replace('-', '')):
        non_use_list.append(time2)
        time2 = time1
        time1 = non_use_list[0]
    time = getday()
    config = read_config(server, info)
    if is_sum_or_record == 'sum':
        return_list = {'time1': time1, 'time2': time2, 'type': is_sum_or_record, 'output': ''}
        return_list['output'] = minus_stats_file(
            os.path.join(
                config_path,
                is_sum_or_record,
                config['{}list'.format(is_sum_or_record)][time1]['name']
            ),
            os.path.join(
                config_path,
                is_sum_or_record,
                config['{}list'.format(is_sum_or_record)][time2]['name']
            )
        )
    elif is_sum_or_record == 'record':
        return_list = {'time1': time1, 'time2': time2, 'type': is_sum_or_record, 'output': {}}
        for x in os.listdir(os.path.join(config_path, is_sum_or_record, config['{}list'.format(is_sum_or_record)][time2]['name'])):
            return_list['output'][x] = minus_stats_file(
                os.path.join(
                    config_path,
                    is_sum_or_record,
                    config['{}list'.format(is_sum_or_record)][time1]['name'],
                    x
                ),
                os.path.join(
                    config_path,
                    is_sum_or_record,
                    config['{}list'.format(is_sum_or_record)][time2]['name'],
                    x
                )
            )
    return return_list


def generate_minus_file(server, info, is_sum_or_record, time1, time2):  # minus
    minus_dict = generate_minus_dict(server, info, is_sum_or_record, time1, time2)
    name = '{}({}~{})'.format(getday(), time1, time2)
    if minus_dict['type'] == 'record':
        for filename, stats in minus_dict['output'].items():
            open(os.path.join(config_path, 'minus', is_sum_or_record, name, filename), 'w').write(json.dumps(stats, indent=4))
    elif minus_dict['type'] == 'sum':
        open(os.path.join(config_path, 'minus', is_sum_or_record, '{}.json'.format(name)), 'w').write(json.dumps(minus_dict['output'], indent=4))
    print_plugin_message(server, info, '成功生成{}与{}之间的{}:minus文件, 文件路径:'.format(time1, time2, is_sum_or_record))
    print_message(server, info, os.path.join(config_path, 'minus', is_sum_or_record, name))


def view_list(server, info, is_sum_or_record):  # list
    config = read_config(server, info)
    if is_sum_or_record in ['sum', 'record']:
        if config['{}list'.format(is_sum_or_record)] == {}:
            print_message(server, info, '没有已生成的{}文件'.format(is_sum_or_record))
            return
        print_message(server, info, '{}文件如下:'.format(is_sum_or_record))
        for file_info in config['{}list'.format(is_sum_or_record)].values():
            print_message(server, info, '时间: {}, 注释: {}, 文件(夹)名: {}'.format(file_info['time'], file_info['note'], file_info['name']))
    elif is_sum_or_record == 'all':
        for i in ['sum', 'record']:
            view_list(server, info, i)


def sumtoplayer_add_input(server, info, name):  # sumtoplayer add_input
    config = read_config(server, info)
    if name not in config['sumtoplayer']['inputplayerlist']:
        config['sumtoplayer']['inputplayerlist'].append(name)
    write_config(config)
    print_plugin_message(server, info, '成功将{}添加至输入列表'.format(name))


def sumtoplayer_set_output(server, info, name):  # sumtoplayer set_output
    config = read_config(server, info)
    if name != config['sumtoplayer']['outputplayer']:
        config['sumtoplayer']['outputplayer'] = name
    write_config(config)
    print_plugin_message(server, info, '成功将{}设置为输出玩家'.format(name))


def sumtoplayer_execute(server, info):  # sumtoplayer execute
    config = read_config(server, info)
    player_list = get_player_list()
    as_output = config['sumtoplayer']['outputplayer']
    as_input = config['sumtoplayer']['inputplayerlist']
    if as_output == '':
        return
    as_input = list(set(as_input))
    for x in range(len(as_input)):
        if '' == as_input[x]:
            as_input.pop(x)
            break
    if as_output not in as_input:
        as_input.append(as_output)
    if len(as_input) < 2:
        return
    filelist = []
    for name in as_input:
        filelist.append('{}.json'.format(player_list[name]))
    output_dict = sum_players(filelist)
    for filename in filelist:
        os.remove(os.path.join(world_path, 'stats', filename))
    open(os.path.join(world_path, 'stats', '{}.json'.format(player_list[as_output])), 'w').write(json.dumps(output_dict))
    config['sumtoplayer']['inputplayerlist'] = []
    write_config(config)
    print_plugin_message(server, info, '成功将{}的统计数据合并到{}'.format(', '.join(as_input), as_output))


def sumtoplayer_clear_input(server, info):  # sumtoplayer clear
    config = read_config(server, info)
    config['sumtoplayer']['inputplayerlist'] = []
    print_plugin_message(server, info, '成功将输入列表与输出玩家清空')
    write_config(config)


def sumtoplayer_del_input(server, info, name):  # sumtoplayer del_input
    config = read_config(server, info)
    if name in config['sumtoplayer']['inputplayerlist']:
        for x in range(len(config['sumtoplayer']['inputplayerlist'])):
            if name == config['sumtoplayer']['inputplayerlist'][x]:
                config['sumtoplayer']['inputplayerlist'].pop(x)
                break
    write_config(config)
    print_plugin_message(server, info, '成功将{}从输入列表中删除'.format(name))


def sumtoplayer_view_list(server, info):  # sumtoplayer list
    cfd = read_config(server, info)
    print_message(server, info, '§r§7------输入列表------')
    for name in cfd['sumtoplayer']['inputplayerlist']:
        print_message(server, info, '§l§r§l - §r§7{}'.format(name))
    print_message(server, info, '§r§7------输出玩家------')
    if cfd['sumtoplayer']['outputplayer'] != '':
        print_message(server, info, '§l§r§l - §r§7{}'.format(cfd['sumtoplayer']['outputplayer']))
    print_message(server, info, '§r§7----------------')


def initialization():
    for i in [os.path.join(config_path, 'record'), os.path.join(config_path, 'sum')]:
        if not os.path.exists(i):
            os.makedirs(i)
    if not os.path.exists(os.path.join(config_path, 'config.json')):
        open(os.path.join(config_path, 'config.json'), 'w').write(json.dumps({"sumlist": {}, "recordlist": {}, "sumtoplayer": {"inputplayerlist": [], "outputplayer": ""}}, indent=4))


def on_info(server, info):
    is_bot_in = info.content.find('-bot') >= 0
    command = info.content.replace('-bot', '').replace('&', '§').split()
    lencommand = len(command)

    if not lencommand:
        return
    if lencommand == 1 and command[0] in tip_prefix:
        if command[0] != prefix:
            print_plugin_message(server, info, '请使用{}!'.format(prefix))
            return
    if command[0] != prefix:
        return
    if lencommand == 1 and command[0] == prefix:
        print_message(server, info, help_message[0])
        return
    if lencommand == 3 and command[0] == prefix and command[1] == 'help':
        try:
            print_message(server, info, help_message[int(command[2]) - 1])
        except ValueError:
            print_message(server, info, help_message[command[2]])
        return
    if lencommand >= 2 and command[0] == prefix:
        try:
            if command[1] in commandlist["permission_required"] and server.get_permission_level(info) < 2:
                print_plugin_message(server, info, '§c权限不足！§r')
                return
        except TypeError:
            return
    initialization()
    spawn_total_dig_dummy()

    # !!sp query <ID> <cls> <target>
    if command[1] == 'query' and lencommand == 5:
        save_all(server)
        query_stats(server, info, command[2], command[3], command[4])

    # !!sp rank <cls> <target> [rank_amount] [-bot]
    if command[1] == 'rank' and lencommand in [4, 5]:
        save_all(server)
        r_a = int(command[4]) if lencommand == 5 else 15
        rank(server, info, command[2], command[3], r_a, is_bot_in)

    # !!sp save
    if command[1] == 'save' and lencommand == 2:
        save_all(server)
        print_plugin_message(server, info, '成功保存')

    # !!sp scoreboard <cls> <target> [title] [-bot]
    if command[1] == 'scoreboard' and lencommand in [4, 5]:
        gpsinoffgeninst()
        save_all(server)
        title = command[4] if lencommand == 5 else None
        build_scoreboard(server, info, command[2], command[3], is_bot_in_board=is_bot_in, title=title, is_show=True, scbd_name=scoreboard_name)

    # !!sp create <cls> <target> <ID> [title]  [-bot]
    if command[1] == 'create' and lencommand in [5, 6]:
        save_all(server)
        title = command[5] if lencommand == 6 else None
        build_scoreboard(server, info, command[2], command[3], is_bot_in_board=is_bot_in, title=title, scbd_name=command[4])

    # !!sp set_display <ID>
    if command[1] == 'set_display' and lencommand in [2, 3]:
        scoreboard_ID = command[2] if lencommand == 3 else ''
        set_display_scoreboard(server, info, scoreboard_ID)

    # !!sp make
    if command[1] == 'make' and lencommand == 2:
        switch_total_dig_scoreboard(server, info, True, True)

    # !!sp make
    if command[1] == 'make_mined' and lencommand == 2:
        switch_total_mine_scoreboard(server, info, True, True)

    # !!sp clear
    if command[1] == 'clear' and lencommand == 2:
        switch_total_dig_scoreboard(server, info, False, True)

    # !!sp clear_mined
    if command[1] == 'clear_mined' and lencommand == 2:
        switch_total_mine_scoreboard(server, info, False, True)

    # !!sp sum [note]
    if command[1] == 'sum' and lencommand in [2, 3]:
        save_all(server)
        note = command[2] if lencommand == 3 else None
        generate_sum_file(server, info, note=note)

    # !!sp record [note]
    if command[1] == 'record' and lencommand in [2, 3]:
        save_all(server)
        note = command[2] if lencommand == 3 else None
        generate_record_file(server, info, note=note)

    # !!sp del <record/sum> <file_name>
    if command[1] == 'del' and lencommand == 4:
        del_file(server, info, command[2], command[3])

    # !!sp del_all
    if command[1] == 'del_all' and lencommand == 2:
        del_all_file(server, info)

    # !!sp del_player <ID>
    if command[1] == 'del_player' and lencommand == 3:
        del_player(server, info, command[2])

    # !!sp change <cls1> <target1> <cls2> <target2>
    if command[1] == 'change' and lencommand == 6:
        save_all(server)
        change_stats(server, info, command[2], command[3], command[4], command[5])

    # !!sp minus <sum/record> <time1> <time2>
    if command[1] == 'minus' and lencommand == 5:
        generate_minus_file(server, info, command[2], command[3], command[4])

    # !!sp list <sum/record>
    if command[1] == 'list' and lencommand == 3:
        view_list(server, info, command[2])

    # !!sp sumtoplayer
    if command[1] == 'sumtoplayer':
        # add_input <ID>
        if command[2] == 'add_input' and lencommand == 4: sumtoplayer_add_input(server, info, command[3])
        # set_output <ID>
        if command[2] == 'set_output' and lencommand == 4: sumtoplayer_set_output(server, info, command[3])
        # execute
        if command[2] == 'execute' and lencommand == 3:
            save_all(server)
            sumtoplayer_execute(server, info)
        # clear
        if command[2] == 'clear' and lencommand == 3: sumtoplayer_clear_input(server, info)
        # del_input <ID>
        if command[2] == 'del_input' and lencommand == 4: sumtoplayer_del_input(server, info, command[3])
        # list
        if command[2] == 'list' and lencommand == 3: sumtoplayer_view_list(server, info)
