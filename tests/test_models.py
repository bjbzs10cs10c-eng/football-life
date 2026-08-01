"""A3：模型类与 JSON 加载校验测试。"""

import json

import pytest

import config.settings as s
import models.club as mc
import models.event as me
import models.match as mm
import models.player as mp


def make_valid_player():
    return mp.Player(
        name="Li Ming",
        age=s.START_AGE,
        nationality="CN",
        position="ST",
        foot="R",
        attributes=mp.Player.make_default_attributes(),
    )


def make_valid_club():
    return mc.Club(
        name="Test FC",
        league="中超",
        tier="TOP_LEAGUE",
        strength=70,
        facility=60,
        salary_level=55,
    )


def make_valid_event():
    return me.GameEvent(
        type="training",
        description="测试事件",
        choice_a="选项A",
        choice_b="选项B",
        effect="shooting+1",
    )


def make_valid_match():
    return mm.MatchRecord(
        opponent="Test United",
        result="2-1",
        date=s.SEASON_START_DATE,
    )


class TestPlayerModel:
    def test_valid_player(self):
        assert make_valid_player().validate() is not None

    def test_default_attributes_have_15_keys(self):
        attrs = mp.Player.make_default_attributes()
        assert list(attrs) == s.ALL_ATTRIBUTES
        assert len(attrs) == 15

    def test_rejects_unknown_position(self):
        player = make_valid_player()
        player.position = "GK"
        with pytest.raises(ValueError, match="position"):
            player.validate()

    def test_rejects_unknown_foot(self):
        player = make_valid_player()
        player.foot = "X"
        with pytest.raises(ValueError, match="foot"):
            player.validate()

    def test_rejects_missing_attribute(self):
        player = make_valid_player()
        del player.attributes["shooting"]
        with pytest.raises(ValueError, match="attributes"):
            player.validate()

    def test_rejects_out_of_range_attribute(self):
        player = make_valid_player()
        player.attributes["shooting"] = 101
        with pytest.raises(ValueError, match="shooting"):
            player.validate()

    def test_rejects_bad_condition(self):
        player = make_valid_player()
        player.condition = -1
        with pytest.raises(ValueError, match="condition"):
            player.validate()

    def test_serialization_round_trip(self):
        player = make_valid_player()
        restored = mp.Player.from_dict(player.to_dict())
        assert restored == player


class TestClubModel:
    def test_valid_club(self):
        assert make_valid_club().validate() is not None

    def test_rejects_unknown_tier(self):
        club = make_valid_club()
        club.tier = "SUPER"
        with pytest.raises(ValueError, match="tier"):
            club.validate()

    def test_rejects_empty_name(self):
        club = make_valid_club()
        club.name = "  "
        with pytest.raises(ValueError, match="名称"):
            club.validate()

    def test_rejects_out_of_range_strength(self):
        club = make_valid_club()
        club.strength = 101
        with pytest.raises(ValueError, match="strength"):
            club.validate()

    def test_serialization_round_trip(self):
        club = make_valid_club()
        restored = mc.Club.from_dict(club.to_dict())
        assert restored == club


class TestMatchModel:
    def test_valid_match(self):
        assert make_valid_match().validate() is not None

    def test_rejects_bad_result(self):
        match = make_valid_match()
        match.result = "2:1"
        with pytest.raises(ValueError, match="result"):
            match.validate()

    def test_rejects_out_of_range_rating(self):
        match = make_valid_match()
        match.rating = 10.5
        with pytest.raises(ValueError, match="rating"):
            match.validate()

    def test_serialization_round_trip(self):
        match = make_valid_match()
        restored = mm.MatchRecord.from_dict(match.to_dict())
        assert restored == match


class TestEventModel:
    def test_valid_event(self):
        assert make_valid_event().validate() is not None

    def test_rejects_unknown_type(self):
        event = make_valid_event()
        event.type = "random"
        with pytest.raises(ValueError, match="type"):
            event.validate()

    def test_rejects_empty_choice(self):
        event = make_valid_event()
        event.choice_a = ""
        with pytest.raises(ValueError, match="choice_a"):
            event.validate()

    def test_parse_effect_none(self):
        assert me.parse_effect(me.EFFECT_NONE) == {}

    def test_parse_effect_multi_token(self):
        assert me.parse_effect("shooting+3;condition-20") == {
            "shooting": 3,
            "condition": -20,
        }

    def test_parse_effect_rejects_bad_syntax(self):
        with pytest.raises(ValueError, match="语法"):
            me.parse_effect("shooting+=3")

    def test_parse_effect_rejects_unknown_key(self):
        with pytest.raises(ValueError, match="未知键"):
            me.parse_effect("vision+1")

    def test_parse_effect_rejects_duplicate_key(self):
        with pytest.raises(ValueError, match="重复"):
            me.parse_effect("shooting+1;shooting+2")

    def test_serialization_round_trip(self):
        event = make_valid_event()
        restored = me.GameEvent.from_dict(event.to_dict())
        assert restored == event


class TestJsonLoaders:
    def test_load_clubs_covers_all_tiers(self, tmp_path):
        path = tmp_path / "clubs.json"
        path.write_text(
            json.dumps(
                [
                    {"name": f"{tier}{i}", "league": "中超", "tier": tier,
                     "strength": 60, "facility": 60, "salary_level": 60}
                    for tier in s.CLUB_TIERS
                    for i in range(1)
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        clubs = mc.load_clubs(path)
        assert {club.tier for club in clubs} == set(s.CLUB_TIERS)

    def test_load_clubs_rejects_duplicate_names(self, tmp_path):
        path = tmp_path / "clubs.json"
        path.write_text(
            json.dumps(
                [
                    {"name": "Dup", "league": "中超", "tier": "TOP_LEAGUE",
                     "strength": 60, "facility": 60, "salary_level": 60},
                    {"name": "Dup", "league": "中甲", "tier": "LOW_PRO",
                     "strength": 55, "facility": 55, "salary_level": 55},
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="重复"):
            mc.load_clubs(path)

    def test_load_events_covers_all_types(self, tmp_path):
        path = tmp_path / "events.json"
        path.write_text(
            json.dumps(
                [
                    {"type": event_type, "description": f"{event_type}事件",
                     "choice_a": "A", "choice_b": "B", "effect": "none"}
                    for event_type in s.EVENT_TYPES
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        events = me.load_events(path)
        assert {event.type for event in events} == set(s.EVENT_TYPES)

    def test_load_events_rejects_missing_type(self, tmp_path):
        path = tmp_path / "events.json"
        path.write_text(
            json.dumps(
                [{"type": "training", "description": "x", "choice_a": "A",
                  "choice_b": "B", "effect": "none"}],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="类型覆盖"):
            me.load_events(path)
