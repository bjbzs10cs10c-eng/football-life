"""B6：训练与成长系统测试。

覆盖：年龄系数分段、成长公式（职业态度×年龄×基础效果、0.5 粒度取整、
有效训练至少 +1）、四类训练流程（属性/体力/受伤）、体力不足、属性上限截断。
"""

import random

import pytest

import config.settings as s
import systems.growth as g
import systems.player_creation as pc
import systems.training as tr


def make_player(age=s.START_AGE, professionalism=80, condition=s.START_CONDITION):
    player = pc.create_player("Li Ming", "CN", "ST", "R", age=age, rng=random.Random(1))
    for attr in s.ALL_ATTRIBUTES:
        player.attributes[attr] = 50
    player.attributes["professionalism"] = professionalism
    player.condition = condition
    return player


class FakeRng:
    """按顺序返回预设 randint 结果，便于精确控制随机。"""

    def __init__(self, values):
        self.values = list(values)

    def randint(self, low, high):
        assert self.values, "FakeRng 的随机值已耗尽"
        return self.values.pop(0)


class TestAgeFactor:
    @pytest.mark.parametrize(
        "age,expected",
        [
            (16, 1.0),
            (17, 1.0),
            (22, 1.0),
            (23, 0.6),
            (28, 0.6),
            (29, 0.25),
            (35, 0.25),
        ],
    )
    def test_brackets(self, age, expected):
        assert g.age_factor(age) == expected

    def test_age_below_first_bracket_uses_first_factor(self):
        assert g.age_factor(10) == s.GROWTH_AGE_BRACKETS[0][2]


class TestGrowthAmount:
    def test_seventeen_with_high_professionalism(self):
        # 基础 2 × 职业态度 0.8 × 年龄 1.0 = 1.6 -> 0.5 粒度 1.5 -> +2
        assert g.growth_amount(17, 80, 2) == 2

    def test_thirty_with_high_professionalism(self):
        # 基础 2 × 0.8 × 0.25 = 0.4 -> 至少 +1
        assert g.growth_amount(30, 80, 2) == 1

    def test_zero_base_gives_no_growth(self):
        assert g.growth_amount(17, 80, 0) == 0

    def test_higher_professionalism_grows_more(self):
        low = g.growth_amount(17, 40, 3)
        high = g.growth_amount(17, 100, 3)
        assert high >= low
        assert high > low

    def test_younger_grows_more_than_older(self):
        young = g.growth_amount(17, 80, 3)
        old = g.growth_amount(30, 80, 3)
        assert young >= old

    def test_rounding_to_half_step(self):
        # 基础 3 × 1.0 × 1.0 = 3.0 -> +3
        assert g.growth_amount(17, 100, 3) == 3
        # 基础 3 × 0.8 × 1.0 = 2.4 -> 2.5 -> +3
        assert g.growth_amount(17, 80, 3) == 3


class TestTrainingTypes:
    def test_technical_trains_only_shooting_and_passing(self):
        player = make_player()
        before = dict(player.attributes)
        result = tr.train(player, "TECHNICAL", rng=FakeRng([2, 3]))
        assert result.success
        assert not result.injured
        assert set(result.gains) == {"shooting", "passing"}
        for attr in s.ALL_ATTRIBUTES:
            if attr in ("shooting", "passing"):
                assert player.attributes[attr] > before[attr]
            else:
                assert player.attributes[attr] == before[attr]

    def test_physical_trains_three_attributes(self):
        player = make_player()
        result = tr.train(player, "PHYSICAL", rng=FakeRng([95, 2, 2, 2]))
        assert result.success
        assert set(result.gains) == {"pace", "strength", "stamina"}
        assert result.condition_change == -s.TRAINING_TYPES["PHYSICAL"]["condition_cost"]

    def test_tactical_trains_decision_only(self):
        player = make_player()
        result = tr.train(player, "TACTICAL", rng=FakeRng([2]))
        assert set(result.gains) == {"decision"}

    def test_rest_restores_condition(self):
        player = make_player(condition=50)
        result = tr.train(player, "REST")
        assert result.success
        assert result.gains == {}
        assert player.condition == min(
            s.MAX_CONDITION, 50 + s.REST_CONDITION_RESTORE
        )
        assert result.condition_change == s.REST_CONDITION_RESTORE

    def test_rest_restore_clamped_to_max(self):
        player = make_player(condition=90)
        tr.train(player, "REST")
        assert player.condition == s.MAX_CONDITION

    def test_condition_deducted(self):
        player = make_player()
        result = tr.train(player, "TECHNICAL", rng=FakeRng([2, 2]))
        assert player.condition == s.START_CONDITION - s.TRAINING_TYPES["TECHNICAL"]["condition_cost"]
        assert result.condition_change == -s.TRAINING_TYPES["TECHNICAL"]["condition_cost"]

    def test_not_enough_condition_fails_without_changes(self):
        player = make_player(condition=10)
        before = dict(player.attributes)
        result = tr.train(player, "TECHNICAL", rng=FakeRng([2, 2]))
        assert not result.success
        assert player.attributes == before
        assert player.condition == 10

    def test_rest_works_with_zero_condition(self):
        player = make_player(condition=0)
        result = tr.train(player, "REST")
        assert result.success
        assert player.condition == s.REST_CONDITION_RESTORE

    def test_invalid_training_type_raises(self):
        player = make_player()
        with pytest.raises(ValueError, match="训练类型"):
            tr.train(player, "SHOOTING")


class TestInjury:
    def test_physical_injury_roll_hits(self):
        player = make_player()
        # 第一笔 randint(1,100)=1 命中 5% 受伤，之后随机值不应被消耗
        result = tr.train(player, "PHYSICAL", rng=FakeRng([1]))
        assert result.injured
        assert result.gains == {}
        assert result.condition_change == -(
            s.TRAINING_TYPES["PHYSICAL"]["condition_cost"]
            + s.INJURY_CONDITION_PENALTY
        )

    def test_physical_injury_roll_misses(self):
        player = make_player()
        result = tr.train(player, "PHYSICAL", rng=FakeRng([95, 2, 2, 2]))
        assert not result.injured
        assert result.gains != {}

    def test_technical_never_injures(self):
        player = make_player()
        result = tr.train(player, "TECHNICAL", rng=FakeRng([2, 2]))
        assert not result.injured


class TestClamping:
    def test_attribute_capped_at_max(self):
        player = make_player()
        player.attributes["shooting"] = 99
        player.attributes["passing"] = 99
        tr.train(player, "TECHNICAL", rng=FakeRng([3, 3]))
        assert player.attributes["shooting"] == s.MAX_ATTRIBUTE
        assert player.attributes["passing"] == s.MAX_ATTRIBUTE

    def test_condition_not_below_zero(self):
        player = make_player(condition=15)
        tr.train(player, "TECHNICAL", rng=FakeRng([2, 2]))
        assert player.condition == 0

    def test_player_remains_valid_after_training(self):
        player = make_player()
        tr.train(player, "TECHNICAL", rng=FakeRng([2, 2]))
        player.validate()
