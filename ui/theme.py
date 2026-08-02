"""UI 主题（C11）。

按 UIDesign §2 的色彩与字体规范：
- 足球绿背景、深黑灰卡片、金色高亮、红色风险；
- 中文字体 Microsoft YaHei，标题 28px / 模块标题 20px / 普通 14px / 数据 16px。
"""

COLORS = {
    "background": "#14532D",      # 足球绿（深）
    "card": "#22262B",            # 深黑灰卡片
    "card_border": "#3A4149",
    "gold": "#D4AF37",            # 金色（荣誉/高评分）
    "danger": "#C0392B",          # 红色（伤病/风险）
    "text": "#ECF0F1",
    "text_dim": "#9AA5B1",
    "green": "#27AE60",
}


def build_stylesheet() -> str:
    c = COLORS
    return f"""
    QWidget {{
        font-family: "Microsoft YaHei";
        font-size: 14px;
        color: {c['text']};
        background-color: {c['background']};
    }}
    QMainWindow, QStackedWidget {{
        background-color: {c['background']};
    }}
    QLabel {{
        color: {c['text']};
    }}
    QLabel[role="title"] {{
        font-size: 28px;
        font-weight: bold;
        color: {c['gold']};
    }}
    QLabel[role="subtitle"] {{
        font-size: 20px;
    }}
    QLabel[role="section"] {{
        font-size: 20px;
        font-weight: bold;
        color: {c['gold']};
    }}
    QLabel[role="data"] {{
        font-size: 16px;
        font-weight: bold;
    }}
    QLabel[role="dim"] {{
        color: {c['text_dim']};
    }}
    QLabel[role="danger"] {{
        color: {c['danger']};
    }}
    QFrame[role="card"] {{
        background-color: {c['card']};
        border: 1px solid {c['card_border']};
        border-radius: 8px;
    }}
    QPushButton {{
        background-color: {c['green']};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 16px;
    }}
    QPushButton:hover {{
        background-color: #2E9F5F;
    }}
    QPushButton:disabled {{
        background-color: #5A6B5F;
        color: #B8C4B8;
    }}
    QLineEdit, QComboBox, QDoubleSpinBox {{
        background-color: {c['card']};
        border: 1px solid {c['card_border']};
        border-radius: 4px;
        padding: 4px 8px;
        color: {c['text']};
    }}
    QProgressBar {{
        background-color: {c['card_border']};
        border: none;
        border-radius: 3px;
        height: 12px;
        text-align: center;
        color: {c['text']};
    }}
    QProgressBar::chunk {{
        background-color: {c['green']};
        border-radius: 3px;
    }}
    QTextEdit {{
        background-color: {c['card']};
        border: 1px solid {c['card_border']};
        border-radius: 6px;
        color: {c['text']};
    }}
    QRadioButton {{
        color: {c['text']};
        spacing: 6px;
    }}
    """


def apply_theme(widget) -> None:
    """给窗口/应用应用统一样式表。"""
    widget.setStyleSheet(build_stylesheet())
