import sys
import os
import json

from PyQt5.QtCore import Qt, QObject, pyqtSignal, QThread, QTimer, QTimer, QSize, QUrl
from PyQt5.QtGui import QKeySequence, QIcon
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QToolBar, QAction, QProgressBar, QLabel, QSlider, QComboBox,
                             QGraphicsView, QGraphicsScene, QSplitter, QCheckBox, QStyle,
                             QUndoStack, QGroupBox, QPushButton, QSpinBox, QFileDialog, QTableWidget,
                             QTableWidgetItem, QStackedWidget)
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtGui import QDesktopServices

# importing styles:
from styles import (apply_button_style, apply_disabled_button_style, apply_label_style,
                    apply_title_style, apply_link_style, apply_window_style)
from auth_window import AuthView  # for Login/Register


if os.getenv("DEVELOP_MACHINE"):
    SETTINGS_PATH = "/Users/danielgehrman/Documents/Programming/Projects/Video editor/config/settings.json"
else:
    SETTINGS_PATH = "/need/to/set/settings/path"


class HelloModel(QObject):
    def __init__(self):
        self.settings_path = SETTINGS_PATH
        self.settings = self.load_settings()

    def load_settings(self):
        with open(self.settings_path, 'r') as file:
            settings = json.load(file)
        return settings

    def get_is_signed_in(self):
        signed_bool = self.settings.get('is_signed_in', False)
        print("Is user signed in? Ans:", signed_bool)
        return signed_bool

class HelloViewModel(QObject):
    state_changed = pyqtSignal(bool)    # Signal to indicate a change in state — (un)signed or not

    UNSIGNED = 0
    SIGNED = 1


    def __init__(self, model):
        super().__init__()
        self.model = model
        # self.current_state = self.UNSIGNED  # Default to unsigned
        self.current_state = self.model.get_is_signed_in()
        self.worker = None
    
    def switch_to_signed(self):
        self.current_state = self.SIGNED
        self.state_changed.emit()

    def switch_to_unsigned(self):
        self.current_state = self.UNSIGNED
        self.state_changed.emit()
    
    def open_new_project(self):
        print("openning new project")
        return
        self.editor = VideoEditor()
        self.editor.show()
        self.close()

    def open_project(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if folder_path:
            print(f"Selected folder: {folder_path}")

# might be needed
# class WindowWorker(QThread)
class UnsignedView(QWidget):

    def __init__(self, view_model):
        super().__init__()
        self.view_model = view_model 

        login_register_btn = QPushButton("Login/Register")
        apply_disabled_button_style(login_register_btn)
        login_register_btn.clicked.connect(self.open_login_register)
        self.addWidget(login_register_btn)


        # Ссылка "Why register?"
        why_register_btn = QPushButton("Why register?")
        apply_link_style(why_register_btn)
        why_register_btn.clicked.connect(self.open_why_register)
        self.addWidget(why_register_btn, alignment=Qt.AlignCenter)

class SignedView(QWidget):

    def __init__(self, view_model):
        super().__init__()
        self.view_model = view_model 

        account_management_btn = QPushButton("Account Management")
        apply_disabled_button_style(account_management_btn)
        account_management_btn.clicked.connect(self.open_account_management)
        self.addWidget(account_management_btn)



class HelloView(QWidget):
    def __init__(self, view_model):
        super().__init__()
        self.view_model = view_model # Reference to ViewModel

        self.setWindowTitle('uMovie - Welcome')
        self.setGeometry(300, 300, 800, 600)
        apply_window_style(self)

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        column1_layout = QVBoxLayout()
        column2_layout = QVBoxLayout()

        # Заголовок
        title_label = QLabel("uMovie")
        apply_title_style(title_label)
        column1_layout.addWidget(title_label, alignment=Qt.AlignCenter)

        # Кнопки
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(20)

        new_project_btn = QPushButton("New Project")
        open_project_btn = QPushButton("Open Project")
        
        apply_button_style(new_project_btn)
        apply_button_style(open_project_btn)

        new_project_btn.clicked.connect(self.view_model.open_new_project)
        open_project_btn.clicked.connect(self.view_model.open_project)

        buttons_layout.addWidget(new_project_btn)
        buttons_layout.addWidget(open_project_btn)

        self.auth_view = QStackedWidget()
        auth_view_u = UnsignedView(self.view_model)
        auth_view_s = SignedView(self.view_model)

        account_management_btn = QPushButton("Account Management")
        apply_disabled_button_style(account_management_btn)
        account_management_btn.clicked.connect(self.open_account_management)
        self.addWidget(account_management_btn)

        column1_layout.addLayout(buttons_layout)
        column1_layout.addWidget(auth_view)


        # Таблица Recent
        recent_label = QLabel("Recent")
        apply_label_style(recent_label)
        main_layout.addWidget(recent_label, alignment=Qt.AlignRight)

        recent_table = QTableWidget(4, 3)
        recent_table.setHorizontalHeaderLabels(["Project", "Time", "Date"])
        recent_table.setFixedSize(300, 150)
        recent_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Захардкодим данные
        recent_data = [
            ("project 4", "12:34", "Yesterday"),
            ("project 3", "23:32", "Monday"),
            ("project 2", "02:02", "16.03"),
            ("project 1", "13:57", "16.12.2024")
        ]

        for row, (project, time, date) in enumerate(recent_data):
            recent_table.setItem(row, 0, QTableWidgetItem(project))
            recent_table.setItem(row, 1, QTableWidgetItem(time))
            recent_table.setItem(row, 2, QTableWidgetItem(date))

        recent_table.resizeColumnsToContents()
        column2_layout.addWidget(recent_table, alignment=Qt.AlignRight)

        main_layout.addLayout(column1_layout)
        main_layout.addLayout(column2_layout)
        self.setLayout(main_layout)

        self.view_model.state_changed.connect(self.update_view)
        self.update_view()  # Set initial state
    
    def update_view(self, display_option):
        # Remove the button and link if they are already in the layout
 

        if display_option:
            self.remove_widget(self.button)
            self.remove_widget(self.link)

            self.layout.addWidget(self.button)
            self.layout.addWidget(self.link)
        else:
            self.layout.addWidget(self.button)
    
    def remove_widget(self, widget):
        self.layout.removeWidget(widget)
        widget.setParent(None)
    

    def open_account_management(self):
        print("Opening Account Management (ui/settings_window.py would be called here)")
    
    def open_login_register(self):
        self.auth_window = AuthView()
        self.auth_window.show()

    def open_why_register(self):
        QDesktopServices.openUrl(QUrl("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
    

if __name__ == '__main__':
    if os.getenv("DEVELOP_MACHINE"):
        print("Running on the development machine.")

    app = QApplication(sys.argv)

    model = HelloModel()
    viewModel = HelloViewModel(model)
    view = HelloView(viewModel)
    
    view.show()
    sys.exit(app.exec_())