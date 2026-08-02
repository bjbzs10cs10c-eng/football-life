"""创建球员页（UIDesign §5 / PRD §4）。

左侧：姓名/国籍/年龄/身高/位置/惯用脚；右侧：初始能力与 Overall 预览。
MVP 不支持 GK，位置为 ST/WING/CM/CB 四项。
"""

import random

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

import config.settings as settings
import systems.player_creation as creation
from models.player import Player
from ui.components.attribute_panel import AttributePanel


class CreatePlayerPage(QWidget):
    player_created = pyqtSignal(Player)

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QHBoxLayout(self)

        # ---- 左侧：人物信息 ----
        form = QWidget()
        form_layout = QFormLayout(form)
        form_layout.setSpacing(12)

        title = QLabel("创建球员")
        title.setProperty("role", "section")
        form_layout.addRow(title)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入姓名")
        form_layout.addRow("姓名：", self.name_edit)

        self.nationality_edit = QLineEdit("中国")
        form_layout.addRow("国籍：", self.nationality_edit)

        age_label = QLabel(f"{settings.START_AGE}（固定）")
        age_label.setProperty("role", "data")
        form_layout.addRow("年龄：", age_label)

        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(1.50, 2.20)
        self.height_spin.setSingleStep(0.01)
        self.height_spin.setDecimals(2)
        self.height_spin.setValue(1.78)
        form_layout.addRow("身高(m)：", self.height_spin)

        self.position_group = QButtonGroup(self)
        position_box = QWidget()
        position_layout = QHBoxLayout(position_box)
        position_layout.setContentsMargins(0, 0, 0, 0)
        self.position_buttons = {}
        for code in settings.POSITION_CODES:
            button = QRadioButton(settings.POSITION_NAMES_ZH[code])
            self.position_group.addButton(button)
            position_layout.addWidget(button)
            self.position_buttons[code] = button
        self.position_buttons["ST"].setChecked(True)
        self.position_group.buttonToggled.connect(
            lambda *_: self._rebuild_preview()
        )
        form_layout.addRow("位置：", position_box)

        self.foot_group = QButtonGroup(self)
        foot_box = QWidget()
        foot_layout = QHBoxLayout(foot_box)
        foot_layout.setContentsMargins(0, 0, 0, 0)
        self.foot_buttons = {}
        for foot in settings.FOOT_OPTIONS:
            button = QRadioButton(settings.FOOT_NAMES_ZH[foot])
            self.foot_group.addButton(button)
            foot_layout.addWidget(button)
            self.foot_buttons[foot] = button
        self.foot_buttons["R"].setChecked(True)
        form_layout.addRow("惯用脚：", foot_box)

        self.confirm_button = QPushButton("确认创建")
        self.confirm_button.setFixedSize(180, 50)
        self.confirm_button.clicked.connect(self._on_confirm)
        form_layout.addRow(self.confirm_button)
        form_layout.addRow(self._error_label())

        # ---- 右侧：能力预览 ----
        preview = QWidget()
        preview_layout = QVBoxLayout(preview)
        preview_title = QLabel("初始能力预览")
        preview_title.setProperty("role", "section")
        self.overall_label = QLabel("Overall: --")
        self.overall_label.setProperty("role", "title")
        preview_layout.addWidget(preview_title)
        preview_layout.addWidget(self.overall_label)
        self.attribute_panel = AttributePanel()
        preview_layout.addWidget(self.attribute_panel, 1)

        root.addWidget(form, 1)
        root.addWidget(preview, 1)
        self._rebuild_preview()

    def _error_label(self) -> QLabel:
        self.error_label = QLabel("")
        self.error_label.setProperty("role", "danger")
        return self.error_label

    def selected_position(self) -> str:
        for code, button in self.position_buttons.items():
            if button.isChecked():
                return code
        return settings.POSITION_CODES[0]

    def selected_foot(self) -> str:
        for foot, button in self.foot_buttons.items():
            if button.isChecked():
                return foot
        return settings.FOOT_OPTIONS[0]

    def _rebuild_preview(self) -> None:
        """用固定种子生成预览属性，保证切换位置时预览稳定。"""
        preview = creation.create_player(
            "预览", "中国", self.selected_position(), self.selected_foot(),
            rng=random.Random(2026),
        )
        self.attribute_panel.refresh(preview)
        self.overall_label.setText(f"Overall: {preview.overall()}")

    def validate_and_create(self) -> Player | None:
        """校验表单并创建球员；不合法返回 None。"""
        name = self.name_edit.text().strip()
        nationality = self.nationality_edit.text().strip()
        if not name:
            self.error_label.setText("姓名不能为空")
            return None
        if not nationality:
            self.error_label.setText("国籍不能为空")
            return None
        self.error_label.setText("")
        return creation.create_player(
            name,
            nationality,
            self.selected_position(),
            self.selected_foot(),
            height=round(self.height_spin.value(), 2),
        )

    def _on_confirm(self) -> None:
        player = self.validate_and_create()
        if player is not None:
            self.player_created.emit(player)
