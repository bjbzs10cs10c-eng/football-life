"""球员卡组件（UIDesign §6.2 / §12）。"""

from PyQt6.QtWidgets import QFrame, QGridLayout, QLabel

from models.player import Player


def condition_status(condition: int) -> str:
    """体力区间 -> 状态文案（UI 展示用）。"""
    if condition >= 90:
        return "状态极佳"
    if condition >= 70:
        return "状态良好"
    if condition >= 50:
        return "状态一般"
    if condition >= 30:
        return "状态疲惫"
    return "状态糟糕"


class PlayerCard(QFrame):
    """球员信息卡：姓名/年龄/位置/Overall/状态。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("role", "card")
        layout = QGridLayout(self)

        self.name_label = self._make_label("", "data")
        self.detail_label = self._make_label("", "dim")
        self.overall_label = self._make_label("--", "title")
        self.status_label = self._make_label("", "data")

        layout.addWidget(QLabel("综合能力"), 0, 0)
        layout.addWidget(self.overall_label, 0, 1)
        layout.addWidget(self.name_label, 1, 0, 1, 2)
        layout.addWidget(self.detail_label, 2, 0, 1, 2)
        layout.addWidget(self.status_label, 3, 0, 1, 2)

    @staticmethod
    def _make_label(text: str, role: str) -> QLabel:
        label = QLabel(text)
        label.setProperty("role", role)
        return label

    def refresh(self, player: Player) -> None:
        """用球员数据刷新卡片显示。"""
        self.name_label.setText(player.name)
        self.detail_label.setText(
            f"年龄 {player.age}  |  位置 {player.position}  |  体力 {player.condition}"
        )
        self.overall_label.setText(str(player.overall()))
        self.status_label.setText(condition_status(player.condition))
