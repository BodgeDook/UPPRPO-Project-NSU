# ui/welcome_window.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QFileDialog
from PyQt5.QtCore import Qt

from styles import apply_button_style, apply_welcome_window_style, apply_label_style, apply_title_style, theme_manager
from video_editor import VideoEditor
from settings_window import SettingsWindow

class WelcomeWindowSigned(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        theme_manager.theme_changed.connect(self.update_theme)

    def initUI(self):
        self.setWindowTitle('uMovie - Welcome')
        self.setGeometry(300, 300, 800, 600)
        apply_welcome_window_style(self)
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        title_label = QLabel("uMovie")
        apply_title_style(title_label)
        main_layout.addWidget(title_label, alignment=Qt.AlignCenter)
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(20)
        new_project_btn = QPushButton("New Project")
        apply_button_style(new_project_btn)
        new_project_btn.clicked.connect(self.open_new_project)
        buttons_layout.addWidget(new_project_btn)
        open_project_btn = QPushButton("Open Project")
        apply_button_style(open_project_btn)
        open_project_btn.clicked.connect(self.open_project)
        buttons_layout.addWidget(open_project_btn)
        account_management_btn = QPushButton("Account Management")
        apply_button_style(account_management_btn)
        account_management_btn.clicked.connect(self.open_account_management)
        buttons_layout.addWidget(account_management_btn)
        main_layout.addLayout(buttons_layout)
        recent_label = QLabel("Recent")
        apply_label_style(recent_label)
        main_layout.addWidget(recent_label, alignment=Qt.AlignRight)
        recent_table = QTableWidget(4, 3)
        recent_table.setHorizontalHeaderLabels(["Project", "Time", "Date"])
        recent_table.setFixedSize(300, 150)
        recent_table.setEditTriggers(QTableWidget.NoEditTriggers)
        recent_data = [("project 4", "12:34", "Yesterday"), ("project 3", "23:32", "Monday"),
                      ("project 2", "02:02", "16.03"), ("project 1", "13:57", "16.12.2024")]
        for row, (project, time, date) in enumerate(recent_data):
            recent_table.setItem(row, 0, QTableWidgetItem(project))
            recent_table.setItem(row, 1, QTableWidgetItem(time))
            recent_table.setItem(row, 2, QTableWidgetItem(date))
        recent_table.resizeColumnsToContents()
        main_layout.addWidget(recent_table, alignment=Qt.AlignRight)
        self.setLayout(main_layout)

    def open_new_project(self):
        self.editor = VideoEditor()
        self.editor.show()
        self.close()

    def open_project(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if folder_path:
            print(f"Selected folder: {folder_path}")

    def open_account_management(self):
        self.settings_window = SettingsWindow(initial_section="account")
        self.settings_window.show()

    def update_theme(self, theme):
        apply_welcome_window_style(self)
        for widget in self.findChildren(QPushButton):
            apply_button_style(widget)
        for widget in self.findChildren(QLabel):
            if widget.text() == "uMovie":
                apply_title_style(widget)
            else:
                apply_label_style(widget)
        self.update()