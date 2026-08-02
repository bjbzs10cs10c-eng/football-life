"""B8：事件系统测试。

覆盖：触发概率、类型过滤、效果应用（属性/体力/金钱/声望及 clamp）、
选项分发（A/B 应用不同效果）、非法选项报错。
"""

import random

import pytest

import config.settings as s
import models.event as me
import systems.event_manager as em
import systems.player_creation as pc


def make_player():
    player = pc.create_player("Li Ming", "CN", "ST", "R", rng=random.Random(1))
    for attr in s.ALL_ATTRIBUTES:
        player.attributes[attr] = 60
    return player


class FakeRng:
    """按顺序返回预设 randint 结果。"""

    def __init__(self, values):
        self.values = list(values)

    def randint(self, low, high):
        assert self.values, "FakeRng 的随机值已耗尽"
        return self.values.pop(0)


class TestRandomEvent:
    def test_not_triggered_returns_none(self):
        # 99 > 15，不触发
        assert em.random_event(rng=FakeRng([99])) is None

    def test_triggered_returns_event(self):
        event = em.random_event(rng=FakeRng([10, 0]))
        assert isinstance(event, me.GameEvent)
        assert event.type in s.EVENT_TYPES

    def test_type_filter(self):
        event = em.random_event(event_type="training", rng=FakeRng([10, 0]))
        assert event.type == "training"
        assert event.choice_a == "加练射门"

    def test_unknown_type_returns_none(self):
        event = em.random_event(event_type="random", rng=FakeRng([10]))
        assert event is None

    def test_trigger_chance_from_config(self):
        threshold = round(s.EVENT_TRIGGER_CHANCE * 100)
        # 命中边界值
        assert em.random_event(rng=FakeRng([threshold, 0])) is not None
        assert em.random_event(rng=FakeRng([threshold + 1])) is None


class TestApplyEffect:
    def test_attribute_change(self):
        player = make_player()
        changes = em.apply_effect(player, "shooting+5")
        assert changes == {"shooting": 5}
        assert player.attributes["shooting"] == 65

    def test_attribute_clamped(self):
        player = make_player()
        player.attributes["shooting"] = 99
        em.apply_effect(player, "shooting+5")
        assert player.attributes["shooting"] == s.MAX_ATTRIBUTE
        em.apply_effect(player, "shooting-500")
        assert player.attributes["shooting"] == s.MIN_ATTRIBUTE

    def test_condition_change_and_clamp(self):
        player = make_player()
        em.apply_effect(player, "condition+30")
        assert player.condition == s.MAX_CONDITION
        em.apply_effect(player, "condition-500")
        assert player.condition == s.MIN_CONDITION

    def test_money_change_and_floor(self):
        player = make_player()
        changes = em.apply_effect(player, "money+5000")
        assert changes == {"money": 5000}
        assert player.money == s.START_MONEY + 5000
        em.apply_effect(player, "money-999999")
        assert player.money == 0

    def test_reputation_change(self):
        player = make_player()
        em.apply_effect(player, "reputation+8")
        assert player.reputation == s.START_REPUTATION + 8

    def test_none_effect_no_change(self):
        player = make_player()
        assert em.apply_effect(player, me.EFFECT_NONE) == {}

    def test_multi_token_effect(self):
        player = make_player()
        changes = em.apply_effect(player, "shooting+3;condition-20;reputation+5")
        assert changes == {"shooting": 3, "condition": -20, "reputation": 5}
        player.validate()

    def test_player_stays_valid(self):
        player = make_player()
        em.apply_effect(player, "shooting+3;condition-20;money+1000;reputation+5")
        player.validate()


class TestHandleEvent:
    def test_choice_a_applies_effect_a(self):
        player = make_player()
        event = me.GameEvent(
            type="training", description="x", choice_a="A", choice_b="B",
            effect_a="shooting+5", effect_b="passing+5",
        )
        changes = em.handle_event(player, event, "A")
        assert changes == {"shooting": 5}
        assert player.attributes["shooting"] == 65
        assert player.attributes["passing"] == 60

    def test_choice_b_applies_effect_b(self):
        player = make_player()
        event = me.GameEvent(
            type="training", description="x", choice_a="A", choice_b="B",
            effect_a="shooting+5", effect_b="passing+5",
        )
        changes = em.handle_event(player, event, "B")
        assert changes == {"passing": 5}
        assert player.attributes["passing"] == 65

    def test_invalid_choice_raises(self):
        player = make_player()
        event = me.GameEvent(
            type="training", description="x", choice_a="A", choice_b="B",
            effect_a="none", effect_b="none",
        )
        with pytest.raises(ValueError, match="choice"):
            em.handle_event(player, event, "C")

    def test_live_event_from_json(self):
        player = make_player()
        events = me.load_events()
        career = next(e for e in events if e.type == "career" and "代言" in e.description)
        changes = em.handle_event(player, career, "A")
        assert changes["money"] == 5000
        assert player.money == s.START_MONEY + 5000
