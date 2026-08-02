"""事件选择弹窗（UIDesign §9 EventDialog）。

显示事件描述与两个选项（含效果说明），选择后返回所选选项（A/B）。
"""

from PyQt6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout

import config.settings as settings
from models.event import GameEvent, parse_effect

_SPECIAL_NAMES = {"condition": "体力", "money": "金钱", "reputation": "声望"}


def effect_to_text(effect: str) -> str:
    """把 effect 表达式转成中文展示文本，如 “shooting+3;condition-20” -> “射门+3，体力-20”。"""
    parsed = parse_effect(effect)
    if not parsed:
        return "无特殊效果"
    parts = []
    for key, delta in parsed.items():
        name = settings.ATTRIBUTE_NAMES_ZH.get(key, _SPECIAL_NAMES.get(key, key))
        parts.append(f"{name}{delta:+d}")
    return "，".join(parts)


class EventDialog(QDialog):
    def __init__(self, event: GameEvent, parent=None):
        super().__init__(parent)
        self.setWindowTitle("事件")
        self.selected_choice: str | None = None

        layout = QVBoxLayout(self)
        description = QLabel(event.description)
        description.setWordWrap(True)
        layout.addWidget(description)

        self.button_a = QPushButton(f"{event.choice_a}\n({effect_to_text(event.effect_a)})")
        self.button_b = QPushButton(f"{event.choice_b}\n({effect_to_text(event.effect_b)})")
        self.button_a.clicked.connect(lambda: self._choose("A"))
        self.button_b.clicked.connect(lambda: self._choose("B"))
        layout.addWidget(self.button_a)
        layout.addWidget(self.button_b)

    def _choose(self, choice: str) -> None:
        self.selected_choice = choice
        self.accept()
