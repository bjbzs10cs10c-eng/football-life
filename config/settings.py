"""《Football Life：我的足球生涯》全局配置中心（A1）。

所有可调数值统一放在这里，方便平衡调整。
程序启动（main.py）与测试都会调用 validate_config()，
确保配置与代码保持一致，防止配置漂移。
"""

from __future__ import annotations

# --------------------------------------------------------------------------
# 基础
# --------------------------------------------------------------------------
GAME_TITLE = "Football Life：我的足球生涯"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

# --------------------------------------------------------------------------
# 属性系统（PRD §5，共 15 项）
# --------------------------------------------------------------------------
ATTRIBUTE_TECHNICAL = ["shooting", "passing", "dribbling", "control", "defending", "heading"]
ATTRIBUTE_PHYSICAL = ["pace", "acceleration", "strength", "stamina", "agility"]
ATTRIBUTE_MENTAL = ["decision", "professionalism", "pressure", "leadership"]

ALL_ATTRIBUTES = ATTRIBUTE_TECHNICAL + ATTRIBUTE_PHYSICAL + ATTRIBUTE_MENTAL

MIN_ATTRIBUTE = 1
MAX_ATTRIBUTE = 100

# 综合能力权重（PRD §6）：技术 40% + 身体 30% + 心理 30%
OVERALL_WEIGHT_TECHNICAL = 0.40
OVERALL_WEIGHT_PHYSICAL = 0.30
OVERALL_WEIGHT_MENTAL = 0.30

# 属性中文名（UI 展示用）
ATTRIBUTE_NAMES_ZH = {
    "shooting": "射门",
    "passing": "传球",
    "dribbling": "盘带",
    "control": "控球",
    "defending": "防守",
    "heading": "头球",
    "pace": "速度",
    "acceleration": "爆发",
    "strength": "力量",
    "stamina": "耐力",
    "agility": "敏捷",
    "decision": "决策",
    "professionalism": "职业态度",
    "pressure": "抗压",
    "leadership": "领导力",
}

# --------------------------------------------------------------------------
# 位置系统（PRD §4.2，MVP 不支持 GK）
# --------------------------------------------------------------------------
# WING 对应 PRD 的 LW/RW（边锋）
POSITION_CODES = ["ST", "WING", "CM", "CB"]
POSITION_NAMES_ZH = {
    "ST": "前锋",
    "WING": "边锋",
    "CM": "中场",
    "CB": "后卫",
}

# 位置初始加成（未定义属性已按确认方案映射，不新增属性）：
# PRD 的「视野」→ decision（CM）
POSITION_BONUSES = {
    "ST": {"shooting": 5, "pace": 3},
    "WING": {"pace": 5, "dribbling": 5},
    "CM": {"passing": 5, "decision": 5},
    "CB": {"defending": 5, "strength": 5},
}

# 惯用脚
FOOT_OPTIONS = ["L", "R"]
FOOT_NAMES_ZH = {"L": "左脚", "R": "右脚"}

# --------------------------------------------------------------------------
# 球员初始值
# --------------------------------------------------------------------------
START_AGE = 17                  # 已确认：固定 17 岁
START_MONEY = 1000
START_REPUTATION = 10
START_CONDITION = 100           # 体力（行动资源，独立于“耐力”属性）
MAX_CONDITION = 100
MIN_CONDITION = 0
RETIRE_AGE = 35                 # 赛季末年龄达到则触发退役评价

# 初始属性随机范围（B4 使用）
INITIAL_ATTRIBUTE_MIN = 50
INITIAL_ATTRIBUTE_MAX = 70

# --------------------------------------------------------------------------
# 训练系统（PRD §7.2 / TDD §7，MVP 四类）
# --------------------------------------------------------------------------
TRAINING_TYPES = {
    "TECHNICAL": {
        "name_zh": "技术训练",
        "attributes": ["shooting", "passing"],
        "gain_min": 1,
        "gain_max": 3,
        "condition_cost": 15,
        "injury_chance_percent": 0,
    },
    "PHYSICAL": {
        "name_zh": "体能训练",
        "attributes": ["pace", "strength", "stamina"],
        "gain_min": 1,
        "gain_max": 3,
        "condition_cost": 20,
        "injury_chance_percent": 5,
    },
    "TACTICAL": {
        "name_zh": "战术训练",
        # PRD 的 positioning → decision
        "attributes": ["decision"],
        "gain_min": 1,
        "gain_max": 3,
        "condition_cost": 10,
        "injury_chance_percent": 0,
    },
    "REST": {
        "name_zh": "休息",
        "attributes": [],
        "gain_min": 0,
        "gain_max": 0,
        "condition_cost": 0,
        "injury_chance_percent": 0,
    },
}
REST_CONDITION_RESTORE = 30

# --------------------------------------------------------------------------
# 成长系统（TDD §6）
# 成长值 = 基础训练效果 × 职业态度系数 × 年龄系数
# --------------------------------------------------------------------------
# (最小年龄, 最大年龄, 年龄系数)；最大年龄为 None 表示无上限
GROWTH_AGE_BRACKETS = [
    (16, 22, 1.0),
    (23, 28, 0.6),
    (29, None, 0.25),
]
GROWTH_ROUND_STEP = 0.5         # 成长值按 0.5 粒度取整（支持小数累加）

# --------------------------------------------------------------------------
# 比赛系统（TDD §8，公式数值全部配置化）
# --------------------------------------------------------------------------
MATCH_RANDOM_FACTOR = 10        # 进球概率随机幅度（百分点的 ±10）
OPPORTUNITY_RANDOM_FACTOR = 5   # 机会数量的随机因素（PRD 示例 +5）
OPPORTUNITY_CLUB_WEIGHT = 1.0
OPPORTUNITY_PLAYER_WEIGHT = 1.0

# 进球概率 = clamp((射门 - 对手门将能力) × SLOPE + 随机, MIN, MAX)
# 默认 SLOPE=0.05：射门 85 vs 门将 75 时基准为 50%（对应 TDD 示例）
GOAL_PROBABILITY_SLOPE = 0.05
GOAL_PROBABILITY_MIN = 0.05
GOAL_PROBABILITY_MAX = 0.95

# 对手门将能力 = 球队实力 × 系数 + 基础（MVP 无 GK 玩家）
OPPONENT_GK_BASE = 15
OPPONENT_GK_FACTOR = 0.75

# 比赛评分：基础 6 + 进球 + 助攻 + 关键表现 - 失误（TDD §9）
RATING_BASE = 6.0
RATING_GOAL_BONUS = 1.5
RATING_ASSIST_BONUS = 1.0
RATING_KEY_PERF_BONUS = 0.5
RATING_MISTAKE_PENALTY = 0.5
RATING_MIN = 1.0
RATING_MAX = 10.0

MATCH_INTERVAL_DAYS = 7         # 每 7 天一场联赛比赛

# 赛后结算（PRD 核心循环：经验/奖金/声望）
MATCH_WIN_BONUS = 200
MATCH_DRAW_BONUS = 100
MATCH_LOSS_BONUS = 50
MATCH_REPUTATION_GAIN = 2

# --------------------------------------------------------------------------
# 事件系统（PRD §10）
# --------------------------------------------------------------------------
EVENT_TYPES = ["training", "match", "career"]
EVENT_TRIGGER_CHANCE = 0.15     # 每次行动触发事件的概率
EVENT_DATA_FILE = "data/events.json"

# --------------------------------------------------------------------------
# 球队与转会（PRD §11 / TDD §11，门槛全部配置化）
# --------------------------------------------------------------------------
CLUB_TIERS = ["AMATEUR", "LOW_PRO", "TOP_LEAGUE", "ELITE"]
CLUB_TIER_NAMES_ZH = {
    "AMATEUR": "业余球队",
    "LOW_PRO": "低级职业联赛",
    "TOP_LEAGUE": "顶级联赛",
    "ELITE": "欧洲豪门",
}
# 各等级转入门槛（TDD 默认：豪门 Overall≥80 且声望≥70）
TRANSFER_OFFER_RULES = {
    "AMATEUR": {"min_overall": 50, "min_reputation": 20},
    "LOW_PRO": {"min_overall": 65, "min_reputation": 40},
    "TOP_LEAGUE": {"min_overall": 75, "min_reputation": 55},
    "ELITE": {"min_overall": 80, "min_reputation": 70},
}
# 月工资（每 SALARY_PAY_INTERVAL_DAYS 天发放一次）
SALARY_BY_TIER = {
    "AMATEUR": 500,
    "LOW_PRO": 2000,
    "TOP_LEAGUE": 8000,
    "ELITE": 20000,
}
SALARY_PAY_INTERVAL_DAYS = 30

# --------------------------------------------------------------------------
# 时间系统（TDD §13）
# --------------------------------------------------------------------------
DAYS_PER_SEASON = 365
SEASON_START_DATE = "2026-01-01"    # ISO 格式，B10 中转换为 date
LEAGUE_CLUB_COUNT = 6               # 简化联赛球队数

# --------------------------------------------------------------------------
# 荣誉（V1 仅三项：世界杯等随 V2 国家队系统加入）
# --------------------------------------------------------------------------
HONORS_ZH = ["联赛冠军", "杯赛冠军", "金球奖"]

# --------------------------------------------------------------------------
# 数据文件与数据库
# --------------------------------------------------------------------------
CLUBS_DATA_FILE = "data/clubs.json"
DATABASE_PATH = "saves/football_life.db"    # 已确认：saves/football_life.db


def validate_config(settings=None):
    """校验配置一致性，非法配置抛出 ValueError。

    传入 dict 时可对副本做校验（便于测试失败分支）；
    默认校验本模块全局配置。
    """
    s = settings if settings is not None else globals()
    errors = []

    attributes = s["ALL_ATTRIBUTES"]
    if len(attributes) != 15:
        errors.append(f"ALL_ATTRIBUTES 应为 15 项，当前 {len(attributes)} 项")
    if len(set(attributes)) != len(attributes):
        errors.append("ALL_ATTRIBUTES 存在重复属性")
    unknown = [a for a in attributes if a not in s["ATTRIBUTE_NAMES_ZH"]]
    if unknown:
        errors.append(f"以下属性缺少中文名映射: {unknown}")

    if "GK" in s["POSITION_CODES"]:
        errors.append("MVP 不支持 GK 位置")

    for code in s["POSITION_CODES"]:
        if code not in s["POSITION_BONUSES"]:
            errors.append(f"位置 {code} 缺少加成定义")
            continue
        bonus = s["POSITION_BONUSES"][code]
        for attr in bonus:
            if attr not in attributes:
                errors.append(f"位置 {code} 的加成引用了未定义属性: {attr}")

    for name, cfg in s["TRAINING_TYPES"].items():
        for attr in cfg["attributes"]:
            if attr not in attributes:
                errors.append(f"训练 {name} 引用了未定义属性: {attr}")
        if cfg["gain_min"] > cfg["gain_max"]:
            errors.append(f"训练 {name} 的 gain_min 大于 gain_max")

    weight_sum = (
        s["OVERALL_WEIGHT_TECHNICAL"]
        + s["OVERALL_WEIGHT_PHYSICAL"]
        + s["OVERALL_WEIGHT_MENTAL"]
    )
    if abs(weight_sum - 1.0) > 1e-6:
        errors.append(f"综合能力权重之和应为 1.0，当前 {weight_sum}")

    for tier in s["TRANSFER_OFFER_RULES"]:
        if tier not in s["CLUB_TIERS"]:
            errors.append(f"转入门槛包含未定义的球队等级: {tier}")

    if errors:
        raise ValueError("配置校验失败:\n" + "\n".join(errors))
    return True
