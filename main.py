"""《Football Life：我的足球生涯》程序入口。

校验配置后启动 PyQt6 主窗口（开始页 / 创建球员页 / 主仪表盘）。
"""

import sys

import config.settings as settings


def main() -> int:
    settings.validate_config()

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    from ui.main_window import MainWindow

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
