"""球员模型（A3）。

字段与 player / player_attributes 两表对应；属性采用 15 项配置清单
（config.settings.ALL_ATTRIBUTES）。训练/比赛等行为逻辑属于 systems/，
本阶段仅提供数据与校验。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import config.settings as settings


@dataclass
class Player:
    name: str
    age: int
    nationality: str
    position: str
    foot: str
    attributes: dict
    height: float | None = None
    club_id: int | None = None
    money: int = settings.START_MONEY
    reputation: int = settings.START_REPUTATION
    condition: int = settings.START_CONDITION
    current_date: str = settings.SEASON_START_DATE
    season: int = 1
    id: int | None = None

    def validate(self) -> "Player":
        """校验字段合法性，不合法抛出 ValueError。"""
        errors = []
        if not self.name or not self.name.strip():
            errors.append("姓名不能为空")
        if not isinstance(self.age, int) or self.age < 1:
            errors.append(f"年龄须为正整数，当前 {self.age!r}")
        if not self.nationality or not self.nationality.strip():
            errors.append("国籍不能为空")
        if self.position not in settings.POSITION_CODES:
            errors.append(
                f"position 非法: {self.position!r}，可选 {settings.POSITION_CODES}"
            )
        if self.foot not in settings.FOOT_OPTIONS:
            errors.append(
                f"foot 非法: {self.foot!r}，可选 {settings.FOOT_OPTIONS}"
            )

        attr_keys = list(self.attributes.keys())
        if set(attr_keys) != set(settings.ALL_ATTRIBUTES) or len(attr_keys) != len(
            settings.ALL_ATTRIBUTES
        ):
            errors.append(
                f"attributes 必须包含且仅包含 15 项配置属性，当前键: {attr_keys}"
            )
        else:
            for key in settings.ALL_ATTRIBUTES:
                value = self.attributes[key]
                if (
                    not isinstance(value, int)
                    or isinstance(value, bool)
                    or not (settings.MIN_ATTRIBUTE <= value <= settings.MAX_ATTRIBUTE)
                ):
                    errors.append(
                        f"attributes[{key}] 须为 {settings.MIN_ATTRIBUTE}-"
                        f"{settings.MAX_ATTRIBUTE} 的整数，当前 {value!r}"
                    )

        for field_name, value in (("money", self.money), ("reputation", self.reputation)):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                errors.append(f"{field_name} 须为非负整数，当前 {value!r}")
        if (
            not isinstance(self.condition, int)
            or isinstance(self.condition, bool)
            or not (settings.MIN_CONDITION <= self.condition <= settings.MAX_CONDITION)
        ):
            errors.append(
                f"condition 须为 {settings.MIN_CONDITION}-"
                f"{settings.MAX_CONDITION} 的整数，当前 {self.condition!r}"
            )
        if not self.current_date or not self.current_date.strip():
            errors.append("current_date 不能为空")
        if not isinstance(self.season, int) or self.season < 1:
            errors.append(f"season 须为正整数，当前 {self.season!r}")

        if errors:
            raise ValueError("球员数据校验失败:\n" + "\n".join(errors))
        return self

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        return cls(**data)

    @classmethod
    def make_default_attributes(cls) -> dict:
        """生成一份 15 项属性齐全的默认字典（值取区间下界，B4 再随机化）。"""
        return {key: settings.MIN_ATTRIBUTE for key in settings.ALL_ATTRIBUTES}
