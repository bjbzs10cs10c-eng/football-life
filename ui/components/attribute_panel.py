"""属性面板组件（UIDesign §6.3 / §12 / §13）。

15 项属性进度条分组展示；refresh 时对发生变化的属性播放 72→74 式平滑动效。
"""

from PyQt6.QtCore import QEasingCurve, QVariantAnimation
from PyQt6.QtWidgets import (
    QGridLayout,
    QLabel,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

import config.settings as settings
from models.player import Player


class AttributePanel(QScrollArea):
    """按技术/身体/心理三组展示全部 15 项属性。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self._last_values: dict = {}
        self._animations: dict = {}
        container = QWidget()
        self._layout = QVBoxLayout(container)
        self._bars = {}
        for group, keys in (
            ("技术能力", settings.ATTRIBUTE_TECHNICAL),
            ("身体能力", settings.ATTRIBUTE_PHYSICAL),
            ("心理能力", settings.ATTRIBUTE_MENTAL),
        ):
            section = QLabel(group)
            section.setProperty("role", "section")
            self._layout.addWidget(section)
            grid = QGridLayout()
            for row, key in enumerate(keys):
                name = QLabel(settings.ATTRIBUTE_NAMES_ZH[key])
                bar = QProgressBar()
                bar.setRange(settings.MIN_ATTRIBUTE, settings.MAX_ATTRIBUTE)
                value = QLabel("--")
                value.setProperty("role", "data")
                grid.addWidget(name, row, 0)
                grid.addWidget(bar, row, 1)
                grid.addWidget(value, row, 2)
                self._bars[key] = (bar, value)
            self._layout.addLayout(grid)
        self._layout.addStretch(1)
        self.setWidget(container)

    def refresh(self, player: Player) -> None:
        """用球员属性刷新全部进度条。"""
        for key, (bar, value) in self._bars.items():
            new_value = player.attributes[key]
            old_value = self._last_values.get(key, new_value)
            if old_value != new_value:
                self._animate(key, bar, value, old_value, new_value)
            else:
                bar.setValue(new_value)
                value.setText(str(new_value))
            self._last_values[key] = new_value

    def _animate(
        self,
        key: str,
        bar: QProgressBar,
        value_label: QLabel,
        start: int,
        end: int,
    ) -> None:
        """旧值 -> 新值的平滑动效（约 600ms），结束后定格最终值。"""
        animation = self._animations.get(key)
        if animation is not None:
            animation.stop()
        animation = QVariantAnimation(self)
        animation.setStartValue(start)
        animation.setEndValue(end)
        animation.setDuration(600)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        def on_value(changed) -> None:
            current = int(changed)
            bar.setValue(current)
            value_label.setText(str(current))

        animation.valueChanged.connect(on_value)
        animation.finished.connect(lambda: value_label.setText(str(end)))
        animation.start()
        self._animations[key] = animation
