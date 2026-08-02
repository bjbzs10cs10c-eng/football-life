"""主窗口（C11-C13）。

页面：开始 / 创建球员 / 主仪表盘 / 训练 / 比赛 / 转会 / 生涯 / 球队。
全流程：新建档 → 创建 → 训练/比赛/事件 → 转会 → 退役评价。
训练与比赛页由 C12 实现，通过 data_changed/log_message/finished 与仪表盘联动。
"""

from PyQt6.QtWidgets import QMainWindow, QMessageBox, QStackedWidget

import config.settings as settings
import models.club as mc
import systems.career as career_sys
import systems.save_load as save_load
import systems.transfer as tr
from models.player import Player
from ui.career_page import CareerPage
from ui.club_page import ClubPage
from ui.create_player_page import CreatePlayerPage
from ui.main_dashboard import MainDashboard
from ui.match_page import MatchPage
from ui.start_page import StartPage
from ui.theme import apply_theme
from ui.training_page import TrainingPage
from ui.transfer_page import TransferPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(settings.GAME_TITLE)
        self.resize(settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT)
        apply_theme(self)

        self.start_page = StartPage()
        self.create_page = CreatePlayerPage()
        self.dashboard = MainDashboard()
        self.training_page = TrainingPage()
        self.match_page = MatchPage()
        self.transfer_page = TransferPage()
        self.career_page = CareerPage()
        self.club_page = ClubPage()

        self.stack = QStackedWidget()
        for page in (
            self.start_page,
            self.create_page,
            self.dashboard,
            self.training_page,
            self.match_page,
            self.transfer_page,
            self.career_page,
            self.club_page,
        ):
            self.stack.addWidget(page)
        self.setCentralWidget(self.stack)

        self.start_page.new_career_clicked.connect(
            lambda: self.stack.setCurrentWidget(self.create_page)
        )
        self.start_page.load_save_clicked.connect(self._load_save)
        self.create_page.player_created.connect(self._on_player_created)

        panel = self.dashboard.button_panel
        panel.training_requested.connect(self._open_training)
        panel.match_requested.connect(self._open_match)
        panel.transfer_requested.connect(self._show_transfer)
        panel.career_requested.connect(self._show_career)
        panel.club_requested.connect(self._show_club)
        panel.save_requested.connect(self._save)

        for page in (self.training_page, self.match_page):
            page.data_changed.connect(self.dashboard.refresh)
            page.log_message.connect(self.dashboard.log)
            page.finished.connect(self._back_to_dashboard)

        self.transfer_page.transfer_accepted.connect(self._on_transfer_accepted)
        self.transfer_page.transfer_rejected.connect(self._back_to_dashboard)
        self.career_page.back_requested.connect(self._back_to_dashboard)
        self.club_page.back_requested.connect(self._back_to_dashboard)

    # ---------- 流程入口 ----------

    def _load_save(self) -> None:
        try:
            data = save_load.load_game()
        except FileNotFoundError:
            QMessageBox.information(self, "读取存档", "未找到存档，请先开始新生涯。")
            return
        self.dashboard.set_data(data.player, data.club, data.matches, data.career)
        self.dashboard.log(f"欢迎回来，{data.player.name}！")
        self.stack.setCurrentWidget(self.dashboard)

    def _on_player_created(self, player: Player) -> None:
        self.dashboard.set_data(player)
        self.dashboard.log(f"欢迎加入足球生涯，{player.name}！从青训开始你的旅程。")
        self.stack.setCurrentWidget(self.dashboard)

    def _open_training(self) -> None:
        self.training_page.set_data(self.dashboard.player, self.dashboard.club)
        self.stack.setCurrentWidget(self.training_page)

    def _open_match(self) -> None:
        self.match_page.set_data(
            self.dashboard.player,
            self.dashboard.club,
            self.dashboard.matches,
        )
        self.stack.setCurrentWidget(self.match_page)

    def _show_transfer(self) -> None:
        if self.dashboard.player is None:
            return
        self.transfer_page.refresh(self.dashboard.player)
        self.stack.setCurrentWidget(self.transfer_page)

    def _on_transfer_accepted(self, player: Player, club: mc.Club) -> None:
        self.dashboard.set_data(
            player, club, self.dashboard.matches, self.dashboard.career
        )
        self.dashboard.log(
            f"转会完成！你已加盟 {club.name}（月薪 {tr.salary_for(club)}）"
        )
        self.stack.setCurrentWidget(self.dashboard)

    def _show_career(self) -> None:
        self.career_page.refresh(self.dashboard.career)
        self.stack.setCurrentWidget(self.career_page)

    def _show_club(self) -> None:
        self.club_page.refresh(self.dashboard.club)
        self.stack.setCurrentWidget(self.club_page)

    def _back_to_dashboard(self) -> None:
        self.dashboard.refresh()
        self.stack.setCurrentWidget(self.dashboard)
        self._check_retirement()

    def _check_retirement(self) -> None:
        player = self.dashboard.player
        if player is None or not career_sys.should_retire(player):
            return
        result = career_sys.retirement_evaluation(player, self.dashboard.career)
        QMessageBox.information(
            self, "退役评价", f"[{result.label}]\n{result.description}"
        )

    def _save(self) -> None:
        if self.dashboard.player is None:
            return
        save_load.save_game(
            self.dashboard.player,
            club=self.dashboard.club,
            matches=self.dashboard.matches,
            career=self.dashboard.career,
        )
        QMessageBox.information(self, "保存进度", "存档成功！")
