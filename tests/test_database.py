"""A2：数据库层测试。

覆盖：建表完整性、15 属性列与配置一致、外键约束、幂等初始化、
schema 校验（失败分支）、损坏库与不可写路径的错误处理。
"""

import sqlite3

import pytest

import config.settings as s
import database.db as db


@pytest.fixture()
def conn(tmp_path):
    c = db.connect(tmp_path / "test.db")
    yield c
    c.close()


class TestInitDb:
    def test_creates_all_six_tables(self, tmp_path):
        db.init_db(tmp_path / "test.db")
        c = db.connect(tmp_path / "test.db")
        try:
            assert db.list_tables(c) == db.EXPECTED_TABLES
            assert len(db.EXPECTED_TABLES) == 6
        finally:
            c.close()

    def test_init_is_idempotent(self, tmp_path):
        path = tmp_path / "test.db"
        db.init_db(path)
        db.init_db(path)  # 第二次执行不应报错
        c = db.connect(path)
        try:
            assert db.list_tables(c) == db.EXPECTED_TABLES
        finally:
            c.close()

    def test_init_creates_missing_parent_dirs(self, tmp_path):
        db.init_db(tmp_path / "a" / "b" / "test.db")
        assert (tmp_path / "a" / "b" / "test.db").exists()

    def test_player_attributes_columns_match_config(self, tmp_path):
        db.init_db(tmp_path / "test.db")
        c = db.connect(tmp_path / "test.db")
        try:
            columns = db.attribute_columns(c)
            assert columns == s.ALL_ATTRIBUTES
            assert len(columns) == 15
        finally:
            c.close()

    def test_validate_schema_ok_on_fresh_db(self, tmp_path):
        db.init_db(tmp_path / "test.db")
        c = db.connect(tmp_path / "test.db")
        try:
            assert db.validate_schema(c) == []
        finally:
            c.close()


class TestConstraints:
    def test_foreign_keys_enforced(self, conn):
        db.init_db(conn=conn)
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO player_attributes (player_id, shooting) VALUES (999, 60)"
            )

    def test_cascade_delete_removes_attributes(self, conn):
        db.init_db(conn=conn)
        conn.execute(
            "INSERT INTO player (name, age, nationality, position, foot, current_date)"
            " VALUES ('Li Ming', 17, 'CN', 'ST', 'R', '2026-01-01')"
        )
        player_id = conn.execute("SELECT id FROM player").fetchone()["id"]
        conn.execute(
            "INSERT INTO player_attributes (player_id, shooting) VALUES (?, 60)",
            (player_id,),
        )
        conn.execute("DELETE FROM player WHERE id = ?", (player_id,))
        assert conn.execute(
            "SELECT COUNT(*) AS n FROM player_attributes"
        ).fetchone()["n"] == 0


class TestValidateSchemaFailures:
    def test_reports_missing_table(self, conn):
        conn.execute("CREATE TABLE player (id INTEGER PRIMARY KEY)")
        errors = db.validate_schema(conn)
        assert any("缺少数据表" in e for e in errors)

    def test_reports_missing_attribute(self, conn):
        conn.execute(
            "CREATE TABLE player_attributes (player_id INTEGER PRIMARY KEY, shooting INTEGER)"
        )
        errors = db.validate_schema(conn)
        assert any("属性列与配置不一致" in e for e in errors)


class TestErrorHandling:
    def test_corrupt_database_raises_clear_error(self, tmp_path):
        path = tmp_path / "corrupt.db"
        path.write_bytes(b"this is not a sqlite database")
        c = db.connect(path)
        try:
            with pytest.raises(sqlite3.DatabaseError):
                c.execute("SELECT 1")
        finally:
            c.close()

    def test_unwritable_path_raises(self, tmp_path):
        blocker = tmp_path / "not_a_dir"
        blocker.write_text("x")
        with pytest.raises(OSError):
            db.connect(blocker / "child.db")
