"""比赛页（UIDesign §8）。

随机对手、自动文字模拟；比分/逐条事件/评分/结算正确显示，
比赛记录进入模型列表（存档同步），比赛后推进 1 天并检查比赛事件。
播放期间按钮禁用，防止连点重复比赛。
"""

import random as _random

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import models.club as club_model
import config.settings as settings
import systems.career as career
import systems.match_engine as match_engine
from models.club import Club
from models.career import Career
from models.match import MatchRecord
from models.player import Player
from ui.components.MatchTextBox import MatchTextBox
from ui.event_flow import format_event_log, run_event_if_any


class MatchPage(QWidget):
    data_changed = pyqtSignal()
    log_message = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.player: Player | None = None
        self.club: Club | None = None
        self.matches: list[MatchRecord] = []
        self.career: Career | None = None
        self._busy = False

        layout = QVBoxLayout(self)
        title = QLabel("比赛")
        title.setProperty("role", "section")
        self.fixture_label = QLabel("")
        self.fixture_label.setProperty("role", "title")
        self.day_label = QLabel("")
        self.day_label.setProperty("role", "data")
        self.score_label = QLabel("比分: --")
        self.score_label.setProperty("role", "data")
        self.rating_label = QLabel("评分: --")
        self.rating_label.setProperty("role", "data")
        self.settle_label = QLabel("")
        self.settle_label.setProperty("role", "dim")
        layout.addWidget(title)
        layout.addWidget(self.fixture_label)
        layout.addWidget(self.day_label)
        layout.addWidget(self.score_label)
        layout.addWidget(self.rating_label)
        layout.addWidget(self.settle_label)

        row = QHBoxLayout()
        self.play_button = QPushButton("开始比赛")
        self.play_button.setFixedSize(180, 50)
        self.play_button.clicked.connect(self._on_play)
        self.back_button = QPushButton("返回")
        self.back_button.setFixedSize(120, 50)
        self.back_button.clicked.connect(self.finished.emit)
        row.addStretch(1)
        row.addWidget(self.play_button)
        row.addWidget(self.back_button)
        row.addStretch(1)
        layout.addLayout(row)

        self.match_text = MatchTextBox()
        self.match_text.setMinimumHeight(220)
        self.match_text.playback_finished.connect(self._on_playback_finished)
        layout.addWidget(self.match_text, 1)

    def set_data(
        self,
        player: Player,
        club: Club | None,
        matches: list[MatchRecord],
        career: Career | None = None,
    ) -> None:
        self.player = player
        self.club = club
        self.matches = matches
        self.career = career
        self._pick_opponent()
        self._refresh_match_day()
        self.refresh()

    def _refresh_match_day(self) -> None:
        """比赛日才允许比赛：非比赛日禁用按钮并显示倒计时。"""
        if self.player is None:
            return
        days = career.days_until_next_match(self.player)
        if days == 0:
            self.play_button.setEnabled(True)
            self.day_label.setText("今天是一周一度的比赛日！")
        else:
            self.play_button.setEnabled(False)
            self.day_label.setText(f"距离下一场比赛还有 {days} 天")

    def _pick_opponent(self) -> None:
        rng = _random
        pool = [
            c for c in club_model.load_clubs()
            if self.club is None or c.name != self.club.name
        ]
        self.opponent = rng.choice(pool) if pool else None

    def refresh(self) -> None:
        if self.player is None:
            return
        mine = self.club.name if self.club else "青训队"
        theirs = self.opponent.name if self.opponent else "无对手"
        self.fixture_label.setText(f"{mine}  VS  {theirs}")

    def _on_play(self) -> None:
        if self._busy or self.player is None or self.opponent is None:
            return
        if career.days_until_next_match(self.player) != 0:
            return  # 非比赛日不允许比赛（一周一赛）
        self._busy = True
        self.play_button.setEnabled(False)
        try:
            result = match_engine.play_match(
                self.player,
                self.opponent.name,
                self.club.strength if self.club else 60,
                self.opponent.strength,
            )
            self.matches.append(result.to_record())
            if self.career is not None:
                self.career.games += 1
                self.career.goals += result.goals
                self.career.assists += result.assists
            self.score_label.setText(
                f"比分: {self.player.name} 所在队 {result.result} {self.opponent.name}"
            )
            self.rating_label.setText(f"评分: {result.rating:.1f}")
            self.settle_label.setText(
                f"{result.outcome.upper()} | 奖金+{result.bonus}"
                f" | 声望+{result.reputation_gain} | 体力-{result.condition_cost}"
            )
            # 比赛占用当天，结束后进入下一天（下一场比赛在 6 天后）
            day_logs = career.advance_days(self.player, 1, club=self.club)
            for log in day_logs:
                self.log_message.emit(log)
            event_result = run_event_if_any(self.player, "match", self)
            if event_result is not None:
                self.log_message.emit(f"事件: {format_event_log(event_result)}")
            self.match_text.play_events(result.events, interval_ms=300)
            self.data_changed.emit()
        except Exception:
            self._busy = False
            self.play_button.setEnabled(True)
            raise

    def _on_playback_finished(self) -> None:
        self._busy = False
        self._refresh_match_day()
        self._pick_opponent()
        self.refresh()
