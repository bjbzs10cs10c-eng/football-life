"""比赛记录模型（A3）。

字段与 database/init.sql 的 matches 表一一对应。比赛模拟逻辑属于
systems/match_engine.py，本阶段仅提供数据与校验。
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

import config.settings as settings

_RESULT_RE = re.compile(r"^\d+-\d+$")


@dataclass
class MatchRecord:
    opponent: str
    result: str
    date: str
    goals: int = 0
    assists: int = 0
    rating: float = settings.RATING_BASE
    season: int = 1
    player_id: int | None = None
    id: int | None = None

    def validate(self) -> "MatchRecord":
        """校验字段合法性，不合法抛出 ValueError。"""
        errors = []
        if not self.opponent or not self.opponent.strip():
            errors.append("对手不能为空")
        if not _RESULT_RE.match(self.result or ""):
            errors.append(f"result 须为 '进球-失球' 格式，当前 {self.result!r}")
        if not self.date or not self.date.strip():
            errors.append("date 不能为空")
        for field_name in ("goals", "assists"):
            value = getattr(self, field_name)
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 0
            ):
                errors.append(f"{field_name} 须为非负整数，当前 {value!r}")
        if (
            not isinstance(self.rating, (int, float))
            or isinstance(self.rating, bool)
            or not (settings.RATING_MIN <= self.rating <= settings.RATING_MAX)
        ):
            errors.append(
                f"rating 须为 {settings.RATING_MIN}-{settings.RATING_MAX}，"
                f"当前 {self.rating!r}"
            )
        if not isinstance(self.season, int) or self.season < 1:
            errors.append(f"season 须为正整数，当前 {self.season!r}")
        if errors:
            raise ValueError("比赛记录校验失败:\n" + "\n".join(errors))
        return self

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MatchRecord":
        return cls(**data)
