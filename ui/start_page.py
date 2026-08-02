"""开始页（UIDesign §4）：新建生涯 / 读取存档 / 设置。"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

import config.settings as settings


class StartPage(QWidget):
    new_career_clicked = pyqtSignal()
    load_save_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addStretch(3)

        title = QLabel(settings.GAME_TITLE)
        title.setProperty("role", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("体验一个足球运动员从少年到传奇的一生")
        subtitle.setProperty("role", "subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(40)

        self.new_button = QPushButton("开始新生涯")
        self.new_button.setFixedSize(220, 50)
        self.new_button.clicked.connect(self.new_career_clicked.emit)

        self.load_button = QPushButton("读取存档")
        self.load_button.setFixedSize(220, 50)
        self.load_button.clicked.connect(self.load_save_clicked.emit)

        self.settings_button = QPushButton("设置")
        self.settings_button.setFixedSize(220, 50)
        self.settings_button.setEnabled(False)  # MVP 无设置页

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        button_row.addLayout(self._buttons_column())
        button_row.addStretch(1)
        layout.addLayout(button_row)
        layout.addStretch(3)

    def _buttons_column(self):
        column = QVBoxLayout()
        for button in (self.new_button, self.load_button, self.settings_button):
            column.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)
        return column
