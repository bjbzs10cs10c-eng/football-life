"""数据库连接与初始化（A2）。

统一从 config/settings.py 读取数据库路径与属性清单，
保证表结构（15 项属性）与配置始终保持一致。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import config.settings as settings

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = Path(__file__).resolve().parent / "init.sql"

EXPECTED_TABLES = {"player", "player_attributes", "club", "matches", "career", "events"}


def _resolve_path(db_path=None) -> Path:
    """解析数据库路径：未指定时使用配置路径（相对路径基于项目根目录）。"""
    if db_path is not None:
        return Path(db_path)
    p = Path(settings.DATABASE_PATH)
    return p if p.is_absolute() else PROJECT_ROOT / p


def connect(db_path=None) -> sqlite3.Connection:
    """打开数据库连接；目录不存在时自动创建。"""
    path = _resolve_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path=None, conn=None) -> None:
    """执行 init.sql 建表（幂等：已存在的表不重建、不报错）。"""
    settings.validate_config()
    own_conn = conn is None
    if own_conn:
        conn = connect(db_path)
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        if own_conn:
            conn.close()


def list_tables(conn) -> set:
    """返回库中全部业务表名。"""
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {row["name"] for row in rows}


def attribute_columns(conn) -> list:
    """返回 player_attributes 中属性列（不含 player_id），顺序即建表顺序。"""
    rows = conn.execute("PRAGMA table_info(player_attributes)").fetchall()
    return [row["name"] for row in rows if row["name"] != "player_id"]


def validate_schema(conn) -> list:
    """校验数据库 schema 与配置一致，返回问题列表；一致时返回空列表。"""
    errors = []
    tables = list_tables(conn)
    missing = sorted(EXPECTED_TABLES - tables)
    if missing:
        errors.append(f"缺少数据表: {missing}")

    if "player_attributes" in tables:
        columns = attribute_columns(conn)
        if columns != settings.ALL_ATTRIBUTES:
            errors.append(f"player_attributes 属性列与配置不一致: 表={columns}")
    return errors
