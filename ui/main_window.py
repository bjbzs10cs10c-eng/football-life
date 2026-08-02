"""主窗口（C11）：开始页 / 创建球员页 / 主仪表盘 三页切换。"""

from PyQt6.QtWidgets import QMainWindow, QMessageBox, QStackedWidget

import config.settings as settings
import systems.save_load as save_load
from models.player import Player
from ui.create_player_page import CreatePlayerPage
from ui.main_dashboard import MainDashboard
from ui.start_page import StartPage
from ui.theme import apply_theme


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(settings.GAME_TITLE)
        self.resize(settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT)
        apply_theme(self)

        self.start_page = StartPage()
        self.create_page = CreatePlayerPage()
        self.dashboard = MainDashboard()

        self.stack = QStackedWidget()
        self.stack.addWidget(self.start_page)
        self.stack.addWidget(self.create_page)
        self.stack.addWidget(self.dashboard)
        self.setCentralWidget(self.stack)

        self.start_page.new_career_clicked.connect(
            lambda: self.stack.setCurrentWidget(self.create_page)
        )
        self.start_page.load_save_clicked.connect(self._load_save)
        self.create_page.player_created.connect(self._on_player_created)
        self.dashboard.button_panel.save_requested.connect(self._save)
        self.dashboard.button_panel.training_requested.connect(
            lambda: self._placeholder("训练功能将在后续阶段开放")
        )
        self.dashboard.button_panel.match_requested.connect(
            lambda: self._placeholder("比赛功能将在后续阶段开放")
        )
        self.dashboard.button_panel.transfer_requested.connect(
            lambda: self._placeholder("转会功能将在后续阶段开放")
        )
        self.dashboard.button_panel.career_requested.connect(
            lambda: self._placeholder("生涯统计将在后续阶段开放")
        )

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

    def _placeholder(self, message: str) -> None:
        QMessageBox.information(self, "提示", message)
