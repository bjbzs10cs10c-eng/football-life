"""生涯统计页（UIDesign §11）：展示 career 表对应数据。"""

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QFormLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from models.career import Career


class CareerPage(QWidget):
    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        title = QLabel("职业生涯")
        title.setProperty("role", "section")
        root.addWidget(title)

        form = QWidget()
        form_layout = QFormLayout(form)
        form_layout.setSpacing(16)
        self.games_label = self._data_label()
        self.goals_label = self._data_label()
        self.assists_label = self._data_label()
        self.trophies_label = self._data_label()
        self.best_award_label = self._data_label()
        form_layout.addRow("职业比赛：", self.games_label)
        form_layout.addRow("进球：", self.goals_label)
        form_layout.addRow("助攻：", self.assists_label)
        form_layout.addRow("冠军：", self.trophies_label)
        form_layout.addRow("最佳荣誉：", self.best_award_label)
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

    def refresh(self, career: Career | None) -> None:
        """用生涯数据刷新显示；无数据时按全 0 展示。"""
        if career is None:
            career = Career()
        career.validate()
        self.games_label.setText(str(career.games))
        self.goals_label.setText(str(career.goals))
        self.assists_label.setText(str(career.assists))
        self.trophies_label.setText(str(career.trophies))
        self.best_award_label.setText(career.best_award or "—")
