"""训练页（UIDesign §7）。

四类训练（技术/体能/战术/休息），训练后立即刷新属性与体力、
弹出结果、推进 1 天并检查训练事件。带忙碌锁防止连点重复执行。
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import config.settings as settings
import systems.career as career
import systems.training as training
from models.club import Club
from models.player import Player
from ui.event_flow import format_event_log, run_event_if_any


def _training_description(training_type: str) -> str:
    cfg = settings.TRAINING_TYPES[training_type]
    if training_type == "REST":
        return f"恢复体力 +{settings.REST_CONDITION_RESTORE}"
    attrs = "、".join(
        settings.ATTRIBUTE_NAMES_ZH[a] for a in cfg["attributes"]
    )
    text = f"提升: {attrs}  |  消耗体力: {cfg['condition_cost']}"
    if cfg["injury_chance_percent"] > 0:
        text += f"  |  受伤概率: {cfg['injury_chance_percent']}%"
    return text


class TrainingPage(QWidget):
    data_changed = pyqtSignal()
    log_message = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.player: Player | None = None
        self.club: Club | None = None
        self._busy = False

        layout = QVBoxLayout(self)
        title = QLabel("训练")
        title.setProperty("role", "section")
        self.status_label = QLabel("")
        self.status_label.setProperty("role", "data")
        layout.addWidget(title)
        layout.addWidget(self.status_label)

        self.type_buttons = {}
        for training_type in settings.TRAINING_TYPES:
            button = QPushButton(
                f"{settings.TRAINING_TYPES[training_type]['name_zh']}\n"
                f"{_training_description(training_type)}"
            )
            button.setCheckable(True)
            button.setFixedHeight(80)
            button.clicked.connect(lambda _, t=training_type: self._select(t))
            layout.addWidget(button)
            self.type_buttons[training_type] = button
        self.type_buttons["TECHNICAL"].setChecked(True)
        self._selected_type = "TECHNICAL"

        row = QHBoxLayout()
        self.start_button = QPushButton("开始训练")
        self.start_button.setFixedSize(180, 50)
        self.start_button.clicked.connect(self._on_start)
        self.back_button = QPushButton("返回")
        self.back_button.setFixedSize(120, 50)
        self.back_button.clicked.connect(self.finished.emit)
        row.addStretch(1)
        row.addWidget(self.start_button)
        row.addWidget(self.back_button)
        row.addStretch(1)
        layout.addLayout(row)
        layout.addStretch(1)

    def set_data(self, player: Player, club: Club | None) -> None:
        self.player = player
        self.club = club
        self.refresh()

    def refresh(self) -> None:
        if self.player is None:
            return
        is_match_day = career.days_until_next_match(self.player) == 0
        self.start_button.setEnabled(not is_match_day)
        self.status_label.setText(
            f"{self.player.name}  |  日期 {self.player.current_date}"
            f"  |  体力 {self.player.condition}  |  金钱 {self.player.money}"
            + (
                "  |  今天是比赛日，请先完成比赛！"
                if is_match_day
                else ""
            )
        )

    def _select(self, training_type: str) -> None:
        self._selected_type = training_type
        for key, button in self.type_buttons.items():
            button.setChecked(key == training_type)

    def _on_start(self) -> None:
        if self._busy or self.player is None:
            return
        if career.days_until_next_match(self.player) == 0:
            QMessageBox.information(self, "训练", "今天是比赛日，请先完成比赛。")
            return
        self._busy = True
        self.start_button.setEnabled(False)
        try:
            result = training.train(self.player, self._selected_type)
            if not result.success:
                QMessageBox.information(self, "训练", "体力不足，请先休息。")
                return
            day_logs = career.advance_days(self.player, 1, club=self.club)
            for log in day_logs:
                self.log_message.emit(log)
            self._show_result(result)
            event_result = run_event_if_any(self.player, "training", self)
            if event_result is not None:
                self.log_message.emit(f"事件: {format_event_log(event_result)}")
            self.refresh()
            self.data_changed.emit()
        finally:
            self._busy = False
            self.start_button.setEnabled(True)

    def _show_result(self, result: training.TrainingResult) -> None:
        gains = "、".join(
            f"{settings.ATTRIBUTE_NAMES_ZH[k]}+{v}" for k, v in result.gains.items()
        ) or "无属性提升"
        text = f"训练完成！\n{gains}\n体力{result.condition_change:+d}"
        if result.injured:
            text += "\n⚠ 训练中受伤，体力额外-25"
        QMessageBox.information(self, "训练结果", text)
