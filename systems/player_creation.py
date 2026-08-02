"""球员创建系统（B4）。

流程（PRD §3.1 / §4）：
1. 在配置区间（INITIAL_ATTRIBUTE_MIN~MAX）内随机生成 15 项初始属性；
2. 应用位置加成（PRD §4.2 / config.POSITION_BONUSES），并截断到 1-100；
3. 生成 Player 实例并校验。
Overall（综合能力）见 models.player.calculate_overall / Player.overall。
"""

from __future__ import annotations

import random as _random

import config.settings as settings
from models.player import Player


def generate_initial_attributes(rng=None) -> dict:
    """在配置区间内为 15 项属性各生成一个随机整数。

    rng 传入 random.Random 实例时可复现（测试用）；默认使用全局随机。
    """
    if rng is None:
        rng = _random
    return {
        attr: rng.randint(
            settings.INITIAL_ATTRIBUTE_MIN, settings.INITIAL_ATTRIBUTE_MAX
        )
        for attr in settings.ALL_ATTRIBUTES
    }


def apply_position_bonus(attributes: dict, position: str) -> dict:
    """按位置加成属性（PRD §4.2），结果截断到 1-100。"""
    if position not in settings.POSITION_CODES:
        raise ValueError(
            f"position 非法: {position!r}，可选 {settings.POSITION_CODES}"
        )
    result = dict(attributes)
    for attr, bonus in settings.POSITION_BONUSES.get(position, {}).items():
        result[attr] = max(
            settings.MIN_ATTRIBUTE,
            min(settings.MAX_ATTRIBUTE, result.get(attr, 0) + bonus),
        )
    return result


def create_player(
    name: str,
    nationality: str,
    position: str,
    foot: str,
    age: int | None = None,
    height: float | None = None,
    rng=None,
) -> Player:
    """创建一名带随机初始属性与位置加成的新球员（默认 17 岁，见配置）。"""
    if age is None:
        age = settings.START_AGE
    base = generate_initial_attributes(rng)
    attributes = apply_position_bonus(base, position)
    player = Player(
        name=name,
        age=age,
        nationality=nationality,
        position=position,
        foot=foot,
        attributes=attributes,
        height=height,
    )
    return player.validate()
