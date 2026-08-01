-- 《Football Life》数据库初始化脚本（A2）
-- 表结构与命名统一采用 TDD §4（PRD 中的 match/event 表统一为 matches/events）。
-- 全部使用 IF NOT EXISTS，保证初始化幂等。

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS player (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    nationality TEXT NOT NULL,
    height REAL,
    position TEXT NOT NULL,
    foot TEXT NOT NULL,
    club_id INTEGER,
    money INTEGER NOT NULL DEFAULT 0,
    reputation INTEGER NOT NULL DEFAULT 0,
    condition INTEGER NOT NULL DEFAULT 100,
    current_date TEXT NOT NULL,
    season INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (club_id) REFERENCES club(id)
);

-- 15 项属性列与 config/settings.py 的 ALL_ATTRIBUTES 顺序保持一致
-- （由 database/db.validate_schema 自动校验）
CREATE TABLE IF NOT EXISTS player_attributes (
    player_id INTEGER PRIMARY KEY,
    shooting INTEGER NOT NULL DEFAULT 1,
    passing INTEGER NOT NULL DEFAULT 1,
    dribbling INTEGER NOT NULL DEFAULT 1,
    control INTEGER NOT NULL DEFAULT 1,
    defending INTEGER NOT NULL DEFAULT 1,
    heading INTEGER NOT NULL DEFAULT 1,
    pace INTEGER NOT NULL DEFAULT 1,
    acceleration INTEGER NOT NULL DEFAULT 1,
    strength INTEGER NOT NULL DEFAULT 1,
    stamina INTEGER NOT NULL DEFAULT 1,
    agility INTEGER NOT NULL DEFAULT 1,
    decision INTEGER NOT NULL DEFAULT 1,
    professionalism INTEGER NOT NULL DEFAULT 1,
    pressure INTEGER NOT NULL DEFAULT 1,
    leadership INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (player_id) REFERENCES player(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS club (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    league TEXT,
    tier TEXT NOT NULL,
    strength INTEGER NOT NULL,
    facility INTEGER NOT NULL,
    salary_level INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    opponent TEXT NOT NULL,
    result TEXT NOT NULL,
    goals INTEGER NOT NULL DEFAULT 0,
    assists INTEGER NOT NULL DEFAULT 0,
    rating REAL NOT NULL DEFAULT 6.0,
    date TEXT NOT NULL,
    season INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (player_id) REFERENCES player(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS career (
    player_id INTEGER PRIMARY KEY,
    games INTEGER NOT NULL DEFAULT 0,
    goals INTEGER NOT NULL DEFAULT 0,
    assists INTEGER NOT NULL DEFAULT 0,
    trophies INTEGER NOT NULL DEFAULT 0,
    best_award TEXT,
    FOREIGN KEY (player_id) REFERENCES player(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    description TEXT NOT NULL,
    choice_a TEXT,
    choice_b TEXT,
    effect TEXT
);

CREATE INDEX IF NOT EXISTS idx_matches_player ON matches(player_id);
