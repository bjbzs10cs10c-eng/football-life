"""俱乐部模型（A3）。

字段与 database/init.sql 的 club 表一一对应：
name / league / tier / strength / facility / salary_level。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import config.settings as settings


@dataclass
class Club:
    name: str
    league: str
    tier: str
    strength: int
    facility: int
    salary_level: int
    id: int | None = None

    def validate(self) -> "Club":
        """校验字段合法性，不合法抛出 ValueError。"""
        errors = []
        if not self.name or not self.name.strip():
            errors.append("俱乐部名称不能为空")
        if not self.league or not self.league.strip():
            errors.append("俱乐部联赛不能为空")
        if self.tier not in settings.CLUB_TIERS:
            errors.append(
                f"tier 非法: {self.tier!r}，可选 {settings.CLUB_TIERS}"
            )
        for field in ("strength", "facility", "salary_level"):
            value = getattr(self, field)
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not (settings.CLUB_VALUE_MIN <= value <= settings.CLUB_VALUE_MAX)
            ):
                errors.append(
                    f"{field} 须为 {settings.CLUB_VALUE_MIN}-"
                    f"{settings.CLUB_VALUE_MAX} 的整数，当前 {value!r}"
                )
        if errors:
            raise ValueError("俱乐部数据校验失败:\n" + "\n".join(errors))
        return self

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Club":
        return cls(**data)


def load_clubs(path: str | Path | None = None) -> list[Club]:
    """读取 data/clubs.json，逐条校验并检查重复与等级覆盖。

    内存中的 Club.id 按数据文件顺序分配（1..N），供 player.club_id 引用；
    存档写入数据库后以数据库生成的 id 为准。
    """
    p = Path(path) if path is not None else Path(settings.CLUBS_DATA_FILE)
    if not p.is_absolute():
        p = Path(__file__).resolve().parent.parent / p
    raw = json.loads(p.read_text(encoding="utf-8"))
    clubs = []
    for index, item in enumerate(raw, start=1):
        club = Club.from_dict(item).validate()
        club.id = index
        clubs.append(club)

    names = [c.name for c in clubs]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        raise ValueError(f"俱乐部名称重复: {dupes}")

    missing_tiers = [
        tier for tier in settings.CLUB_TIERS
        if not any(c.tier == tier for c in clubs)
    ]
    if missing_tiers:
        raise ValueError(f"俱乐部数据缺少等级覆盖: {missing_tiers}")
    return clubs
