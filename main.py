"""《Football Life：我的足球生涯》程序入口（A1 占位版）。

当前仅校验配置并打开一个占位窗口，用于验证工程骨架与 PyQt6 环境可用。
后续阶段（C11）将替换为真实的页面与流程。
"""

import sys

import config.settings as settings


def main() -> int:
    settings.validate_config()

    from PyQt6.QtCore import QTimer
    from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow

    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle(settings.GAME_TITLE)
    window.resize(settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT)
    window.setCentralWidget(QLabel("Football Life 工程骨架已就绪", window))
    # 占位版：1.5 秒后自动退出，便于自动化冒烟验证
    QTimer.singleShot(1500, app.quit)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
