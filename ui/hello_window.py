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
    SETTINGS_PATH = "/Users/danielgehrman/Documents/Programming/Projects/uMovie/config/settings.json"
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
        folder_path = QFileDialog.getExistingDirectory()
        if folder_path:
            print(f"Selected folder: {folder_path}")


# class HelloView(QWidget):
#     def __init__(self, view_model):
#         super().__init__()
#         self.view_model = view_model # Reference to ViewModel

#         self.setWindowTitle('uMovie - Welcome')
#         self.setGeometry(300, 300, 800, 600)
#         apply_window_style(self)

#         main_layout = QVBoxLayout()
#         main_layout.setAlignment(Qt.AlignCenter)

#         column1_layout = QVBoxLayout()
#         column2_layout = QVBoxLayout()

#         # Заголовок
#         title_label = QLabel("uMovie")
#         apply_title_style(title_label)
#         column1_layout.addWidget(title_label, alignment=Qt.AlignCenter)

#         # Кнопки
#         buttons_layout = QVBoxLayout()
#         buttons_layout.setSpacing(20)

#         new_project_btn = QPushButton("New Project")
#         open_project_btn = QPushButton("Open Project")
        
#         apply_button_style(new_project_btn)
#         apply_button_style(open_project_btn)

#         new_project_btn.clicked.connect(self.view_model.open_new_project)
#         open_project_btn.clicked.connect(self.view_model.open_project)

#         buttons_layout.addWidget(new_project_btn)
#         buttons_layout.addWidget(open_project_btn)

#         # self.auth_view = QStackedWidget()
#         # auth_view_u = UnsignedView(self.view_model)
#         # auth_view_s = SignedView(self.view_model)

#         account_management_btn = QPushButton("Account Management")
#         apply_disabled_button_style(account_management_btn)
#         account_management_btn.clicked.connect(self.open_account_management)
#         self.addWidget(account_management_btn)

#         column1_layout.addLayout(buttons_layout)
#         # column1_layout.addWidget(auth_view)

#         # 1) Create a QStackedWidget for auth:
#         self.auth_stack = QStackedWidget()
#         self._build_unsigned_page()
#         self._build_signed_page()
#         main_layout.addWidget(self.auth_stack)

#         # 2) Wire state changes to switch pages:
#         self.view_model.state_changed.connect(self.on_state_changed)
#         self.on_state_changed(self.view_model.model.get_is_signed_in())


#         # Таблица Recent
#         recent_label = QLabel("Recent")
#         apply_label_style(recent_label)
#         main_layout.addWidget(recent_label, alignment=Qt.AlignRight)

#         recent_table = QTableWidget(4, 3)
#         recent_table.setHorizontalHeaderLabels(["Project", "Time", "Date"])
#         recent_table.setFixedSize(300, 150)
#         recent_table.setEditTriggers(QTableWidget.NoEditTriggers)

#         # Захардкодим данные
#         recent_data = [
#             ("project 4", "12:34", "Yesterday"),
#             ("project 3", "23:32", "Monday"),
#             ("project 2", "02:02", "16.03"),
#             ("project 1", "13:57", "16.12.2024")
#         ]

#         for row, (project, time, date) in enumerate(recent_data):
#             recent_table.setItem(row, 0, QTableWidgetItem(project))
#             recent_table.setItem(row, 1, QTableWidgetItem(time))
#             recent_table.setItem(row, 2, QTableWidgetItem(date))

#         recent_table.resizeColumnsToContents()
#         column2_layout.addWidget(recent_table, alignment=Qt.AlignRight)

#         main_layout.addLayout(column1_layout)
#         main_layout.addLayout(column2_layout)
#         self.setLayout(main_layout)

#         # self.view_model.state_changed.connect(self.update_view)
#         # self.update_view()  # Set initial state
    
#     # def update_view(self, display_option):
#     #     # Remove the button and link if they are already in the layout
#     #     if display_option:
#     #         self.remove_widget(self.button)
#     #         self.remove_widget(self.link)
#     #         self.layout.addWidget(self.button)
#     #         self.layout.addWidget(self.link)
#     #     else:
#     #         self.layout.addWidget(self.button)

#     # @pyqtSlot(bool)
#     def on_state_changed(self, is_signed_in):
#         # assume unsigned page is index 0, signed page is index 1
#         self.auth_stack.setCurrentIndex(1 if is_signed_in else 0)

#     # def remove_widget(self, widget):
#     #     self.layout.removeWidget(widget)
#     #     widget.setParent(None)

#     def open_account_management(self):
#         print("Opening Account Management (ui/settings_window.py would be called here)")
    
#     def open_login_register(self):
#         self.auth_window = AuthView()
#         self.auth_window.show()

#     def open_why_register(self):
#         QDesktopServices.openUrl(QUrl("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
    
#     def _build_unsigned_page(self):
#         page = QWidget()
#         lo = QVBoxLayout(page)
#         btn = QPushButton("Login / Register")
#         apply_button_style(btn)
#         btn.clicked.connect(self.open_login_register)
#         lo.addWidget(btn, alignment=Qt.AlignCenter)

#         link = QPushButton("Why register?")
#         apply_link_style(link)
#         link.clicked.connect(self.open_why_register)
#         lo.addWidget(link, alignment=Qt.AlignCenter)

#         self.auth_stack.addWidget(page)

#     def _build_signed_page(self):
#         page = QWidget()
#         lo = QVBoxLayout(page)
#         btn = QPushButton("Account Management")
#         apply_button_style(btn)
#         btn.clicked.connect(self.open_account_management)
#         lo.addWidget(btn, alignment=Qt.AlignCenter)
#         self.auth_stack.addWidget(page)
    
class HelloView(QWidget):
    def __init__(self, view_model):
        super().__init__()
        self.view_model = view_model

        self.setWindowTitle('uMovie – Welcome')
        self.setGeometry(300, 300, 800, 600)
        apply_window_style(self)

        # ─── Main layout ───
        main_layout = QHBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        # Left column: title, new/open buttons, auth stack
        column1 = QVBoxLayout()
        column1.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # Title
        title = QLabel("uMovie")
        apply_title_style(title)
        column1.addWidget(title)

        # New/Open buttons
        for text, slot in (("New Project", self.view_model.open_new_project),
                           ("Open Project", self.view_model.open_project)):
            btn = QPushButton(text)
            apply_button_style(btn)
            btn.clicked.connect(slot)
            column1.addWidget(btn)
        column1.addSpacing(20)

        # Auth stack
        self.auth_stack = QStackedWidget()
        self._build_unsigned_page()
        self._build_signed_page()
        column1.addWidget(self.auth_stack)

        # Right column: Recent table
        column2 = QVBoxLayout()
        column2.setAlignment(Qt.AlignTop | Qt.AlignRight)
        recent_label = QLabel("Recent")
        apply_label_style(recent_label)
        column2.addWidget(recent_label)
        recent_table = QTableWidget(4, 3)
        recent_table.setHorizontalHeaderLabels(["Project","Time","Date"])
        recent_table.setEditTriggers(QTableWidget.NoEditTriggers)
        for row, (p,t,d) in enumerate([
            ("project 4","12:34","Yesterday"),
            ("project 3","23:32","Monday"),
            ("project 2","02:02","16.03"),
            ("project 1","13:57","16.12.2024"),
        ]):
            for col,item in enumerate((p,t,d)):
                recent_table.setItem(row,col,QTableWidgetItem(item))
        recent_table.resizeColumnsToContents()
        column2.addWidget(recent_table)

        # Put columns into main layout
        main_layout.addLayout(column1)
        main_layout.addLayout(column2)

        # ─── Connect auth switching ───
        self.view_model.state_changed.connect(self.on_state_changed)
        # Initialize to whatever is in settings.json
        self.on_state_changed(self.view_model.current_state)

    def _build_unsigned_page(self):
        page = QWidget()
        lo = QVBoxLayout(page)
        lo.setAlignment(Qt.AlignCenter)
        btn = QPushButton("Login / Register")
        apply_button_style(btn)
        btn.clicked.connect(self.open_login_register)
        lo.addWidget(btn)
        link = QPushButton("Why register?")
        apply_link_style(link)
        link.clicked.connect(self.open_why_register)
        lo.addWidget(link)
        self.auth_stack.addWidget(page)

    def _build_signed_page(self):
        page = QWidget()
        lo = QVBoxLayout(page)
        lo.setAlignment(Qt.AlignCenter)
        btn = QPushButton("Account Management")
        apply_button_style(btn)
        btn.clicked.connect(self.open_account_management)
        lo.addWidget(btn)
        self.auth_stack.addWidget(page)

    # @pyqtSlot(bool)
    def on_state_changed(self, is_signed_in):
        # page 0 = unsigned, page 1 = signed
        self.auth_stack.setCurrentIndex(1 if is_signed_in else 0)

    def open_login_register(self):
        self.auth_window = AuthView()
        self.auth_window.show()

    def open_why_register(self):
        QDesktopServices.openUrl(QUrl("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))

    def open_account_management(self):
        print("Opening Account Management… (replace with real UI call)")


if __name__ == '__main__':
    if os.getenv("DEVELOP_MACHINE"):
        print("Running on the development machine.")

    app = QApplication(sys.argv)

    model = HelloModel()
    viewModel = HelloViewModel(model)
    view = HelloView(viewModel)
    
    view.show()
    sys.exit(app.exec_())