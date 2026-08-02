"""比赛模拟引擎与赛后结算（B7）。

TDD §8/§9 / PRD §8/§9：
1. 计算对手门将能力；2. 生成个人机会；3. 逐个机会判定射门结果；
4. 生成对手进球与助攻；5. 计算评分；6. 结算奖金/声望/体力。
所有公式数值来自 config/settings.py。
"""

from __future__ import annotations

import random as _random
from dataclasses import dataclass, field

import config.settings as settings
from models.match import MatchRecord
from models.player import Player


@dataclass
class MatchResult:
    """一场模拟比赛的结果与赛后结算数据。"""

    opponent: str
    result: str
    goals: int
    assists: int
    rating: float
    date: str
    outcome: str  # win / draw / loss
    bonus: int
    reputation_gain: int
    condition_cost: int
    events: list = field(default_factory=list)

    def to_record(self) -> MatchRecord:
        """转换为可存档的比赛记录（matches 表字段）。"""
        return MatchRecord(
            opponent=self.opponent,
            result=self.result,
            goals=self.goals,
            assists=self.assists,
            rating=self.rating,
            date=self.date,
        )


def opponent_gk(opponent_strength: float) -> float:
    """对手门将能力 = 球队实力 × 系数 + 基础（MVP 无 GK 玩家）。"""
    return settings.OPPONENT_GK_BASE + opponent_strength * settings.OPPONENT_GK_FACTOR


def goal_probability(shooting: int, gk: float, random_factor: float = 0.0) -> float:
    """单次机会进球概率 = clamp((射门-门将)×SLOPE + 随机, MIN, MAX)。"""
    prob = (shooting - gk) * settings.GOAL_PROBABILITY_SLOPE + random_factor
    return max(
        settings.GOAL_PROBABILITY_MIN,
        min(settings.GOAL_PROBABILITY_MAX, prob),
    )


def opportunity_count(
    club_strength: float,
    shooting: int,
    random_value: int,
    condition: int = settings.MAX_CONDITION,
) -> int:
    """机会数量 = (球队攻击力 + 球员射门 + 随机) ÷ 折算除数 × 体力系数，至少 1 次。"""
    raw = (
        club_strength * settings.OPPORTUNITY_CLUB_WEIGHT
        + shooting * settings.OPPORTUNITY_PLAYER_WEIGHT
        + random_value
    )
    condition_factor = condition / settings.MAX_CONDITION
    return max(
        1, round(raw / settings.OPPORTUNITY_DIVISOR * condition_factor)
    )


def calculate_rating(
    goals: int,
    assists: int,
    key_performance: bool = False,
    mistake: bool = False,
) -> float:
    """比赛评分 = 基础 6 + 进球奖励 + 助攻奖励 + 关键表现 - 失误，截断到 1-10。"""
    rating = (
        settings.RATING_BASE
        + goals * settings.RATING_GOAL_BONUS
        + assists * settings.RATING_ASSIST_BONUS
        + (settings.RATING_KEY_PERF_BONUS if key_performance else 0)
        - (settings.RATING_MISTAKE_PENALTY if mistake else 0)
    )
    return round(
        max(settings.RATING_MIN, min(settings.RATING_MAX, rating)), 1
    )


def play_match(
    player: Player,
    opponent: str,
    club_strength: float,
    opponent_strength: float,
    date: str | None = None,
    rng=None,
) -> MatchResult:
    """模拟一场比赛并完成赛后结算（奖金/声望/体力），返回比赛结果。"""
    if not opponent or not opponent.strip():
        raise ValueError("对手名称不能为空")
    player.validate()
    if rng is None:
        rng = _random
    if date is None:
        date = player.current_date

    shooting = player.attributes["shooting"]
    gk = opponent_gk(opponent_strength)

    random_value = rng.randint(
        -settings.OPPORTUNITY_RANDOM_FACTOR, settings.OPPORTUNITY_RANDOM_FACTOR
    )
    opportunities = opportunity_count(
        club_strength, shooting, random_value, player.condition
    )

    goals = 0
    events = []
    for _ in range(opportunities):
        minute = rng.randint(1, 90)
        prob_random = (
            rng.randint(-settings.MATCH_RANDOM_FACTOR, settings.MATCH_RANDOM_FACTOR)
            / 100
        )
        prob = goal_probability(shooting, gk, prob_random)
        scored = rng.randint(1, 100) <= round(prob * 100)
        if scored:
            goals += 1
            events.append(
                f"第{minute}分钟，{player.name}获得机会"
                f"（射门{shooting} vs 门将{gk:.0f}）→ 进球！"
            )
        else:
            events.append(
                f"第{minute}分钟，{player.name}获得机会"
                f"（射门{shooting} vs 门将{gk:.0f}）→ 射门被扑出"
            )

    opp_goals = max(
        0,
        round(
            (opponent_strength - club_strength) / settings.OPPONENT_GOAL_FACTOR
            + rng.randint(
                -settings.OPPONENT_GOAL_RANDOM, settings.OPPONENT_GOAL_RANDOM
            )
        ),
    )

    assists = 0
    if goals >= 1 and rng.randint(1, 100) <= settings.ASSIST_CHANCE_PERCENT:
        assists = 1

    rating = calculate_rating(
        goals, assists, key_performance=goals >= 2, mistake=goals == 0
    )

    if goals > opp_goals:
        outcome, bonus = "win", settings.MATCH_WIN_BONUS
    elif goals < opp_goals:
        outcome, bonus = "loss", settings.MATCH_LOSS_BONUS
    else:
        outcome, bonus = "draw", settings.MATCH_DRAW_BONUS

    player.money += bonus
    player.reputation += settings.MATCH_REPUTATION_GAIN
    player.condition = max(settings.MIN_CONDITION, player.condition - settings.MATCH_CONDITION_COST)
    player.validate()

    return MatchResult(
        opponent=opponent,
        result=f"{goals}-{opp_goals}",
        goals=goals,
        assists=assists,
        rating=rating,
        date=date,
        outcome=outcome,
        bonus=bonus,
        reputation_gain=settings.MATCH_REPUTATION_GAIN,
        condition_cost=settings.MATCH_CONDITION_COST,
        events=events,
    )
