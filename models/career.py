"""生涯统计模型（B5）。

字段与 database/init.sql 的 career 表一一对应：
games / goals / assists / trophies / best_award。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class Career:
    games: int = 0
    goals: int = 0
    assists: int = 0
    trophies: int = 0
    best_award: str | None = None
    player_id: int | None = None

    def validate(self) -> "Career":
        """校验字段合法性，不合法抛出 ValueError。"""
        errors = []
        for field_name in ("games", "goals", "assists", "trophies"):
            value = getattr(self, field_name)
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 0
            ):
                errors.append(f"{field_name} 须为非负整数，当前 {value!r}")
        if self.best_award is not None and not self.best_award.strip():
            errors.append("best_award 不能为空白字符串")
        if errors:
            raise ValueError("生涯统计校验失败:\n" + "\n".join(errors))
        return self

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Career":
        return cls(**data)
