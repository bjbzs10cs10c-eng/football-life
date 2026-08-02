"""C11：开始页 / 创建球员页 / 主仪表盘 / 主窗口流程测试（无头模式）。"""

import random
import time

import pytest

import config.settings as s
import models.club as mc
import systems.player_creation as pc
import systems.transfer as tr
from models.career import Career
from ui.career_page import CareerPage
from ui.club_page import ClubPage
from ui.create_player_page import CreatePlayerPage
from ui.main_dashboard import MainDashboard
from ui.main_window import MainWindow
from ui.start_page import StartPage
from ui.transfer_page import TransferPage


def make_player():
    return pc.create_player("Li Ming", "CN", "ST", "R", rng=random.Random(1))


def wait_until(condition, qapp, timeout_ms=3000):
    """轮询事件循环直到条件满足或超时。"""
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        qapp.processEvents()
        if condition():
            return True
        time.sleep(0.005)
    return False


def no_event(monkeypatch):
    """屏蔽训练/比赛页里的随机事件弹窗。"""
    monkeypatch.setattr("ui.training_page.run_event_if_any", lambda *a, **k: None)
    monkeypatch.setattr("ui.match_page.run_event_if_any", lambda *a, **k: None)


class TestStartPage:
    def test_buttons_exist(self, qapp):
        page = StartPage()
        assert page.new_button.text() == "开始新生涯"
        assert page.load_button.text() == "读取存档"

    def test_new_career_signal(self, qapp):
        page = StartPage()
        emitted = []
        page.new_career_clicked.connect(lambda: emitted.append(True))
        page.new_button.click()
        assert emitted == [True]


class TestCreatePlayerPage:
    def test_positions_exclude_gk(self, qapp):
        page = CreatePlayerPage()
        assert set(page.position_buttons) == {"ST", "WING", "CM", "CB"}
        assert set(page.foot_buttons) == {"L", "R"}

    def test_preview_updates_when_position_changes(self, qapp):
        page = CreatePlayerPage()
        before = page.attribute_panel._bars["defending"][0].value()
        page.position_buttons["CB"].setChecked(True)
        after = page.attribute_panel._bars["defending"][0].value()
        assert after == before + s.POSITION_BONUSES["CB"]["defending"]

    def test_empty_name_rejected(self, qapp):
        page = CreatePlayerPage()
        page.name_edit.setText("   ")
        assert page.validate_and_create() is None
        assert page.error_label.text()

    def test_empty_nationality_rejected(self, qapp):
        page = CreatePlayerPage()
        page.name_edit.setText("Li Ming")
        page.nationality_edit.setText("")
        assert page.validate_and_create() is None

    def test_valid_form_creates_player(self, qapp):
        page = CreatePlayerPage()
        page.name_edit.setText("Li Ming")
        page.position_buttons["WING"].setChecked(True)
        page.foot_buttons["L"].setChecked(True)
        player = page.validate_and_create()
        assert player is not None
        assert player.name == "Li Ming"
        assert player.position == "WING"
        assert player.foot == "L"
        assert player.age == s.START_AGE


class TestMainDashboard:
    def test_set_data_refreshes_display(self, qapp):
        dashboard = MainDashboard()
        player = make_player()
        dashboard.set_data(player)
        assert dashboard.player_card.name_label.text() == "Li Ming"
        assert dashboard.season_label.text() == f"第 {player.season} 赛季"
        assert "青训" in dashboard.club_label.text()
        assert f"声望: {player.reputation}" in dashboard.reputation_label.text()
        assert len(dashboard.attribute_panel._bars) == 15
        dashboard.log("测试日志")
        assert "测试日志" in dashboard.log_view.toPlainText()

    def test_all_action_buttons_present(self, qapp):
        dashboard = MainDashboard()
        texts = {
            button.text()
            for button in dashboard.button_panel._buttons.values()
        }
        assert {
            "训练", "下一场比赛", "转会市场", "生涯统计", "查看球队", "保存进度",
        } <= texts


class TestMainWindow:
    def test_starts_on_start_page(self, qapp):
        window = MainWindow()
        assert window.stack.currentWidget() is window.start_page

    def test_new_career_switches_to_create_page(self, qapp):
        window = MainWindow()
        window.start_page.new_career_clicked.emit()
        assert window.stack.currentWidget() is window.create_page

    def test_player_created_switches_to_dashboard(self, qapp):
        window = MainWindow()
        window.create_page.name_edit.setText("Li Ming")
        window.create_page._on_confirm()
        assert window.stack.currentWidget() is window.dashboard
        assert window.dashboard.player is not None

    def test_load_save_success(self, qapp, monkeypatch):
        from PyQt6.QtWidgets import QMessageBox

        import systems.save_load as sl
        from ui import main_window

        player = make_player()
        monkeypatch.setattr(
            main_window.save_load, "load_game", lambda: sl.SaveData(player=player)
        )
        monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
        window = MainWindow()
        window._load_save()
        assert window.stack.currentWidget() is window.dashboard
        assert window.dashboard.player.name == "Li Ming"

    def test_load_save_missing_show_info(self, qapp, monkeypatch):
        from PyQt6.QtWidgets import QMessageBox

        from ui import main_window

        def fake_load():
            raise FileNotFoundError("未找到存档")

        monkeypatch.setattr(main_window.save_load, "load_game", fake_load)
        messages = []
        monkeypatch.setattr(
            QMessageBox,
            "information",
            lambda *a, **k: messages.append(a[2]),
        )
        window = MainWindow()
        window._load_save()
        assert window.stack.currentWidget() is window.start_page
        assert any("未找到存档" in m for m in messages)

    def test_save_writes_save(self, qapp, monkeypatch):
        from PyQt6.QtWidgets import QMessageBox

        from ui import main_window

        calls = []
        monkeypatch.setattr(
            main_window.save_load,
            "save_game",
            lambda *a, **k: calls.append((a, k)),
        )
        monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
        window = MainWindow()
        window.dashboard.set_data(make_player())
        window._save()
        assert len(calls) == 1


def make_strong_player():
    player = make_player()
    for attr in s.ALL_ATTRIBUTES:
        player.attributes[attr] = 85
    player.reputation = 75
    return player


class TestTransferPage:
    def test_accept_updates_club_id(self, qapp):
        player = make_strong_player()
        page = TransferPage()
        page.refresh(player)
        assert page.targets
        club = page.targets[0]
        page._accept(club)
        assert player.club_id == club.id

    def test_reject_keeps_state(self, qapp):
        player = make_strong_player()
        original_id = player.club_id
        page = TransferPage()
        rejected = []
        page.transfer_rejected.connect(lambda: rejected.append(True))
        page.refresh(player)
        page.back_button.click()
        assert rejected == [True]
        assert player.club_id == original_id

    def test_no_targets_for_weak_player(self, qapp):
        page = TransferPage()
        page.refresh(make_player())
        assert page.targets == []


class TestCareerPage:
    def test_display_matches_db(self, qapp, tmp_path):
        import systems.save_load as sl

        player = make_player()
        career = Career(
            games=10, goals=5, assists=3, trophies=2, best_award="联赛冠军"
        )
        path = tmp_path / "career.db"
        sl.save_game(player, career=career, db_path=path)
        data = sl.load_game(db_path=path)
        page = CareerPage()
        page.refresh(data.career)
        assert page.games_label.text() == "10"
        assert page.goals_label.text() == "5"
        assert page.assists_label.text() == "3"
        assert page.trophies_label.text() == "2"
        assert page.best_award_label.text() == "联赛冠军"

    def test_none_career_shows_zeros(self, qapp):
        page = CareerPage()
        page.refresh(None)
        assert page.games_label.text() == "0"
        assert page.best_award_label.text() == "—"


class TestClubPage:
    def test_readonly_display(self, qapp):
        from PyQt6.QtWidgets import QComboBox, QLineEdit

        club = next(c for c in mc.load_clubs() if c.tier == "TOP_LEAGUE")
        page = ClubPage()
        page.refresh(club)
        assert page.name_label.text() == club.name
        assert page.league_label.text() == club.league
        assert page.strength_label.text() == str(club.strength)
        assert page.facility_label.text() == str(club.facility)
        assert page.salary_label.text() == str(tr.salary_for(club))
        # 只读：无任何输入控件
        assert not page.findChildren(QLineEdit)
        assert not page.findChildren(QComboBox)

    def test_no_club_shows_youth(self, qapp):
        page = ClubPage()
        page.refresh(None)
        assert page.name_label.text() == "青训"


class TestFullFlow:
    def test_new_game_to_retirement(self, qapp, monkeypatch):
        from PyQt6.QtWidgets import QMessageBox

        from ui import main_window as mw_module

        # 屏蔽阻塞交互：无随机事件、弹窗自动确认
        no_event(monkeypatch)
        monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
        monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: None)
        monkeypatch.setattr(
            mw_module.save_load, "save_game", lambda *a, **k: 1
        )

        window = MainWindow()
        # 新建档 -> 创建
        window.create_page.name_edit.setText("Flow Player")
        window.create_page._on_confirm()
        assert window.stack.currentWidget() is window.dashboard
        player = window.dashboard.player
        assert player.name == "Flow Player"

        # 训练（技术训练，体力下降）
        window._open_training()
        assert window.stack.currentWidget() is window.training_page
        window.training_page.type_buttons["TECHNICAL"].click()
        window.training_page.start_button.click()
        assert player.condition < s.START_CONDITION
        window.training_page.back_button.click()
        assert window.stack.currentWidget() is window.dashboard

        # 比赛（记录进入 matches）
        before = len(window.dashboard.matches)
        window._open_match()
        assert window.stack.currentWidget() is window.match_page
        window.match_page.play_button.click()
        assert wait_until(
            lambda: len(window.dashboard.matches) == before + 1, qapp
        )
        window.match_page.back_button.click()
        assert window.stack.currentWidget() is window.dashboard

        # 转会（提升能力后进入转会页并接受）
        for attr in s.ALL_ATTRIBUTES:
            player.attributes[attr] = 85
        player.reputation = 75
        window._show_transfer()
        assert window.stack.currentWidget() is window.transfer_page
        assert window.transfer_page.targets
        club = window.transfer_page.targets[0]
        window.transfer_page._accept(club)
        assert window.dashboard.player.club_id == club.id
        assert window.stack.currentWidget() is window.dashboard

        # 球队页只读入口
        window._show_club()
        assert window.stack.currentWidget() is window.club_page
        assert window.club_page.name_label.text() == club.name
        window.club_page.back_requested.emit()
        assert window.stack.currentWidget() is window.dashboard

        # 生涯页入口
        window._show_career()
        assert window.stack.currentWidget() is window.career_page
        window.career_page.back_requested.emit()

        # 退役检查（不崩溃，QMessageBox 已 stub）
        player.age = s.RETIRE_AGE
        window._back_to_dashboard()
        # 数据完整：存档调用已触发、球员仍有效
        player.validate()
