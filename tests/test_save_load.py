"""B5：存档/读档系统测试。

覆盖：五表（player/player_attributes/club/matches/career）保存读取往返、
单存档覆盖语义、无存档报错、校验失败不破坏旧存档、损坏库报错。
"""

import random
import sqlite3

import pytest

import config.settings as s
import models.career as mcareer
import models.club as mclub
import models.match as mmatch
import systems.player_creation as pc
import systems.save_load as sl


def make_player():
    return pc.create_player("Li Ming", "CN", "ST", "R", rng=random.Random(1))


def make_club():
    return mclub.Club(
        name="上海海港", league="中超", tier="TOP_LEAGUE",
        strength=78, facility=72, salary_level=70,
    )


def make_matches():
    return [
        mmatch.MatchRecord(
            opponent="Test A", result="2-1", date="2026-01-08",
            goals=1, assists=1, rating=7.5,
        ),
        mmatch.MatchRecord(
            opponent="Test B", result="0-2", date="2026-01-15",
            goals=0, assists=0, rating=6.0,
        ),
    ]


def make_career():
    return mcareer.Career(
        games=10, goals=5, assists=3, trophies=1, best_award="联赛冠军"
    )


def assert_player_equal(left, right):
    left_dict = left.to_dict()
    right_dict = right.to_dict()
    left_dict.pop("id", None)
    right_dict.pop("id", None)
    left_dict.pop("player_id", None)
    right_dict.pop("player_id", None)
    assert left_dict == right_dict


class TestPlayerRoundTrip:
    def test_player_and_attributes_round_trip(self, tmp_path):
        player = make_player()
        player_id = sl.save_game(player, db_path=tmp_path / "save.db")
        data = sl.load_game(db_path=tmp_path / "save.db")
        assert data.player.id == player_id
        assert_player_equal(data.player, player)
        assert data.player.overall() == player.overall()

    def test_saves_single_player_row(self, tmp_path):
        sl.save_game(make_player(), db_path=tmp_path / "save.db")
        conn = sqlite3.connect(tmp_path / "save.db")
        try:
            assert conn.execute("SELECT COUNT(*) FROM player").fetchone()[0] == 1
            assert (
                conn.execute("SELECT COUNT(*) FROM player_attributes").fetchone()[0]
                == 1
            )
        finally:
            conn.close()


class TestClubRoundTrip:
    def test_club_round_trip_and_link(self, tmp_path):
        player = make_player()
        club = make_club()
        sl.save_game(player, club=club, db_path=tmp_path / "save.db")
        data = sl.load_game(db_path=tmp_path / "save.db")
        assert data.club is not None
        assert data.club.name == club.name
        assert data.club.league == club.league
        assert data.club.tier == club.tier
        assert data.club.strength == club.strength
        assert data.club.facility == club.facility
        assert data.club.salary_level == club.salary_level
        assert data.player.club_id == data.club.id

    def test_no_club_gives_none(self, tmp_path):
        sl.save_game(make_player(), db_path=tmp_path / "save.db")
        data = sl.load_game(db_path=tmp_path / "save.db")
        assert data.club is None
        assert data.player.club_id is None


class TestMatchesAndCareerRoundTrip:
    def test_matches_round_trip_in_order(self, tmp_path):
        matches = make_matches()
        sl.save_game(make_player(), matches=matches, db_path=tmp_path / "save.db")
        data = sl.load_game(db_path=tmp_path / "save.db")
        assert len(data.matches) == 2
        for saved, loaded in zip(matches, data.matches):
            assert_player_equal(loaded, saved)
            assert loaded.player_id == data.player.id

    def test_career_round_trip(self, tmp_path):
        career = make_career()
        sl.save_game(make_player(), career=career, db_path=tmp_path / "save.db")
        data = sl.load_game(db_path=tmp_path / "save.db")
        assert data.career is not None
        assert data.career.games == 10
        assert data.career.goals == 5
        assert data.career.assists == 3
        assert data.career.trophies == 1
        assert data.career.best_award == "联赛冠军"
        assert data.career.player_id == data.player.id

    def test_empty_matches_and_career(self, tmp_path):
        sl.save_game(make_player(), db_path=tmp_path / "save.db")
        data = sl.load_game(db_path=tmp_path / "save.db")
        assert data.matches == []
        assert data.career is None


class TestSingleSaveSemantics:
    def test_second_save_overwrites_first(self, tmp_path):
        path = tmp_path / "save.db"
        sl.save_game(make_player(), db_path=path)
        other = make_player()
        other.name = "Wang Wu"
        sl.save_game(other, db_path=path)
        data = sl.load_game(db_path=path)
        assert data.player.name == "Wang Wu"
        conn = sqlite3.connect(path)
        try:
            assert conn.execute("SELECT COUNT(*) FROM player").fetchone()[0] == 1
            assert conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0] == 0
        finally:
            conn.close()

    def test_validation_failure_keeps_old_save(self, tmp_path):
        path = tmp_path / "save.db"
        sl.save_game(make_player(), db_path=path)
        bad = make_player()
        bad.position = "GK"
        with pytest.raises(ValueError, match="position"):
            sl.save_game(bad, db_path=path)
        data = sl.load_game(db_path=path)
        assert data.player.name == "Li Ming"


class TestLoadErrors:
    def test_no_save_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="存档"):
            sl.load_game(db_path=tmp_path / "empty.db")

    def test_corrupt_database_raises(self, tmp_path):
        path = tmp_path / "corrupt.db"
        path.write_bytes(b"not a sqlite database")
        with pytest.raises(sqlite3.DatabaseError):
            sl.load_game(db_path=path)

    def test_missing_attributes_raises_clear_error(self, tmp_path):
        path = tmp_path / "save.db"
        sl.save_game(make_player(), db_path=path)
        conn = sqlite3.connect(path)
        try:
            conn.execute("DELETE FROM player_attributes")
            conn.commit()
        finally:
            conn.close()
        with pytest.raises(ValueError, match="属性"):
            sl.load_game(db_path=path)


class TestConnReuse:
    def test_accepts_existing_connection(self, tmp_path):
        import database.db as db

        conn = db.connect(tmp_path / "save.db")
        try:
            player_id = sl.save_game(make_player(), conn=conn)
            data = sl.load_game(conn=conn)
            assert data.player.id == player_id
        finally:
            conn.close()
