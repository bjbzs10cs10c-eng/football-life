"""C11：开始页 / 创建球员页 / 主仪表盘 / 主窗口流程测试（无头模式）。"""

import random

import pytest

import config.settings as s
import systems.player_creation as pc
from ui.create_player_page import CreatePlayerPage
from ui.main_dashboard import MainDashboard
from ui.main_window import MainWindow
from ui.start_page import StartPage


def make_player():
    return pc.create_player("Li Ming", "CN", "ST", "R", rng=random.Random(1))


class TestStartPage:
    def test_buttons_exist(self, qapp):
        page = StartPage()
        assert page.new_button.text() == "开始新生涯"
        assert page.load_button.text() == "读取存档"
        assert page.settings_button.text() == "设置"
        assert not page.settings_button.isEnabled()  # MVP 无设置页

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
        assert {"训练", "下一场比赛", "转会市场", "生涯统计", "保存进度"} <= texts


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
