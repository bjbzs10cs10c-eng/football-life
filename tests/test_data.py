"""A3：静态数据文件（clubs.json / events.json）完整性测试。"""

import json
from pathlib import Path

import config.settings as s
import models.event as me

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLUBS_FILE = PROJECT_ROOT / "data" / "clubs.json"
EVENTS_FILE = PROJECT_ROOT / "data" / "events.json"

# 等级 -> 允许的联赛（数据质量约定，与转会系统 tier 语义一致）
TIER_LEAGUES = {
    "AMATEUR": {"中乙"},
    "LOW_PRO": {"中甲", "英冠"},
    "TOP_LEAGUE": {"中超", "英超", "西甲", "德甲", "意甲", "法甲"},
    "ELITE": {"英超", "西甲", "德甲", "意甲", "法甲"},
}


class TestClubsJson:
    def test_file_exists_and_parses(self):
        assert CLUBS_FILE.exists()
        clubs = json.loads(CLUBS_FILE.read_text(encoding="utf-8"))
        assert isinstance(clubs, list)
        assert len(clubs) >= 10

    def test_required_fields_and_types(self):
        clubs = json.loads(CLUBS_FILE.read_text(encoding="utf-8"))
        required = ("name", "league", "tier", "strength", "facility", "salary_level")
        for club in clubs:
            for field_name in required:
                assert field_name in club, f"缺少字段 {field_name}: {club}"
            assert isinstance(club["name"], str) and club["name"].strip()
            assert isinstance(club["league"], str) and club["league"].strip()
            for field_name in ("strength", "facility", "salary_level"):
                value = club[field_name]
                assert isinstance(value, int) and not isinstance(value, bool)
                assert s.CLUB_VALUE_MIN <= value <= s.CLUB_VALUE_MAX

    def test_tier_coverage_and_names_unique(self):
        clubs = json.loads(CLUBS_FILE.read_text(encoding="utf-8"))
        tiers = {club["tier"] for club in clubs}
        assert tiers == set(s.CLUB_TIERS)
        names = [club["name"] for club in clubs]
        assert len(names) == len(set(names))

    def test_tier_league_consistency(self):
        clubs = json.loads(CLUBS_FILE.read_text(encoding="utf-8"))
        for club in clubs:
            assert club["tier"] in TIER_LEAGUES
            assert club["league"] in TIER_LEAGUES[club["tier"]], club


class TestEventsJson:
    def test_file_exists_and_parses(self):
        assert EVENTS_FILE.exists()
        events = json.loads(EVENTS_FILE.read_text(encoding="utf-8"))
        assert isinstance(events, list)
        assert len(events) >= 9

    def test_fields_match_events_table(self):
        events = json.loads(EVENTS_FILE.read_text(encoding="utf-8"))
        table_columns = {
            "type", "description", "choice_a", "choice_b",
            "effect_a", "effect_b",
        }
        for event in events:
            assert set(event.keys()) == table_columns, event

    def test_three_to_five_events_per_type(self):
        events = json.loads(EVENTS_FILE.read_text(encoding="utf-8"))
        for event_type in s.EVENT_TYPES:
            count = sum(1 for e in events if e["type"] == event_type)
            assert 3 <= count <= 5, f"类型 {event_type} 应有 3~5 条，当前 {count}"

    def test_effect_grammar_valid(self):
        events = json.loads(EVENTS_FILE.read_text(encoding="utf-8"))
        for event in events:
            for field_name in ("effect_a", "effect_b"):
                parsed = me.parse_effect(event[field_name])
                for key, delta in parsed.items():
                    assert isinstance(delta, int)
                    assert key in set(s.ALL_ATTRIBUTES) | set(
                        s.EVENT_SPECIAL_EFFECT_KEYS
                    )

    def test_no_duplicate_descriptions(self):
        events = json.loads(EVENTS_FILE.read_text(encoding="utf-8"))
        descriptions = [e["description"] for e in events]
        assert len(descriptions) == len(set(descriptions))
