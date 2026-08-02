# 将项目根目录加入 pytest 的 sys.path，使测试可直接 import config 等顶层包。

import os

# GUI 测试使用无头模式，必须在创建 QApplication 之前设置
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest


@pytest.fixture(scope="session")
def qapp():
    """提供全局唯一的 QApplication（无头模式）。"""
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app
