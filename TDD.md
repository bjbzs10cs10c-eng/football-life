# TDD（Technical Design Document）

# 《Football Life：我的足球生涯》

## 技术设计文档 V1.0 MVP

---

# 1. 文档信息

| 项目   | 内容                      |
| ---- | ----------------------- |
| 项目名称 | Football Life：我的足球生涯    |
| 版本   | V1.0 MVP                |
| 技术架构 | Python + PyQt6 + SQLite |
| 运行环境 | Windows 10/11           |
| 开发模式 | 单机应用                    |
| 数据存储 | 本地 SQLite               |
| 目标   | 实现可玩的足球职业生涯模拟游戏         |

---

# 2. 系统总体架构

采用**分层架构设计**：


FootballLife
│
├── UI层（PyQt6）
│
├── 游戏逻辑层
│
│   ├── Player System
│   ├── Training System
│   ├── Match Engine
│   ├── Event System
│   ├── Transfer System
│
├── 数据层
│
│   ├── SQLite Database
│   ├── JSON配置文件
│
└── 工具层
    ├── Random
    ├── Calculator
    └── Logger


---

# 3. 项目目录结构

最终目录：


FootballLife/

│
├── main.py                 # 程序入口
│
├── config/
│   └── settings.py         # 游戏参数配置
│
├── database/
│   ├── db.py               # 数据库连接
│   ├── init.sql            # 初始化SQL
│
├── models/
│   ├── player.py           # 球员模型
│   ├── club.py             # 俱乐部模型
│   ├── match.py            # 比赛模型
│   └── event.py            # 事件模型
│
├── systems/
│   ├── training.py         # 训练系统
│   ├── match_engine.py     # 比赛模拟
│   ├── growth.py           # 成长系统
│   ├── transfer.py         # 转会系统
│   └── event_manager.py    # 事件管理
│
├── ui/
│   ├── main_window.py
│   ├── player_page.py
│   ├── match_page.py
│   └── training_page.py
│
├── data/
│   ├── clubs.json
│   ├── events.json
│
└── saves/
    └── career.db


---

# 4. 数据库设计

数据库：


football_life.db


---

# 4.1 player表

保存玩家基本信息。

sql
CREATE TABLE player (

id INTEGER PRIMARY KEY,

name TEXT,

age INTEGER,

nationality TEXT,

height REAL,

position TEXT,

foot TEXT,

club_id INTEGER,

money INTEGER,

reputation INTEGER

);


---

示例：

| 字段         | 值              |
| ---------- | -------------- |
| name       | Li Ming        |
| age        | 17             |
| position   | ST             |
| club       | Shanghai Youth |
| reputation | 10             |

---

# 4.2 player_attributes表

保存能力。

sql
CREATE TABLE player_attributes (

player_id INTEGER,

shooting INTEGER,

passing INTEGER,

dribbling INTEGER,

control INTEGER,

defending INTEGER,

heading INTEGER,

pace INTEGER,

strength INTEGER,

stamina INTEGER,

decision INTEGER,

professionalism INTEGER

);


---

范围：


1-100


---

# 4.3 club表

球队数据。

sql
CREATE TABLE club(

id INTEGER PRIMARY KEY,

name TEXT,

league TEXT,

strength INTEGER,

facility INTEGER,

salary_level INTEGER

);


---

示例：


Barcelona

strength:
90

facility:
95


---

# 4.4 match表

比赛记录。

sql
CREATE TABLE matches(

id INTEGER PRIMARY KEY,

player_id INTEGER,

opponent TEXT,

result TEXT,

goals INTEGER,

assists INTEGER,

rating REAL,

date TEXT

);


---

示例：


vs Arsenal

2-1

Goal:
1

Rating:
8.2


---

# 4.5 career表

生涯统计。

sql
CREATE TABLE career(

player_id INTEGER,

games INTEGER,

goals INTEGER,

assists INTEGER,

trophies INTEGER,

best_award TEXT

);


---

# 4.6 event表

随机事件。

sql
CREATE TABLE events(

id INTEGER PRIMARY KEY,

type TEXT,

description TEXT,

choice_a TEXT,

choice_b TEXT,

effect TEXT

);


---

# 5. 核心类设计

---

# 5.1 Player类

文件：


models/player.py


---

职责：

管理球员状态。

接口：

python
class Player:


    def train():

        pass


    def play_match():

        pass


    def calculate_rating():

        pass


    def age_up():

        pass


---

属性：

python
player.name

player.age

player.attributes

player.club

player.money

player.reputation


---

# 6. 成长系统设计

文件：


systems/growth.py


---

## 属性增长公式

训练收益：


增长值=

基础训练效果

×

职业态度系数

×

年龄系数



---

例如：

17岁：


职业态度 80

训练射门：

+2


---

30岁：

同样训练：


+0.5


---

年龄影响：

| 年龄    | 成长 |
| ----- | -- |
| 16-22 | 高速 |
| 23-28 | 正常 |
| 29+   | 下降 |

---

# 7. 训练系统

文件：


systems/training.py


---

接口：

python
train(player,type)


---

训练类型：

python
TECHNICAL

PHYSICAL

TACTICAL

REST


---

逻辑：

python
if type=="shooting":

    player.shooting += random(1,3)

    stamina -=15


---

# 8. 比赛模拟引擎

核心模块：


match_engine.py


---

## 输入

python
player

opponent

club_strength

player_condition


---

## 输出

python
MatchResult


包含：

python
goals

assists

rating

events


---

# 8.1 比赛流程


开始比赛

↓

计算球队实力

↓

生成个人机会

↓

判断事件

↓

生成评分

↓

保存记录


---

# 8.2 机会计算

公式：


机会数量=

球队攻击力

+

球员能力

+

随机值


---

例如：


球队攻击力:
70


球员进攻:
80


随机:
+5


机会:
155


---

# 8.3 射门事件

公式：


进球概率=

(射门能力-门将能力)

×0.5

+

随机因素


---

例：


射门:

85


门将:

75


基础:

50%



---

# 9. 球员评分系统

比赛评分：

范围：


1-10


计算：


评分=

基础6

+

进球奖励

+

助攻奖励

+

关键表现

-
失误


---

示例：


进球:

+1.5


助攻:

+1


最终:

8.5


---

# 10. 事件系统

文件：


event_manager.py


---

事件结构：

JSON:

json
{

"type":"training",

"text":

"教练发现你的射门天赋",

"choices":[

{

"text":"加练射门",

"effect":

"shooting+3"

}

]

}


---

调用：

python
event=random_event()

show(event)


---

# 11. 转会系统

文件：


transfer.py


---

转会条件：


综合能力

+

声望

+

年龄

+

比赛表现


---

示例：


Overall >80

Reputation >70

↓

豪门邀请


---

# 12. GUI设计

采用：

PyQt6

---

## 主窗口


MainWindow

|
├── 玩家信息
|
├── 当前球队
|
├── 下一场比赛
|
├── 操作按钮
|
├── 新闻窗口



---

按钮：


训练

比赛

转会

查看生涯


---

# 13. 游戏时间系统

采用：


Day


作为最小单位。

一年：


365 Day


---

流程：


点击行动

↓

日期+1

↓

检查事件

↓

进入下一天


---

# 14. 存档系统

采用：

SQLite。

保存：

* 玩家
* 属性
* 球队
* 历史比赛

接口：

python
save_game()

load_game()


---

# 15. 配置系统

文件：


config/settings.py


统一管理：

python
MAX_ATTRIBUTE=100

START_AGE=17

MATCH_RANDOM_FACTOR=10


方便调整平衡。

---

# 16. 开发顺序

## Sprint 1：核心数据

完成：


Player

Database

Save/Load


---

## Sprint 2：游戏逻辑

完成：


Training

Growth

Match Engine


---

## Sprint 3：职业系统

完成：


Club

Transfer

Career


---

## Sprint 4：界面

完成：


PyQt6 UI


---

## Sprint 5：优化

增加：


事件

新闻

平衡调整


---

# 17. 测试要求

## 单元测试

测试：

* 属性增长
* 比赛概率
* 转会条件

例如：

python
def test_training():

    old=player.shooting

    train(player,"shoot")

    assert player.shooting>old


---
