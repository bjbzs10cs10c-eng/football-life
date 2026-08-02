"""转会页（UIDesign §10）。

展示当前可加入的俱乐部（systems.transfer.eligible_clubs），
接受转会走与模型一致的 transfer() 校验；拒绝则不改变任何数据。
"""

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

import config.settings as settings
import models.club as mc
import systems.transfer as tr
from models.player import Player


class TransferPage(QWidget):
    transfer_accepted = pyqtSignal(Player, mc.Club)
    transfer_rejected = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.player: Player | None = None
        self.targets: list[mc.Club] = []
        root = QVBoxLayout(self)

        title = QLabel("转会市场")
        title.setProperty("role", "section")
        root.addWidget(title)
        self.hint_label = QLabel("")
        self.hint_label.setProperty("role", "dim")
        root.addWidget(self.hint_label)

        self.list_area = QScrollArea()
        self.list_area.setWidgetResizable(True)
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_area.setWidget(self.list_container)
        root.addWidget(self.list_area, 1)

        self.back_button = QPushButton("返回（暂不转会）")
        self.back_button.setFixedSize(200, 45)
        self.back_button.clicked.connect(self.transfer_rejected.emit)
        root.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignCenter)

    def refresh(
        self,
        player: Player,
        clubs: list[mc.Club] | None = None,
    ) -> None:
        """按球员当前门槛重建候选俱乐部列表。"""
        self.player = player
        self.targets = tr.eligible_clubs(player, clubs)
        self._clear_list()
        if not self.targets:
            self.hint_label.setText(
                "暂无俱乐部向你发出邀约，提升能力与声望后再来看看。"
            )
            return
        self.hint_label.setText(
            f"共 {len(self.targets)} 家俱乐部可加入"
        )
        for club in self.targets:
            self.list_layout.addWidget(self._club_row(club))
        self.list_layout.addStretch(1)

    def _clear_list(self) -> None:
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _club_row(self, club: mc.Club) -> QFrame:
        frame = QFrame()
        frame.setProperty("role", "card")
        row = QHBoxLayout(frame)
        info = QLabel(
            f"{club.name}\n"
            f"{club.league}  |  {settings.CLUB_TIER_NAMES_ZH[club.tier]}  |  "
            f"实力 {club.strength}\n月薪 {tr.salary_for(club)}"
        )
        row.addWidget(info, 1)
        accept = QPushButton("接受")
        accept.setFixedSize(100, 40)
        accept.clicked.connect(lambda _=False, c=club: self._accept(c))
        row.addWidget(accept)
        return frame

    def _accept(self, club: mc.Club) -> None:
        if self.player is None:
            return
        tr.transfer(self.player, club)  # 与模型一致：门槛校验失败会抛错
        self.transfer_accepted.emit(self.player, club)
