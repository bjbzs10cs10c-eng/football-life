"""B7：比赛模拟引擎与赛后结算测试。

覆盖：进球概率公式/clamp、门将能力、机会数量（含体力影响）、
完整比赛流程（确定性随机序列）、胜负结算、评分、记录转换。
"""

import random

import pytest

import config.settings as s
import systems.match_engine as me
import systems.player_creation as pc


def make_player(shooting=80, condition=s.START_CONDITION):
    player = pc.create_player("Li Ming", "CN", "ST", "R", rng=random.Random(1))
    for attr in s.ALL_ATTRIBUTES:
        player.attributes[attr] = 60
    player.attributes["shooting"] = shooting
    player.condition = condition
    return player


class FakeRng:
    """按顺序返回预设 randint 结果，便于精确控制随机。"""

    def __init__(self, values):
        self.values = list(values)

    def randint(self, low, high):
        assert self.values, "FakeRng 的随机值已耗尽"
        return self.values.pop(0)


class TestGoalProbability:
    def test_tdd_example_base_fifty_percent(self):
        # (85-75)×0.05 = 0.50
        assert me.goal_probability(85, 75, 0.0) == 0.5

    def test_random_factor_shifts_probability(self):
        assert me.goal_probability(85, 75, 0.1) == pytest.approx(0.6)
        assert me.goal_probability(85, 75, -0.1) == pytest.approx(0.4)

    def test_clamped_to_max(self):
        assert me.goal_probability(100, 1, 0.0) == s.GOAL_PROBABILITY_MAX

    def test_clamped_to_min(self):
        assert me.goal_probability(1, 100, 0.0) == s.GOAL_PROBABILITY_MIN


class TestOpponentGk:
    def test_formula(self):
        # 15 + 78×0.75 = 73.5
        assert me.opponent_gk(78) == pytest.approx(73.5)


class TestOpportunityCount:
    def test_tdd_example_style_value(self):
        # 78 + 60 + 5 = 143 -> /30 = 4.77 -> 5 次
        assert me.opportunity_count(78, 60, 5) == 5

    def test_lower_condition_reduces_chances(self):
        full = me.opportunity_count(78, 60, 5, condition=100)
        half = me.opportunity_count(78, 60, 5, condition=50)
        assert half <= full
        assert half == 2  # 143/30×0.5 = 2.38 -> 2

    def test_at_least_one_chance(self):
        assert me.opportunity_count(10, 10, -5) >= 1


class TestPlayMatchDraw:
    def test_draw_full_flow(self):
        player = make_player(shooting=80)
        rng = FakeRng([0, 10, 0, 95, 20, 0, 95, 30, 0, 95, 40, 0, 95, 50, 0, 95, 0])
        result = me.play_match(
            player, "Test United", 78, 75, date="2026-01-08", rng=rng
        )
        assert result.result == "0-0"
        assert result.outcome == "draw"
        assert result.goals == 0
        assert result.assists == 0
        assert result.rating == pytest.approx(5.5)  # 6 - 失误 0.5
        assert len(result.events) == 5
        assert result.bonus == s.MATCH_DRAW_BONUS
        assert result.reputation_gain == s.MATCH_REPUTATION_GAIN
        assert result.date == "2026-01-08"
        # 赛后结算
        assert player.money == s.START_MONEY + s.MATCH_DRAW_BONUS
        assert player.reputation == s.START_REPUTATION + s.MATCH_REPUTATION_GAIN
        assert player.condition == s.START_CONDITION - s.MATCH_CONDITION_COST
        player.validate()


class TestPlayMatchWin:
    def test_win_with_goal_and_assist_tdd_rating(self):
        player = make_player(shooting=50)
        rng = FakeRng([5, 10, 5, 5, 20, -5, 96, 0, 30])
        result = me.play_match(player, "Weak FC", 20, 20, rng=rng)
        # 2 次机会：第 10 分钟进球、第 20 分钟被扑出
        assert result.goals == 1
        assert result.assists == 1
        assert result.result == "1-0"
        assert result.outcome == "win"
        assert result.rating == pytest.approx(8.5)  # 6+1.5+1，TDD §9 示例
        assert result.bonus == s.MATCH_WIN_BONUS
        assert player.money == s.START_MONEY + s.MATCH_WIN_BONUS


class TestPlayMatchLoss:
    def test_loss_against_stronger_opponent(self):
        player = make_player(shooting=50)
        rng = FakeRng([-5, 10, 0, 96, 20, 0, 96, 1])
        result = me.play_match(player, "Strong FC", 20, 60, rng=rng)
        assert result.goals == 0
        assert result.result == "0-4"
        assert result.outcome == "loss"
        assert result.bonus == s.MATCH_LOSS_BONUS
        assert result.rating == pytest.approx(5.5)


class TestRating:
    def test_base_rating(self):
        assert me.calculate_rating(0, 0) == s.RATING_BASE

    def test_goal_and_assist(self):
        assert me.calculate_rating(1, 1) == 8.5

    def test_key_performance_and_mistake(self):
        assert me.calculate_rating(2, 1, key_performance=True) == s.RATING_MAX
        assert me.calculate_rating(0, 0, mistake=True) == 5.5

    def test_clamped(self):
        assert me.calculate_rating(99, 99, key_performance=True) == s.RATING_MAX


class TestRecordConversion:
    def test_to_record_matches_table_fields(self):
        player = make_player(shooting=50)
        rng = FakeRng([5, 10, 5, 5, 20, -5, 96, 0, 30])
        result = me.play_match(player, "Weak FC", 20, 20, date="2026-01-08", rng=rng)
        record = result.to_record()
        record.validate()
        assert record.opponent == "Weak FC"
        assert record.result == "1-0"
        assert record.goals == 1
        assert record.assists == 1
        assert record.rating == 8.5
        assert record.date == "2026-01-08"
