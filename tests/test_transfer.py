"""B9：俱乐部与转会系统测试。

覆盖：四档转入门槛、最高可达档位、候选俱乐部筛选（档位/排除当前）、
转会动作与门槛校验、按档位工资、load_clubs 稳定 id。
"""

import random

import pytest

import config.settings as s
import models.club as mc
import systems.player_creation as pc
import systems.transfer as tr


def make_player(overall=85, reputation=70):
    player = pc.create_player("Li Ming", "CN", "ST", "R", rng=random.Random(1))
    for attr in s.ALL_ATTRIBUTES:
        player.attributes[attr] = overall
    player.reputation = reputation
    return player


class TestLoadClubsIds:
    def test_ids_assigned_in_file_order(self):
        clubs = mc.load_clubs()
        assert [c.id for c in clubs] == list(range(1, len(clubs) + 1))
        assert len(clubs) >= 10


class TestQualifiesForTier:
    def test_elite_threshold(self):
        rules = s.TRANSFER_OFFER_RULES["ELITE"]
        assert tr.qualifies_for_tier(make_player(rules["min_overall"], rules["min_reputation"]), "ELITE")
        assert not tr.qualifies_for_tier(make_player(rules["min_overall"] - 1, rules["min_reputation"]), "ELITE")
        assert not tr.qualifies_for_tier(make_player(rules["min_overall"], rules["min_reputation"] - 1), "ELITE")

    def test_all_tiers_use_config_rules(self):
        for tier in s.CLUB_TIERS:
            rules = s.TRANSFER_OFFER_RULES[tier]
            player = make_player(rules["min_overall"], rules["min_reputation"])
            assert tr.qualifies_for_tier(player, tier)

    def test_unknown_tier_raises(self):
        with pytest.raises(ValueError, match="tier"):
            tr.qualifies_for_tier(make_player(), "SUPER")


class TestMaxTier:
    def test_elite_player(self):
        assert tr.max_tier_for(make_player(85, 75)) == "ELITE"

    def test_low_pro_player(self):
        # 70 >= 65、45 >= 40 -> LOW_PRO；75 门槛不满足
        assert tr.max_tier_for(make_player(70, 45)) == "LOW_PRO"

    def test_amateur_player(self):
        assert tr.max_tier_for(make_player(55, 25)) == "AMATEUR"

    def test_no_tier_qualifies(self):
        assert tr.max_tier_for(make_player(40, 10)) is None


class TestEligibleClubs:
    def test_elite_player_can_see_all_tiers(self):
        player = make_player(85, 75)
        clubs = tr.eligible_clubs(player)
        assert len(clubs) == len(mc.load_clubs())
        assert {c.tier for c in clubs} == set(s.CLUB_TIERS)

    def test_no_tier_means_no_targets(self):
        assert tr.eligible_clubs(make_player(40, 10)) == []

    def test_targets_limited_to_reachable_tier(self):
        player = make_player(70, 45)  # LOW_PRO
        clubs = tr.eligible_clubs(player)
        assert clubs
        assert all(c.tier in ("AMATEUR", "LOW_PRO") for c in clubs)

    def test_current_club_excluded(self):
        player = make_player(85, 75)
        clubs = mc.load_clubs()
        player.club_id = clubs[0].id
        targets = tr.eligible_clubs(player)
        assert all(c.id != player.club_id for c in targets)
        assert len(targets) == len(clubs) - 1

    def test_custom_club_list_supported(self):
        player = make_player(70, 45)
        subset = mc.load_clubs()[:3]
        targets = tr.eligible_clubs(player, clubs=subset)
        assert all(c in subset for c in targets)


class TestTransfer:
    def test_join_eligible_club(self):
        player = make_player(85, 75)
        club = next(c for c in mc.load_clubs() if c.tier == "ELITE")
        tr.transfer(player, club)
        assert player.club_id == club.id
        player.validate()

    def test_rejects_above_threshold_club(self):
        player = make_player(70, 45)  # LOW_PRO
        elite = next(c for c in mc.load_clubs() if c.tier == "ELITE")
        with pytest.raises(ValueError, match="门槛"):
            tr.transfer(player, elite)

    def test_rejects_unknown_club(self):
        player = make_player(85, 75)
        fake = mc.Club(
            name="No Such FC", league="英超", tier="ELITE",
            strength=90, facility=90, salary_level=90,
        )
        with pytest.raises(ValueError, match="俱乐部"):
            tr.transfer(player, fake)


class TestSalary:
    def test_salary_by_tier(self):
        for tier in s.CLUB_TIERS:
            club = next(c for c in mc.load_clubs() if c.tier == tier)
            assert tr.salary_for(club) == s.SALARY_BY_TIER[tier]
