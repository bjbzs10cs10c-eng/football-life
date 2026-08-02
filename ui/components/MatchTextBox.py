"""比赛文字直播组件（UIDesign §12 MatchTextBox / §8）。

逐条追加比赛事件（如“第35分钟 ... GOAL!”），带播放锁防止重复播放。
"""

from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import QTextEdit


class MatchTextBox(QTextEdit):
    playback_finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self._timer: QTimer | None = None
        self._queue: list = []

    def play_events(self, events: list, interval_ms: int = 500) -> None:
        """按间隔逐条显示事件；已在播放时先停止再重播。"""
        self.stop_playback()
        self._queue = list(events)
        if not self._queue:
            self.playback_finished.emit()
            return
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._show_next)
        self._timer.start()

    def append_all(self, events: list) -> None:
        """立即全部追加（测试与无动画场景用）。"""
        self.stop_playback()
        for event in events:
            self.append(event)

    def is_playing(self) -> bool:
        return self._timer is not None

    def stop_playback(self) -> None:
        if self._timer is not None:
            self._timer.stop()
            self._timer.deleteLater()
            self._timer = None
        self._queue = []

    def _show_next(self) -> None:
        if self._queue:
            self.append(self._queue.pop(0))
        if not self._queue:
            self.stop_playback()
            self.playback_finished.emit()
