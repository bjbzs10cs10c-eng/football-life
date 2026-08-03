"""B10：时间/赛季推进、经济结算与退役评价测试。

覆盖：日期推进、跨赛季（season+1/年龄+1）、30 天周期发薪（有/无俱乐部）、
退役判定、退役评价分档与描述。
"""

import random

import pytest

import config.settings as s
import models.career as mcareer
import models.club as mc
import systems.career as career
import systems.player_creation as pc
import systems.transfer as tr


def make_player(date_str=s.SEASON_START_DATE):
    player = pc.create_player("Li Ming", "CN", "ST", "R", rng=random.Random(1))
    player.current_date = date_str
    return player


def make_elite_club():
    return next(c for c in mc.load_clubs() if c.tier == "ELITE")


class TestAdvanceDays:
    def test_advance_one_day(self):
        player = make_player()
        logs = career.advance_days(player, 1)
        assert player.current_date == "2026-01-02"
        assert player.season == 1
        assert logs == []

    def test_advance_seven_days(self):
        player = make_player()
        career.advance_days(player, 7)
        assert player.current_date == "2026-01-08"

    def test_invalid_days_raises(self):
        player = make_player()
        with pytest.raises(ValueError, match="days"):
            career.advance_days(player, 0)
        with pytest.raises(ValueError, match="days"):
            career.advance_days(player, -3)

    def test_player_stays_valid(self):
        player = make_player()
        career.advance_days(player, 30)
        player.validate()


class TestSeasonRollover:
    def test_crossing_season_boundary(self):
        player = make_player("2026-12-31")
        logs = career.advance_days(player, 1)
        assert player.current_date == "2027-01-01"
        assert player.season == 2
        assert player.age == s.START_AGE + 1
        assert any("赛季" in log for log in logs)

    def test_age_increments_once_per_season(self):
        player = make_player("2026-12-30")
        career.advance_days(player, 3)
        assert player.season == 2
        assert player.age == s.START_AGE + 1


class TestSalary:
    def test_paid_every_30_days_with_club(self):
        player = make_player()
        club = make_elite_club()
        career.advance_days(player, 30, club=club)
        assert player.money == s.START_MONEY + tr.salary_for(club)
        career.advance_days(player, 30, club=club)
        assert player.money == s.START_MONEY + 2 * tr.salary_for(club)

    def test_no_pay_on_first_day(self):
        player = make_player()
        career.advance_days(player, 1, club=make_elite_club())
        assert player.money == s.START_MONEY

    def test_no_club_no_pay(self):
        player = make_player()
        career.advance_days(player, 60)
        assert player.money == s.START_MONEY

    def test_pay_logged(self):
        player = make_player()
        logs = career.advance_days(player, 30, club=make_elite_club())
        assert any("工资" in log for log in logs)


class TestRetirement:
    def test_should_retire_at_threshold(self):
        player = make_player()
        player.age = s.RETIRE_AGE - 1
        assert not career.should_retire(player)
        player.age = s.RETIRE_AGE
        assert career.should_retire(player)

    def test_evaluation_legend(self):
        result = career.retirement_evaluation(
            make_player(), mcareer.Career(games=400, goals=300, trophies=5)
        )
        assert result.label == "传奇"
        assert "5" in result.description

    def test_evaluation_star(self):
        result = career.retirement_evaluation(
            make_player(), mcareer.Career(games=200, trophies=1)
        )
        assert result.label == "球星"

    def test_evaluation_good_by_games(self):
        result = career.retirement_evaluation(
            make_player(), mcareer.Career(games=300, trophies=0)
        )
        assert result.label == "优秀"

    def test_evaluation_normal(self):
        result = career.retirement_evaluation(
            make_player(), mcareer.Career(games=150, trophies=0)
        )
        assert result.label == "普通"

    def test_evaluation_mediocre_fallback(self):
        result = career.retirement_evaluation(make_player(), mcareer.Career())
        assert result.label == "平庸"


class TestMatchSchedule:
    def test_season_start_is_match_day(self):
        assert career.days_until_next_match(make_player()) == 0

    def test_mid_week_countdown(self):
        # 2026-01-04 是第 4 天（day3），距 day7 比赛日还有 4 天
        player = make_player("2026-01-04")
        assert career.days_until_next_match(player) == 4

    def test_day_before_match(self):
        # 2026-01-07 是 day6，距比赛日 1 天
        player = make_player("2026-01-07")
        assert career.days_until_next_match(player) == 1

    def test_next_match_day_is_zero(self):
        # 2026-01-08 是 day7，恰好比赛日
        player = make_player("2026-01-08")
        assert career.days_until_next_match(player) == 0
