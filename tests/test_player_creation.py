"""B4：球员创建系统测试。

覆盖：初始属性生成（区间/确定性）、位置加成（四位置/上限截断）、
Overall 综合能力公式、create_player 完整流程与默认值。
"""

import random

import pytest

import config.settings as s
import models.player as mp
import systems.player_creation as pc


def base_attrs(value):
    """构造 15 项属性均为 value 的字典。"""
    return {attr: value for attr in s.ALL_ATTRIBUTES}


class TestGenerateInitialAttributes:
    def test_all_15_attributes_in_configured_range(self):
        attrs = pc.generate_initial_attributes(random.Random(42))
        assert list(attrs) == s.ALL_ATTRIBUTES
        for value in attrs.values():
            assert s.INITIAL_ATTRIBUTE_MIN <= value <= s.INITIAL_ATTRIBUTE_MAX

    def test_deterministic_with_seeded_rng(self):
        first = pc.generate_initial_attributes(random.Random(7))
        second = pc.generate_initial_attributes(random.Random(7))
        assert first == second

    def test_different_seeds_give_variation(self):
        first = pc.generate_initial_attributes(random.Random(1))
        second = pc.generate_initial_attributes(random.Random(2))
        assert sum(first.values()) != sum(second.values())


class TestPositionBonus:
    @pytest.mark.parametrize(
        "position",
        [
            "ST",
            "WING",
            "CM",
            "CB",
        ],
    )
    def test_bonus_applied_from_config(self, position):
        base = base_attrs(50)
        result = pc.apply_position_bonus(base, position)
        expected_bonus = s.POSITION_BONUSES[position]
        for attr in s.ALL_ATTRIBUTES:
            assert result[attr] == 50 + expected_bonus.get(attr, 0)
        # 加成的属性必须与配置一致，且没有意外改动其他属性
        assert {a: result[a] - 50 for a in expected_bonus} == expected_bonus

    def test_bonus_clamped_to_max_attribute(self):
        base = base_attrs(99)
        result = pc.apply_position_bonus(base, "ST")
        assert result["shooting"] == s.MAX_ATTRIBUTE
        assert result["pace"] == s.MAX_ATTRIBUTE

    def test_bonus_clamped_to_min_attribute(self):
        base = base_attrs(1)
        result = pc.apply_position_bonus(base, "CB")
        assert result["defending"] == 6

    def test_invalid_position_raises(self):
        with pytest.raises(ValueError, match="position"):
            pc.apply_position_bonus({}, "GK")


class TestCreatePlayer:
    def test_creates_valid_player_with_defaults(self):
        player = pc.create_player("Li Ming", "CN", "ST", "R", rng=random.Random(1))
        assert player.validate() is not None
        assert player.age == s.START_AGE
        assert player.position == "ST"
        assert player.foot == "R"
        assert player.money == s.START_MONEY
        assert player.reputation == s.START_REPUTATION
        assert player.condition == s.START_CONDITION
        assert player.current_date == s.SEASON_START_DATE
        assert player.season == 1
        assert player.club_id is None

    def test_position_bonus_applied_in_created_player(self):
        seed = 3
        base = pc.generate_initial_attributes(random.Random(seed))
        player = pc.create_player(
            "P", "CN", "CB", "L", rng=random.Random(seed)
        )
        expected_bonus = s.POSITION_BONUSES["CB"]
        for attr in s.ALL_ATTRIBUTES:
            expected = min(
                s.MAX_ATTRIBUTE, base[attr] + expected_bonus.get(attr, 0)
            )
            assert player.attributes[attr] == expected

    def test_custom_age_and_height(self):
        player = pc.create_player(
            "P", "CN", "WING", "R", age=18, height=1.78, rng=random.Random(5)
        )
        assert player.age == 18
        assert player.height == 1.78

    def test_invalid_position_raises(self):
        with pytest.raises(ValueError, match="position"):
            pc.create_player("P", "CN", "GK", "R", rng=random.Random(1))


class TestOverall:
    def test_equal_attributes_give_same_overall(self):
        attrs = base_attrs(60)
        assert mp.calculate_overall(attrs) == 60

    def test_weights_match_config_formula(self):
        attrs = {}
        for attr in s.ATTRIBUTE_TECHNICAL:
            attrs[attr] = 100
        for attr in s.ATTRIBUTE_PHYSICAL:
            attrs[attr] = 40
        for attr in s.ATTRIBUTE_MENTAL:
            attrs[attr] = 40
        # 100×0.40 + 40×0.30 + 40×0.30 = 64
        assert mp.calculate_overall(attrs) == 64

    def test_rounding_to_nearest_int(self):
        attrs = {}
        for attr in s.ATTRIBUTE_TECHNICAL:
            attrs[attr] = 69  # 69×0.40 = 27.6
        for attr in s.ATTRIBUTE_PHYSICAL:
            attrs[attr] = 71  # 71×0.30 = 21.3
        for attr in s.ATTRIBUTE_MENTAL:
            attrs[attr] = 73  # 73×0.30 = 21.9
        # 27.6 + 21.3 + 21.9 = 70.8 -> 71
        assert mp.calculate_overall(attrs) == 71

    def test_player_method_matches_function(self):
        player = pc.create_player("P", "CN", "ST", "R", rng=random.Random(9))
        assert player.overall() == mp.calculate_overall(player.attributes)

    def test_created_player_overall_within_plausible_range(self):
        player = pc.create_player("P", "CN", "ST", "R", rng=random.Random(11))
        assert s.INITIAL_ATTRIBUTE_MIN <= player.overall() <= s.INITIAL_ATTRIBUTE_MAX + 5
