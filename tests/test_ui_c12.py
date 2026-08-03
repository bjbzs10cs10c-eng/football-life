"""C12：训练页 / 比赛页 / 事件弹窗测试（无头模式）。"""

import random
import time

import pytest
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QDialog, QMessageBox

import config.settings as s
import models.club as mc
import models.event as me
import systems.player_creation as pc
import systems.save_load as sl
from ui.components.EventDialog import EventDialog, effect_to_text
from ui.components.MatchTextBox import MatchTextBox
from ui.main_window import MainWindow
from ui.match_page import MatchPage
from ui.training_page import TrainingPage


def make_player():
    player = pc.create_player("Li Ming", "CN", "ST", "R", rng=random.Random(1))
    for attr in s.ALL_ATTRIBUTES:
        player.attributes[attr] = 70
    player.attributes["shooting"] = 80
    return player


def make_club():
    return next(c for c in mc.load_clubs() if c.tier == "TOP_LEAGUE")


def wait_until(condition, qapp, timeout_ms=3000):
    """轮询事件循环直到条件满足或超时。"""
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        qapp.processEvents()
        if condition():
            return True
        time.sleep(0.005)
    return False


def no_message_box(monkeypatch):
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)


def no_event(monkeypatch):
    monkeypatch.setattr("ui.training_page.run_event_if_any", lambda *a, **k: None)
    monkeypatch.setattr("ui.match_page.run_event_if_any", lambda *a, **k: None)


class FakeRng:
    """按顺序返回预设 randint 结果，保证训练成长确定性。"""

    def __init__(self, values):
        self.values = list(values)

    def randint(self, low, high):
        assert self.values, "FakeRng 的随机值已耗尽"
        return self.values.pop(0)


class TestMatchTextBox:
    def test_append_all(self, qapp):
        box = MatchTextBox()
        box.append_all(["第10分钟 获得机会", "进球！"])
        text = box.toPlainText()
        assert "第10分钟" in text and "进球！" in text
        assert not box.is_playing()

    def test_play_events_streamby_stream(self, qapp):
        box = MatchTextBox()
        finished = []
        box.playback_finished.connect(lambda: finished.append(True))
        box.play_events(["事件1", "事件2"], interval_ms=1)
        assert box.is_playing()
        assert wait_until(lambda: bool(finished), qapp)
        text = box.toPlainText()
        assert "事件1" in text and "事件2" in text
        assert not box.is_playing()

    def test_stop_playback_clears(self, qapp):
        box = MatchTextBox()
        box.play_events(["a", "b", "c"], interval_ms=1000)
        box.stop_playback()
        assert not box.is_playing()
        assert box.toPlainText() == ""


class TestEventDialog:
    def test_choice_a_and_effect_text(self, qapp):
        event = me.load_events()[0]  # 训练：加练射门 shooting+3;condition-20
        assert effect_to_text(event.effect_a) == "射门+3，体力-20"

    def test_exec_choice_b(self, qapp):
        event = me.load_events()[0]
        dialog = EventDialog(event)
        QTimer.singleShot(0, dialog.button_b.click)
        assert dialog.exec() == QDialog.DialogCode.Accepted
        assert dialog.selected_choice == "B"

    def test_choice_effect_applies(self, qapp):
        player = make_player()
        event = me.load_events()[-1]  # career 代言：A money+5000
        from systems.event_manager import handle_event

        changes = handle_event(player, event, "A")
        assert changes["money"] == 5000
        assert player.money == s.START_MONEY + 5000


class TestTrainingPage:
    def test_training_refreshes_player_and_page(self, qapp, monkeypatch):
        no_message_box(monkeypatch)
        no_event(monkeypatch)
        # 固定随机：体能训练不受伤，且三项基础收益均为 3（保证成长）
        monkeypatch.setattr(
            "systems.training._random", FakeRng([95, 3, 3, 3])
        )
        player = make_player()
        club = make_club()
        page = TrainingPage()
        page.set_data(player, club)
        changed = []
        page.data_changed.connect(lambda: changed.append(True))

        old_pace = player.attributes["pace"]
        old_condition = player.condition
        old_date = player.current_date
        page.type_buttons["PHYSICAL"].setChecked(True)
        page._select("PHYSICAL")
        page._on_start()

        assert player.attributes["pace"] > old_pace
        assert player.condition < old_condition
        assert player.current_date != old_date
        assert changed == [True]
        assert "体力" in page.status_label.text()
        player.validate()

    def test_rest_restores_condition(self, qapp, monkeypatch):
        no_message_box(monkeypatch)
        no_event(monkeypatch)
        player = make_player()
        player.condition = 30
        page = TrainingPage()
        page.set_data(player, make_club())
        page._select("REST")
        page._on_start()
        assert player.condition == 30 + s.REST_CONDITION_RESTORE

    def test_insufficient_condition_blocked(self, qapp, monkeypatch):
        messages = []
        monkeypatch.setattr(
            QMessageBox, "information", lambda *a, **k: messages.append(a[2])
        )
        no_event(monkeypatch)
        player = make_player()
        player.condition = 5
        date = player.current_date
        page = TrainingPage()
        page.set_data(player, make_club())
        page._on_start()
        assert any("体力不足" in m for m in messages)
        assert player.current_date == date

    def test_rapid_clicks_no_crash(self, qapp, monkeypatch):
        no_message_box(monkeypatch)
        no_event(monkeypatch)
        player = make_player()
        page = TrainingPage()
        page.set_data(player, make_club())
        for _ in range(5):
            page._on_start()
        player.validate()  # 无崩溃
        assert player.condition == s.START_CONDITION - 5 * s.TRAINING_TYPES["TECHNICAL"]["condition_cost"]


class TestMatchPage:
    def test_match_updates_score_events_rating(self, qapp, monkeypatch):
        no_event(monkeypatch)
        player = make_player()
        club = make_club()
        matches = []
        page = MatchPage()
        page.set_data(player, club, matches)
        finished = []
        page.match_text.playback_finished.connect(lambda: finished.append(True))
        page._on_play()

        assert len(matches) == 1
        record = matches[0]
        assert "比分" in page.score_label.text()
        assert record.result in page.score_label.text()
        assert f"评分: {record.rating:.1f}" in page.rating_label.text()
        assert "奖金" in page.settle_label.text()
        assert wait_until(lambda: bool(finished), qapp)
        assert "获得机会" in page.match_text.toPlainText()
        # 赛后：日期推进、比赛记录可存档
        assert record.player_id is None or record.player_id == player.id
        player.validate()

    def test_double_click_no_duplicate_match(self, qapp, monkeypatch):
        no_event(monkeypatch)
        player = make_player()
        matches = []
        page = MatchPage()
        page.set_data(player, make_club(), matches)
        finished = []
        page.match_text.playback_finished.connect(lambda: finished.append(True))
        page._on_play()
        page._on_play()  # 播放期间连点：应被忽略
        assert len(matches) == 1
        assert wait_until(lambda: bool(finished), qapp)
        page._on_play()  # 播放结束后可再赛
        assert len(matches) == 2


class TestThreeWaySync:
    def test_ui_model_db_sync(self, qapp, monkeypatch, tmp_path):
        """训练 + 比赛 + 事件 -> 界面刷新 -> 存档 -> 读档一致。"""
        no_message_box(monkeypatch)
        no_event(monkeypatch)
        from systems.event_manager import handle_event
        import systems.career as career_sys

        player = make_player()
        club = make_club()
        matches = []

        # 界面层：训练一次
        page = TrainingPage()
        page.set_data(player, club)
        page._on_start()
        # 训练后推进 6 天到下一个比赛日（一周一赛），再比赛
        career_sys.advance_days(player, 6, club=club)
        # 界面层：比赛一次
        match_page = MatchPage()
        match_page.set_data(player, club, matches)
        match_page._on_play()
        # 事件效果直接应用（模拟弹窗选择 B）
        event = next(e for e in me.load_events() if e.type == "career")
        handle_event(player, event, "B")

        # 模型层：主仪表盘刷新后显示一致
        dashboard = MainWindow().dashboard
        dashboard.set_data(player, club, matches)
        assert dashboard.player.money == player.money
        assert dashboard.matches == matches

        # 数据库层：存档读档往返
        db_path = tmp_path / "sync.db"
        sl.save_game(player, club=club, matches=matches, db_path=db_path)
        data = sl.load_game(db_path=db_path)
        assert data.player.attributes == player.attributes
        assert data.player.money == player.money
        assert data.player.reputation == player.reputation
        assert data.player.condition == player.condition
        assert len(data.matches) == 1
        assert data.matches[0].result == matches[0].result
        assert data.matches[0].rating == matches[0].rating


class TestMainWindowIntegration:
    def test_open_training_and_match_pages(self, qapp):
        window = MainWindow()
        window.dashboard.set_data(make_player(), make_club(), [])
        window.dashboard.button_panel.training_requested.emit()
        assert window.stack.currentWidget() is window.training_page
        window.dashboard.button_panel.match_requested.emit()
        assert window.stack.currentWidget() is window.match_page

    def test_back_returns_to_dashboard(self, qapp):
        window = MainWindow()
        window.dashboard.set_data(make_player())
        window._open_training()
        window.training_page.finished.emit()
        assert window.stack.currentWidget() is window.dashboard
