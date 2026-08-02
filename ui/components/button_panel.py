"""操作按钮面板（UIDesign §6.5）。"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QWidget


class ButtonPanel(QWidget):
    training_requested = pyqtSignal()
    match_requested = pyqtSignal()
    transfer_requested = pyqtSignal()
    career_requested = pyqtSignal()
    save_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addStretch(1)
        buttons = [
            ("训练", self.training_requested),
            ("下一场比赛", self.match_requested),
            ("转会市场", self.transfer_requested),
            ("生涯统计", self.career_requested),
            ("保存进度", self.save_requested),
        ]
        self._buttons = {}
        for text, signal in buttons:
            button = QPushButton(text)
            button.setFixedSize(150, 50)
            button.clicked.connect(signal.emit)
            layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)
            self._buttons[text] = button
        layout.addStretch(1)
