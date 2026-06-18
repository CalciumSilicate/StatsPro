# StatsPro

[![MCDReforged](https://img.shields.io/badge/MCDReforged-2.x-blue)](https://github.com/Fallen-Breath/MCDReforged)
[![Python](https://img.shields.io/badge/Python-3.10+-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

**StatsPro** 是一个功能强大的 MCDReforged 插件，用于管理和展示 Minecraft 玩家统计数据。

## ✨ 功能特性

- 📊 **计分板管理** - 从 stats 文件创建和管理计分板
- 🔍 **数据查询** - 查询单个玩家或全服排行榜数据
- ➕ **加和计分板** - 创建多物品汇总的计分板（如全工具使用量）
- 📁 **数据记录** - 记录玩家数据快照，支持差值分析
- 🔗 **数据合并** - 合并多个玩家的统计数据

## 📦 安装

1. 确保已安装 [MCDReforged](https://github.com/Fallen-Breath/MCDReforged) 2.x
2. 下载 `stats_pro` 目录到 `plugins/` 文件夹
3. 重启 MCDR 或使用 `!!MCDR reload plugin stats_pro`

## 🎮 命令列表

所有命令以 `!!sp` 开头。

### 基础命令

| 命令 | 说明 |
|------|------|
| `!!sp help [页码]` | 查看帮助信息 |
| `!!sp save` | 保存并重载服务器 |
| `!!sp scoreboard <类别> <物品> [显示名]` | 创建计分板 |
| `!!sp set_display [计分板名]` | 设置侧边栏显示 |

### 查询命令

| 命令 | 说明 |
|------|------|
| `!!sp query <玩家> <类别> <物品>` | 查询玩家分数 |
| `!!sp query cls <玩家> <类别> [数量]` | 查询玩家某类别排行 |
| `!!sp query item <玩家> <物品> [数量]` | 查询玩家某物品排行 |

### 排行榜命令

| 命令 | 说明 |
|------|------|
| `!!sp rank <类别> <物品> [数量]` | 查看排行榜 |
| `!!sp rank cls <类别> [数量]` | 查看类别排行 |
| `!!sp rank item <物品> [数量]` | 查看物品排行 |

### 加和计分板命令

| 命令 | 说明 |
|------|------|
| `!!sp sum make [预设名]` | 创建加和计分板 |
| `!!sp sum clear [预设名]` | 清除加和计分板 |
| `!!sp sum create <预设名> [前缀]` | 创建新预设 |
| `!!sp sum remove <预设名>` | 删除预设 |
| `!!sp sum add <预设名> <类别> <物品>` | 添加计分项 |
| `!!sp sum del <预设名> <类别> <物品>` | 删除计分项 |
| `!!sp sum list` | 列出所有预设 |
| `!!sp sum view [预设名]` | 查看预设详情 |

### 数据生成命令

| 命令 | 说明 |
|------|------|
| `!!sp gen sum [备注]` | 生成汇总文件 |
| `!!sp gen record [备注]` | 记录当前数据 |
| `!!sp gen minus <模式> <时间1> <时间2>` | 生成差值文件 |
| `!!sp gen list [模式]` | 列出生成记录 |
| `!!sp gen del <模式> [时间]` | 删除记录 |

### 合并命令 (需要 helper 权限)

| 命令 | 说明 |
|------|------|
| `!!sp merge add <玩家>` | 添加输入玩家 |
| `!!sp merge del <玩家/all>` | 删除输入玩家 |
| `!!sp merge set <玩家>` | 设置输出玩家 |
| `!!sp merge list` | 列出合并配置 |
| `!!sp merge exec` | 执行合并 |

## 📁 项目结构

```
stats_pro/
├── __init__.py          # 插件入口
├── plugin.py            # 插件主类
├── commands.py          # 命令处理
├── config.py            # 配置管理
├── constants.py         # 常量定义
├── models.py            # 数据模型
├── utils.py             # 工具函数
├── stats_service.py     # 统计数据服务
├── scoreboard_service.py # 计分板服务
├── gen_service.py       # 文件生成服务
└── merge_service.py     # 合并服务
```

## ⚙️ 配置文件

配置文件位于 `config/StatsPro/config.json`：

统计数据读取路径会优先使用 Minecraft Java Edition 26.1+ 的新版结构：

- `<MCDR根目录>/server/world/players/stats`

如果新版路径不存在，会回退到旧版结构：

- `<MCDR根目录>/server/world/stats`

```json
{
    "presuppositions": {
        "default": {
            "name": "§c§l挖掘总榜§r",
            "prefix_dummy": "d",
            "prefix_true": "dt",
            "list": {
                "used": {
                    "diamond_pickaxe": "dp",
                    "diamond_axe": "da"
                }
            }
        }
    },
    "gen_list": {
        "sum": {},
        "record": {},
        "minus": {}
    },
    "merge_list": {
        "input": [],
        "output": ""
    }
}
```

## 🔧 UUID 映射

在 `config/StatsPro/uuid.json` 中配置玩家名称与 UUID 的映射：

```json
{
    "PlayerName": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

## 📝 统计类别

支持的统计类别 (`<类别>` 参数)：

- `killed_by` - 被杀死次数
- `killed` - 杀死生物次数
- `custom` - 自定义统计
- `mined` - 挖掘方块
- `used` - 使用物品
- `dropped` - 丢弃物品
- `broken` - 损坏工具
- `picked_up` - 拾取物品
- `crafted` - 合成物品

## 🆕 v2.0.0 更新日志

### 重大重构
- ♻️ 完全重构代码架构，采用模块化设计
- 📝 添加完整的类型注解
- 🌳 使用 MCDR 命令树 API 替代字符串解析
- 🏗️ 分离服务层：配置、统计、计分板、生成、合并

### Bug 修复
- 🐛 修复 `f.write(json.dumps(scores))` 未定义变量错误
- 🐛 修复 `json.load(stats)` 应为 `json.dumps` 的错误
- 🐛 修复类型注解语法错误
- 🐛 修复重复条件判断逻辑
- 🐛 修复 usercache 永远不读取的问题

### 改进
- ✨ 使用 dataclass 定义数据模型
- ✨ 使用 Path 替代字符串路径操作
- ✨ 添加日志系统
- ✨ 改进错误处理

## 📄 许可证

MIT License

## 👤 作者

**CalciumSilicate**

---

*如有问题或建议，欢迎提交 Issue！*
