"""主仪表盘（UIDesign §6）：顶部状态栏 + 球员卡 + 属性面板 + 操作栏 + 日志。"""

from datetime import date

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import config.settings as settings
from models.career import Career
from models.club import Club
from models.match import MatchRecord
from models.player import Player
from ui.components.attribute_panel import AttributePanel
from ui.components.button_panel import ButtonPanel
from ui.components.player_card import PlayerCard


def format_date(iso_date: str) -> str:
    """ISO 日期 -> '2026年01月01日' 中文显示。"""
    d = date.fromisoformat(iso_date)
    return f"{d.year}年{d.month:02d}月{d.day:02d}日"


class MainDashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.player: Player | None = None
        self.club: Club | None = None
        self.matches: list[MatchRecord] = []
        self.career: Career | None = None
        self.attribute_panel = AttributePanel()
        self.button_panel = ButtonPanel()

        root = QVBoxLayout(self)
        root.addLayout(self._build_top_bar())

        body = QHBoxLayout()
        body.addWidget(self._build_player_card(), 1)
        body.addWidget(self.attribute_panel, 2)
        body.addWidget(self.button_panel, 1)
        root.addLayout(body, 1)

        log_frame = QFrame()
        log_frame.setProperty("role", "card")
        log_layout = QVBoxLayout(log_frame)
        log_title = QLabel("新闻 / 事件")
        log_title.setProperty("role", "section")
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(150)
        log_layout.addWidget(log_title)
        log_layout.addWidget(self.log_view)
        root.addWidget(log_frame)

    def _build_top_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        self.date_label = QLabel("")
        self.season_label = QLabel("")
        self.club_label = QLabel("")
        self.reputation_label = QLabel("")
        self.money_label = QLabel("")
        for label in (
            self.date_label,
            self.season_label,
            self.club_label,
            self.reputation_label,
            self.money_label,
        ):
            label.setProperty("role", "data")
            bar.addWidget(label)
        bar.addStretch(1)
        return bar

    def _build_player_card(self) -> QFrame:
        self.player_card = PlayerCard()
        return self.player_card

    def set_data(
        self,
        player: Player,
        club: Club | None = None,
        matches: list[MatchRecord] | None = None,
        career: Career | None = None,
    ) -> None:
        """绑定完整存档数据并刷新界面。"""
        self.player = player
        self.club = club
        self.matches = matches or []
        self.career = career
        self.refresh()

    def refresh(self) -> None:
        """用当前数据刷新全部显示。"""
        if self.player is None:
            return
        self.date_label.setText(format_date(self.player.current_date))
        self.season_label.setText(f"第 {self.player.season} 赛季")
        self.club_label.setText(f"球队: {self.club.name if self.club else '青训'}")
        self.reputation_label.setText(f"声望: {self.player.reputation}")
        self.money_label.setText(f"金钱: {self.player.money}")
        self.player_card.refresh(self.player)
        self.attribute_panel.refresh(self.player)

    def log(self, message: str) -> None:
        """追加一条日志/新闻。"""
        self.log_view.append(message)
