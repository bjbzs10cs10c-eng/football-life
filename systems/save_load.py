"""存档系统（B5）。

TDD §14：使用 SQLite 单一存档（saves/football_life.db）。
save_game() 保存 player / player_attributes / club / matches / career 五张表；
load_game() 读回为 SaveData。重复保存会覆盖旧存档。

约定：所有数据先完成校验再写入，校验失败抛出 ValueError 且不破坏旧存档。
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

import config.settings as settings
import database.db as db
from models.career import Career
from models.club import Club
from models.match import MatchRecord
from models.player import Player


@dataclass
class SaveData:
    """一次读档返回的完整数据。"""

    player: Player
    club: Club | None = None
    matches: list[MatchRecord] = field(default_factory=list)
    career: Career | None = None


def save_game(
    player: Player,
    club: Club | None = None,
    matches: list[MatchRecord] | tuple[MatchRecord, ...] = (),
    career: Career | None = None,
    db_path: str | Path | None = None,
    conn: sqlite3.Connection | None = None,
) -> int:
    """把完整档写入数据库，返回 player id。传入 conn 时复用连接。"""
    # 先全部校验，失败时不触碰数据库（旧存档保持完好）
    player.validate()
    if club is not None:
        club.validate()
    match_list = list(matches)
    for match in match_list:
        match.validate()
    if career is not None:
        career.validate()

    own_conn = conn is None
    if own_conn:
        conn = db.connect(db_path)
    try:
        db.init_db(conn=conn)
        with conn:
            # 单存档语义：清空旧数据（子表先删，避免外键问题）
            for table in ("matches", "career", "player_attributes", "player", "club"):
                conn.execute(f"DELETE FROM {table}")

            club_id = None
            if club is not None:
                cursor = conn.execute(
                    "INSERT INTO club (name, league, tier, strength, facility, salary_level)"
                    " VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        club.name,
                        club.league,
                        club.tier,
                        club.strength,
                        club.facility,
                        club.salary_level,
                    ),
                )
                club_id = cursor.lastrowid

            cursor = conn.execute(
                "INSERT INTO player (name, age, nationality, height, position, foot,"
                " club_id, money, reputation, condition, current_date, season)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    player.name,
                    player.age,
                    player.nationality,
                    player.height,
                    player.position,
                    player.foot,
                    club_id,
                    player.money,
                    player.reputation,
                    player.condition,
                    player.current_date,
                    player.season,
                ),
            )
            player_id = cursor.lastrowid

            attr_columns = ", ".join(settings.ALL_ATTRIBUTES)
            attr_placeholders = ", ".join("?" for _ in settings.ALL_ATTRIBUTES)
            conn.execute(
                f"INSERT INTO player_attributes (player_id, {attr_columns})"
                f" VALUES (?, {attr_placeholders})",
                (player_id, *(player.attributes[a] for a in settings.ALL_ATTRIBUTES)),
            )

            for match in match_list:
                conn.execute(
                    "INSERT INTO matches (player_id, opponent, result, goals, assists,"
                    " rating, date, season) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        player_id,
                        match.opponent,
                        match.result,
                        match.goals,
                        match.assists,
                        match.rating,
                        match.date,
                        match.season,
                    ),
                )

            if career is not None:
                conn.execute(
                    "INSERT INTO career (player_id, games, goals, assists, trophies,"
                    " best_award) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        player_id,
                        career.games,
                        career.goals,
                        career.assists,
                        career.trophies,
                        career.best_award,
                    ),
                )
        return player_id
    finally:
        if own_conn:
            conn.close()


def load_game(
    db_path: str | Path | None = None,
    conn: sqlite3.Connection | None = None,
) -> SaveData:
    """读取最新存档；无存档抛 FileNotFoundError，数据缺失抛 ValueError。"""
    own_conn = conn is None
    if own_conn:
        conn = db.connect(db_path)
    try:
        # 空库/全新库先建表，再判断是否有存档
        db.init_db(conn=conn)
        row = conn.execute("SELECT * FROM player ORDER BY id DESC LIMIT 1").fetchone()
        if row is None:
            raise FileNotFoundError(f"未找到存档: {db_path or settings.DATABASE_PATH}")

        attrs_row = conn.execute(
            "SELECT * FROM player_attributes WHERE player_id = ?", (row["id"],)
        ).fetchone()
        if attrs_row is None:
            raise ValueError("存档损坏：缺少属性数据")
        attributes = {
            attr: attrs_row[attr] for attr in settings.ALL_ATTRIBUTES
        }

        player = Player(
            id=row["id"],
            name=row["name"],
            age=row["age"],
            nationality=row["nationality"],
            height=row["height"],
            position=row["position"],
            foot=row["foot"],
            club_id=row["club_id"],
            money=row["money"],
            reputation=row["reputation"],
            condition=row["condition"],
            current_date=row["current_date"],
            season=row["season"],
            attributes=attributes,
        ).validate()

        club = None
        if row["club_id"] is not None:
            club_row = conn.execute(
                "SELECT * FROM club WHERE id = ?", (row["club_id"],)
            ).fetchone()
            if club_row is not None:
                club = Club(
                    id=club_row["id"],
                    name=club_row["name"],
                    league=club_row["league"],
                    tier=club_row["tier"],
                    strength=club_row["strength"],
                    facility=club_row["facility"],
                    salary_level=club_row["salary_level"],
                ).validate()

        matches = [
            MatchRecord(
                id=match_row["id"],
                player_id=match_row["player_id"],
                opponent=match_row["opponent"],
                result=match_row["result"],
                goals=match_row["goals"],
                assists=match_row["assists"],
                rating=match_row["rating"],
                date=match_row["date"],
                season=match_row["season"],
            ).validate()
            for match_row in conn.execute(
                "SELECT * FROM matches WHERE player_id = ? ORDER BY id",
                (row["id"],),
            )
        ]

        career = None
        career_row = conn.execute(
            "SELECT * FROM career WHERE player_id = ?", (row["id"],)
        ).fetchone()
        if career_row is not None:
            career = Career(
                player_id=career_row["player_id"],
                games=career_row["games"],
                goals=career_row["goals"],
                assists=career_row["assists"],
                trophies=career_row["trophies"],
                best_award=career_row["best_award"],
            ).validate()

        return SaveData(player=player, club=club, matches=matches, career=career)
    finally:
        if own_conn:
            conn.close()
