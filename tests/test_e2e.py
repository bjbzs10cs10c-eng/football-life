"""D14：端到端整季模拟测试。

固定随机种子自动跑完整赛季，断言日期/统计/荣誉一致、结果可复现、
单赛季耗时可接受、存档往返无漂移。
"""

import random
import time

import config.settings as s
import models.career as mcareer
import models.club as mc
import models.match as mm
import systems.career as career_sys
import systems.match_engine as me
import systems.player_creation as pc
import systems.training as training
import systems.transfer as tr


def make_player(overall=70, reputation=45):
    player = pc.create_player("E2E Player", "CN", "ST", "R", rng=random.Random(1))
    for attr in s.ALL_ATTRIBUTES:
        player.attributes[attr] = overall
    player.reputation = reputation
    return player


def simulate_season(player, club, rng, weeks=52):
    """按真实节奏模拟一周（每天一行动）：
    技术/体能/战术训练各一次 + 两场休息 + 一场同档比赛 + 赛后休息，共 7 天。
    """
    matches = []
    career_data = mcareer.Career()
    clubs = mc.load_clubs()
    for _ in range(weeks):
        for train_type in ("TECHNICAL", "PHYSICAL", "TACTICAL"):
            training.train(player, train_type, rng=rng)
        training.train(player, "REST", rng=rng)
        training.train(player, "REST", rng=rng)
        pool = [
            c for c in clubs
            if c.tier == club.tier and c.id != club.id
        ]
        opponent = rng.choice(pool)
        result = me.play_match(
            player, opponent.name, club.strength, opponent.strength, rng=rng
        )
        matches.append(result.to_record())
        career_data.games += 1
        career_data.goals += result.goals
        career_data.assists += result.assists
        training.train(player, "REST", rng=rng)  # 赛后休息一天
        career_sys.advance_days(player, 7, club=club)
    return matches, career_data


class TestEndToEndSeason:
    def test_full_season_date_stats_trophies_consistent(self):
        rng = random.Random(2026)
        player = make_player()
        club = next(c for c in mc.load_clubs() if c.tier == "LOW_PRO")
        tr.transfer(player, club)

        start = time.monotonic()
        matches, career_data = simulate_season(player, club, rng)
        elapsed = time.monotonic() - start

        # 日期/赛季一致：52 周 × 7 天 = 364 天 -> 2026-12-31，赛季 1
        assert player.current_date == "2026-12-31"
        assert player.season == 1
        assert player.age == s.START_AGE

        # 统计一致：比赛记录与生涯数据互相吻合
        assert len(matches) == 52
        assert career_data.games == len(matches)
        assert career_data.goals == sum(m.goals for m in matches)
        assert career_data.assists == sum(m.assists for m in matches)
        assert all(isinstance(m, mm.MatchRecord) and m.validate() for m in matches)

        # 荣誉一致：MVP 无自动荣誉系统，生涯冠军数保持初始值
        assert career_data.trophies == 0
        assert career_data.best_award is None

        # 单赛季耗时可接受（远低于 10 秒）
        assert elapsed < 10, f"单赛季模拟耗时 {elapsed:.2f}s 超过可接受范围"

        player.validate()

    def test_same_seed_reproduces_identical_result(self):
        def run():
            rng = random.Random(42)
            player = make_player()
            club = next(c for c in mc.load_clubs() if c.tier == "LOW_PRO")
            tr.transfer(player, club)
            matches, _ = simulate_season(player, club, rng)
            return (
                player.attributes,
                player.money,
                player.reputation,
                player.condition,
                player.current_date,
                [m.to_dict() for m in matches],
            )

        first = run()
        second = run()
        assert first == second

    def test_three_seasons_growth_and_no_drift(self, tmp_path):
        import systems.save_load as sl

        rng = random.Random(7)
        player = make_player()
        club = next(c for c in mc.load_clubs() if c.tier == "LOW_PRO")
        tr.transfer(player, club)
        all_matches = []
        career_data = mcareer.Career(best_award="联赛冠军")
        for _ in range(3):
            matches, season_career = simulate_season(player, club, rng)
            all_matches.extend(matches)
            career_data.games += season_career.games
            career_data.goals += season_career.goals
            career_data.assists += season_career.assists
            # 能力足够时升级俱乐部
            top = tr.max_tier_for(player)
            if top and tr.salary_for(club) < tr.salary_for(
                next(c for c in mc.load_clubs() if c.tier == top)
            ):
                club = next(
                    c for c in tr.eligible_clubs(player) if c.tier == top
                )
                tr.transfer(player, club)

        # 成长曲线合理：3 个赛季后综合能力提升，且未越界
        assert player.overall() > 70
        assert all(s.MIN_ATTRIBUTE <= v <= s.MAX_ATTRIBUTE for v in player.attributes.values())
        assert len(all_matches) == 52 * 3
        assert career_data.games == 52 * 3
        assert career_data.goals == sum(m.goals for m in all_matches)
        player.validate()

        # 数据无漂移：存档 -> 读档全量比对
        path = tmp_path / "e2e.db"
        sl.save_game(
            player,
            club=club,
            matches=all_matches,
            career=career_data,
            db_path=path,
        )
        data = sl.load_game(db_path=path)
        assert data.player.attributes == player.attributes
        assert data.player.money == player.money
        assert data.player.reputation == player.reputation
        assert data.player.current_date == player.current_date
        assert data.club.name == club.name
        assert len(data.matches) == len(all_matches)
        assert data.career.games == career_data.games
        assert data.career.goals == career_data.goals
        assert data.career.trophies == career_data.trophies
