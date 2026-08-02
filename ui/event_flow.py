"""事件触发流程辅助（C12）。

训练/比赛等行动后调用 run_event_if_any()：按配置概率触发事件弹窗，
玩家选择后应用效果并返回结果；未触发返回 None。
"""

from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QWidget

from models.event import GameEvent
from models.player import Player
from systems.event_manager import handle_event, random_event
import config.settings as settings
from ui.components.EventDialog import EventDialog, effect_to_text

_SPECIAL_NAMES = {"condition": "体力", "money": "金钱", "reputation": "声望"}


def run_event_if_any(
    player: Player,
    event_type: str,
    parent: QWidget | None = None,
    rng=None,
) -> dict | None:
    """触发并处理一条事件；返回 {"event", "choice", "changes"} 或 None。"""
    event = random_event(event_type, rng)
    if event is None:
        return None
    dialog = EventDialog(event, parent)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    changes = handle_event(player, event, dialog.selected_choice)
    return {
        "event": event,
        "choice": dialog.selected_choice,
        "changes": changes,
    }


def format_event_log(result: dict) -> str:
    """把事件结果格式化为日志文本（含所选选项与效果）。"""
    event: GameEvent = result["event"]
    choice = result["choice"]
    text = event.choice_a if choice == "A" else event.choice_b
    parts = [text]
    for key, delta in result["changes"].items():
        if delta == 0:
            continue
        name = settings.ATTRIBUTE_NAMES_ZH.get(key, _SPECIAL_NAMES.get(key, key))
        parts.append(f"{name}{delta:+d}")
    return "，".join(parts)
