"""属性面板组件（UIDesign §6.3 / §12）：15 项属性进度条分组展示。"""

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
            bar.setValue(player.attributes[key])
            value.setText(str(player.attributes[key]))
