"""《Football Life：我的足球生涯》程序入口。

启动前校验配置与资源文件（data/*.json），缺失时给出友好提示；
通过后启动 PyQt6 主窗口。
"""

import sys

import config.settings as settings


def main() -> int:
    settings.validate_config()

    from PyQt6.QtWidgets import QApplication, QMessageBox

    # 启动前预加载资源：缺失/损坏时友好提示而非崩溃
    try:
        import models.club as club_model
        import models.event as event_model

        club_model.load_clubs()
        event_model.load_events()
    except Exception as exc:  # noqa: BLE001 - 统一转为友好提示
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(
            None,
            "资源文件错误",
            f"游戏资源加载失败：{exc}\n请检查 data/ 目录下的 clubs.json、events.json 是否完整。",
        )
        return 1

    app = QApplication.instance() or QApplication(sys.argv)
    from ui.main_window import MainWindow

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
