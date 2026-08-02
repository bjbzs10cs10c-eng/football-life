"""训练系统（B6）。

TDD §7 / PRD §7.2：四类训练（TECHNICAL / PHYSICAL / TACTICAL / REST）。
- 每类训练定义可成长属性、收益区间、体力消耗、受伤概率（config）；
- 体力不足时返回 success=False，不消耗体力、不成长；
- 体能训练按配置概率受伤：本次无成长，额外扣除 INJURY_CONDITION_PENALTY 体力；
- 属性增长调用 systems.growth.growth_amount（职业态度 × 年龄系数）。
"""

from __future__ import annotations

import random as _random
from dataclasses import dataclass, field

import config.settings as settings
from models.player import Player
from systems.growth import growth_amount


@dataclass
class TrainingResult:
    """一次训练的结果。success=False 表示体力不足，训练未执行。"""

    success: bool
    training_type: str
    gains: dict = field(default_factory=dict)
    condition_change: int = 0
    injured: bool = False


def train(player: Player, training_type: str, rng=None) -> TrainingResult:
    """对球员执行一次训练；rng 传入 random.Random 时可复现（测试用）。"""
    if training_type not in settings.TRAINING_TYPES:
        raise ValueError(
            f"训练类型非法: {training_type!r}，可选 {list(settings.TRAINING_TYPES)}"
        )
    cfg = settings.TRAINING_TYPES[training_type]
    if rng is None:
        rng = _random
    player.validate()

    if training_type == "REST":
        restore = min(
            settings.MAX_CONDITION, player.condition + settings.REST_CONDITION_RESTORE
        ) - player.condition
        player.condition += restore
        return TrainingResult(
            success=True,
            training_type=training_type,
            gains={},
            condition_change=restore,
        )

    if player.condition < cfg["condition_cost"]:
        return TrainingResult(
            success=False,
            training_type=training_type,
            gains={},
            condition_change=0,
        )

    injured = False
    if cfg["injury_chance_percent"] > 0:
        injured = rng.randint(1, 100) <= cfg["injury_chance_percent"]

    gains = {}
    for attr in cfg["attributes"]:
        points = 0
        if not injured:
            base = rng.randint(cfg["gain_min"], cfg["gain_max"])
            points = growth_amount(
                player.age, player.attributes["professionalism"], base
            )
        old = player.attributes[attr]
        player.attributes[attr] = min(settings.MAX_ATTRIBUTE, old + points)
        gained = player.attributes[attr] - old
        if gained:
            gains[attr] = gained

    cost = cfg["condition_cost"] + (
        settings.INJURY_CONDITION_PENALTY if injured else 0
    )
    player.condition = max(settings.MIN_CONDITION, player.condition - cost)
    return TrainingResult(
        success=True,
        training_type=training_type,
        gains=gains,
        condition_change=-cost,
        injured=injured,
    )
