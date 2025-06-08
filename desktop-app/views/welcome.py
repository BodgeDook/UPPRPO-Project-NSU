from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton

class WelcomeWindow(QMainWindow):
    open_project_requested = pyqtSignal(str)  # path to an existing project file
    new_project_requested = pyqtSignal()      # create a brand-new project
    login_requested = pyqtSignal()            # open the login dialog

    def __init__(self):
        super().__init__()
        self.setWindowTitle("uMovie – Welcome")
        self.resize(400, 200)

        # Создаем контейнер и лэйаут
        self.container = QWidget()
        self.layout = QVBoxLayout()
        self.container.setLayout(self.layout)

        # Инициализируем кнопки
        self.btn_open = QPushButton("Open Project…")
        self.btn_new = QPushButton("Create New Project")
        self.btn_login = QPushButton("Log In / Register")

        # Подключаем сигналы
        self.btn_open.clicked.connect(self._on_open_clicked)
        self.btn_new.clicked.connect(self.new_project_requested.emit)
        self.btn_login.clicked.connect(self.login_requested.emit)

        # Изначально показываем только кнопку логина
        self.show_unauthenticated_ui()

        self.setCentralWidget(self.container)

    def _on_open_clicked(self):
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Open uMovie Project", filter="uMovie (*.json)")
        if path:
            self.open_project_requested.emit(path)

    def show_unauthenticated_ui(self):
        """Показывает UI до авторизации (только кнопка Log In / Register)."""
        # Очищаем лэйаут
        self._clear_layout()
        # Добавляем только кнопку логина
        self.layout.addWidget(self.btn_login)
        self.layout.addStretch(1)

    def show_authenticated_ui(self):
        """Показывает UI после авторизации (кнопки Open Project и Create New Project)."""
        # Очищаем лэйаут
        self._clear_layout()
        # Добавляем кнопки для работы с проектами
        self.layout.addWidget(self.btn_open)
        self.layout.addWidget(self.btn_new)
        self.layout.addStretch(1)

    def _clear_layout(self):
        """Очищает лэйаут, корректно обрабатывая все элементы."""
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
