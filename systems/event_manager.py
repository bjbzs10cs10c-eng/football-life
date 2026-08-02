"""事件系统（B8）。

PRD §10 / TDD §10：
- random_event()：按 EVENT_TRIGGER_CHANCE 概率随机触发一条事件；
- apply_effect()：解析并应用 effect 表达式（属性/体力/金钱/声望）；
- handle_event()：按选项 A/B 应用对应效果。
事件内容来自 data/events.json（models.event.load_events）。
"""

from __future__ import annotations

import random as _random

import config.settings as settings
from models.event import GameEvent, load_events, parse_effect
from models.player import Player


def random_event(
    event_type: str | None = None,
    rng=None,
) -> GameEvent | None:
    """按触发概率随机返回一条事件；未触发或该类型无事件时返回 None。"""
    if rng is None:
        rng = _random
    threshold = round(settings.EVENT_TRIGGER_CHANCE * 100)
    if rng.randint(1, 100) > threshold:
        return None
    pool = [
        event for event in load_events()
        if event_type is None or event.type == event_type
    ]
    if not pool:
        return None
    return pool[rng.randint(0, len(pool) - 1)]


def apply_effect(player: Player, effect: str) -> dict:
    """应用一条效果表达式，返回实际发生的 {键: 变化量}（已 clamp）。"""
    parsed = parse_effect(effect)
    changes = {}
    for key, delta in parsed.items():
        if key in player.attributes:
            old = player.attributes[key]
            player.attributes[key] = max(
                settings.MIN_ATTRIBUTE,
                min(settings.MAX_ATTRIBUTE, old + delta),
            )
            changes[key] = player.attributes[key] - old
        elif key == "condition":
            old = player.condition
            player.condition = max(
                settings.MIN_CONDITION,
                min(settings.MAX_CONDITION, old + delta),
            )
            changes[key] = player.condition - old
        elif key == "money":
            old = player.money
            player.money = max(0, old + delta)
            changes[key] = player.money - old
        elif key == "reputation":
            old = player.reputation
            player.reputation = max(0, old + delta)
            changes[key] = player.reputation - old
    player.validate()
    return changes


def handle_event(player: Player, event: GameEvent, choice: str) -> dict:
    """处理事件：选择 A 应用 effect_a，选择 B 应用 effect_b。"""
    if choice == "A":
        return apply_effect(player, event.effect_a)
    if choice == "B":
        return apply_effect(player, event.effect_b)
    raise ValueError(f"choice 须为 'A' 或 'B'，当前 {choice!r}")
