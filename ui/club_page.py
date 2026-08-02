"""球队页：只读展示当前俱乐部信息（对应 club 表字段）。"""

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QFormLayout, QLabel, QPushButton, QVBoxLayout, QWidget

import config.settings as settings
import systems.transfer as tr
from models.club import Club


class ClubPage(QWidget):
    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        title = QLabel("当前球队")
        title.setProperty("role", "section")
        root.addWidget(title)

        self.name_label = self._data_label()
        form = QWidget()
        form_layout = QFormLayout(form)
        form_layout.setSpacing(16)
        self.league_label = self._data_label()
        self.tier_label = self._data_label()
        self.strength_label = self._data_label()
        self.facility_label = self._data_label()
        self.salary_level_label = self._data_label()
        self.salary_label = self._data_label()
        form_layout.addRow("俱乐部：", self.name_label)
        form_layout.addRow("联赛：", self.league_label)
        form_layout.addRow("档位：", self.tier_label)
        form_layout.addRow("实力：", self.strength_label)
        form_layout.addRow("训练设施：", self.facility_label)
        form_layout.addRow("工资水平：", self.salary_level_label)
        form_layout.addRow("月薪：", self.salary_label)
        root.addWidget(form)
        root.addStretch(1)

        back = QPushButton("返回")
        back.setFixedSize(150, 45)
        back.clicked.connect(self.back_requested.emit)
        root.addWidget(back, alignment=Qt.AlignmentFlag.AlignCenter)

    @staticmethod
    def _data_label() -> QLabel:
        label = QLabel("--")
        label.setProperty("role", "data")
        return label

    def refresh(self, club: Club | None) -> None:
        """只读展示当前俱乐部；无俱乐部时显示青训提示。"""
        if club is None:
            self.name_label.setText("青训")
            self.league_label.setText("—")
            self.tier_label.setText("—")
            self.strength_label.setText("—")
            self.facility_label.setText("—")
            self.salary_level_label.setText("—")
            self.salary_label.setText("—")
            return
        self.name_label.setText(club.name)
        self.league_label.setText(club.league)
        self.tier_label.setText(settings.CLUB_TIER_NAMES_ZH[club.tier])
        self.strength_label.setText(str(club.strength))
        self.facility_label.setText(str(club.facility))
        self.salary_level_label.setText(str(club.salary_level))
        self.salary_label.setText(str(tr.salary_for(club)))
