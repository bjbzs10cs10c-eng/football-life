"""随机事件模型（A3 / B8）。

字段与 database/init.sql 的 events 表对应（effect 拆分为选项效果）：
type / description / choice_a / choice_b / effect_a / effect_b。
effect_a / effect_b 分别对应选择 A / B 的效果，采用简洁表达式，
例如 "shooting+3;condition-20" 或 "none"。
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import config.settings as settings

EFFECT_NONE = "none"
_EFFECT_TOKEN_RE = re.compile(r"^([a-z_]+)([+-]\d+)$")
_ALLOWED_EFFECT_KEYS = set(settings.ALL_ATTRIBUTES) | set(
    settings.EVENT_SPECIAL_EFFECT_KEYS
)


def parse_effect(effect: str) -> dict:
    """把 effect 表达式解析为 {键: 增量}；'none' 返回空字典。

    增量支持负值，例如 "condition-20"。解析失败抛出 ValueError。
    """
    if effect == EFFECT_NONE:
        return {}
    tokens = [token.strip() for token in effect.split(";") if token.strip()]
    parsed = {}
    for token in tokens:
        match = _EFFECT_TOKEN_RE.match(token)
        if not match:
            raise ValueError(f"effect 语法错误: {token!r}（应为 键+增量 或 'none'）")
        key, delta = match.group(1), int(match.group(2))
        if key not in _ALLOWED_EFFECT_KEYS:
            raise ValueError(
                f"effect 使用了未知键: {key!r}，可选 {sorted(_ALLOWED_EFFECT_KEYS)}"
            )
        if key in parsed:
            raise ValueError(f"effect 键重复: {key!r}")
        parsed[key] = delta
    return parsed


@dataclass
class GameEvent:
    type: str
    description: str
    choice_a: str
    choice_b: str
    effect_a: str
    effect_b: str
    id: int | None = None

    def validate(self) -> "GameEvent":
        """校验字段合法性，不合法抛出 ValueError。"""
        errors = []
        if self.type not in settings.EVENT_TYPES:
            errors.append(
                f"type 非法: {self.type!r}，可选 {settings.EVENT_TYPES}"
            )
        for field_name in ("description", "choice_a", "choice_b"):
            value = getattr(self, field_name)
            if not value or not value.strip():
                errors.append(f"{field_name} 不能为空")
        for field_name in ("effect_a", "effect_b"):
            value = getattr(self, field_name)
            if not value or not value.strip():
                errors.append(f"{field_name} 不能为空")
            else:
                try:
                    parse_effect(value)
                except ValueError as exc:
                    errors.append(str(exc))
        if errors:
            raise ValueError("事件数据校验失败:\n" + "\n".join(errors))
        return self

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "GameEvent":
        return cls(**data)


def load_events(path: str | Path | None = None) -> list[GameEvent]:
    """读取 data/events.json，逐条校验并检查类型覆盖。"""
    p = Path(path) if path is not None else Path(settings.EVENT_DATA_FILE)
    if not p.is_absolute():
        p = Path(__file__).resolve().parent.parent / p
    raw = json.loads(p.read_text(encoding="utf-8"))
    events = [GameEvent.from_dict(item).validate() for item in raw]

    missing_types = [
        event_type for event_type in settings.EVENT_TYPES
        if not any(event.type == event_type for event in events)
    ]
    if missing_types:
        raise ValueError(f"事件数据缺少类型覆盖: {missing_types}")
    return events
