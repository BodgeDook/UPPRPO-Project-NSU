# styles.py

def apply_button_style(widget):
    widget.setStyleSheet("""
        QPushButton {
            background-color: #4A90E2;
            color: white;
            border-radius: 10px;
            padding: 10px;
            font-size: 16px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #357ABD;
        }
        QPushButton:pressed {
            background-color: #2A6099;
        }
    """)

def apply_disabled_button_style(widget):
    widget.setStyleSheet("""
        QPushButton {
            background-color: #A0A0A0;
            color: white;
            border-radius: 10px;
            padding: 10px;
            font-size: 16px;
            font-weight: bold;
        }
    """)

def apply_label_style(widget):
    widget.setStyleSheet("""
        QLabel {
            font-size: 18px;
            color: #333333;
        }
    """)

def apply_title_style(widget):
    widget.setStyleSheet("""
        QLabel {
            font-size: 36px;
            font-weight: bold;
            color: #333333;
        }
    """)

def apply_link_style(widget):
    widget.setStyleSheet("""
        QPushButton {
            font-size: 14px;
            color: #4A90E2;
            background: none;
            border: none;
            text-decoration: underline;
        }
        QPushButton:hover {
            color: #357ABD;
        }
    """)

def apply_window_style(widget):
    widget.setStyleSheet("""
        QWidget {
            background-color: #ADD8E6;
        }
    """)