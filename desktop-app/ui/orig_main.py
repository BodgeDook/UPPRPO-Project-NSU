import sys
from PyQt5.QtCore import Qt, QTimer, QSize, QUrl
from PyQt5.QtGui import QKeySequence, QIcon
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QToolBar, QAction, QProgressBar, QLabel, QSlider, QComboBox,
                             QGraphicsView, QGraphicsScene, QSplitter, QCheckBox, QStyle,
                             QUndoStack, QGroupBox, QPushButton, QSpinBox, QFileDialog, QTableWidget,
                             QTableWidgetItem)
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtGui import QDesktopServices

# importing styles:
from styles import (apply_button_style, apply_disabled_button_style, apply_label_style,
                    apply_title_style, apply_link_style, apply_window_style)
from auth_window import AuthView  # for Login/Register

class VideoEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setupUndoRedo()
        self.setupAutosave()

    def initUI(self):
        self.setWindowTitle('PyVideo Editor')
        self.setGeometry(0, 0, 1920, 1080)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        top_splitter = QSplitter(Qt.Horizontal)
        
        tools_panel = QWidget()
        tools_layout = QHBoxLayout(tools_panel)
        
        self.create_video_tools(tools_layout)
        self.create_audio_tools(tools_layout)

        self.preview_widget = QGraphicsView()
        self.preview_scene = QGraphicsScene()
        self.preview_widget.setScene(self.preview_scene)
        self.video_widget = QVideoWidget()
        self.preview_scene.addWidget(self.video_widget)

        top_splitter.addWidget(tools_panel)
        top_splitter.addWidget(self.preview_widget)
        top_splitter.setSizes([400, 900])

        timeline_widget = QGraphicsView()
        timeline_widget.setMinimumHeight(150)
        self.timeline_scene = QGraphicsScene()
        timeline_widget.setScene(self.timeline_scene)

        main_layout.addWidget(top_splitter)
        main_layout.addWidget(timeline_widget)

        self.createTopToolbars()

    def create_video_tools(self, parent_layout):
        video_group = QGroupBox("Video Tools")
        layout = QVBoxLayout()

        size_group = QGroupBox("Size & Orientation")
        size_layout = QVBoxLayout()
        
        self.aspect_ratio_combo = QComboBox()
        self.aspect_ratio_combo.addItems(["16:9", "4:3", "1:1", "9:16", "Custom"])
        size_layout.addWidget(QLabel("Aspect Ratio:"))
        size_layout.addWidget(self.aspect_ratio_combo)

        self.rotation_buttons = QHBoxLayout()
        for angle in [0, 90, 180, 270]:
            btn = QPushButton(f"{angle}°")
            self.rotation_buttons.addWidget(btn)
        size_layout.addWidget(QLabel("Rotation:"))
        size_layout.addLayout(self.rotation_buttons)
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)

        color_group = QGroupBox("Color Adjustment")
        color_layout = QVBoxLayout()
        
        self.brightness_slider = self.create_slider("Brightness:", -100, 100)
        self.contrast_slider = self.create_slider("Contrast:", -100, 100)
        self.saturation_slider = self.create_slider("Saturation:", 0, 200)
        
        color_layout.addWidget(self.brightness_slider)
        color_layout.addWidget(self.contrast_slider)
        color_layout.addWidget(self.saturation_slider)
        color_group.setLayout(color_layout)
        layout.addWidget(color_group)

        effects_group = QGroupBox("Effects")
        effects_layout = QVBoxLayout()
        
        self.background_removal = QCheckBox("Remove Background")
        self.filters_combo = QComboBox()
        self.filters_combo.addItems(["None", "Sepia", "Grayscale", "Vintage", "Cool", "Warm"])
        
        effects_layout.addWidget(self.background_removal)
        effects_layout.addWidget(QLabel("Video Filters:"))
        effects_layout.addWidget(self.filters_combo)
        effects_group.setLayout(effects_layout)
        layout.addWidget(effects_group)

        video_group.setLayout(layout)
        parent_layout.addWidget(video_group)

    def create_audio_tools(self, parent_layout):
        audio_group = QGroupBox("Audio Tools")
        layout = QVBoxLayout()

        volume_group = QGroupBox("Volume Control")
        volume_layout = QVBoxLayout()
        
        self.volume_slider = self.create_slider("Master Volume:", 0, 200)
        volume_layout.addWidget(self.volume_slider)
        volume_group.setLayout(volume_layout)
        layout.addWidget(volume_group)

        eq_group = QGroupBox("Equalizer")
        eq_layout = QVBoxLayout()
        
        self.low_freq_slider = self.create_slider("Low (60Hz):", -20, 20)
        self.mid_freq_slider = self.create_slider("Mid (1kHz):", -20, 20)
        self.high_freq_slider = self.create_slider("High (16kHz):", -20, 20)
        
        eq_layout.addWidget(self.low_freq_slider)
        eq_layout.addWidget(self.mid_freq_slider)
        eq_layout.addWidget(self.high_freq_slider)
        eq_group.setLayout(eq_layout)
        layout.addWidget(eq_group)

        noise_group = QGroupBox("Noise Reduction")
        noise_layout = QVBoxLayout()
        
        self.noise_reduction = QCheckBox("Enable Noise Reduction")
        self.noise_threshold = QSpinBox()
        self.noise_threshold.setRange(0, 100)
        
        noise_layout.addWidget(self.noise_reduction)
        noise_layout.addWidget(QLabel("Threshold:"))
        noise_layout.addWidget(self.noise_threshold)
        noise_group.setLayout(noise_layout)
        layout.addWidget(noise_group)

        audio_group.setLayout(layout)
        parent_layout.addWidget(audio_group)

    def create_slider(self, label, min_val, max_val):
        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel(label))
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue((max_val + min_val) // 2)
        layout.addWidget(slider)
        container.setLayout(layout)
        return container

    def createTopToolbars(self):
        file_toolbar = QToolBar('File Toolbar')
        file_toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(Qt.TopToolBarArea, file_toolbar)

        action_icons = {
            'New': QStyle.SP_FileIcon,
            'Open': QStyle.SP_DialogOpenButton,
            'Save': QStyle.SP_DialogSaveButton,
            'Export': QStyle.SP_DialogYesButton
        }

        for text, icon in action_icons.items():
            action = QAction(QIcon(''), text, self)
            if icon:
                action.setIcon(self.style().standardIcon(icon))
            file_toolbar.addAction(action)

        progress_toolbar = QToolBar('Progress Toolbar')
        self.addToolBar(Qt.TopToolBarArea, progress_toolbar)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(200)
        progress_toolbar.addWidget(self.progress_bar)

    def setupUndoRedo(self):
        self.undo_stack = QUndoStack(self)
        
        undo_action = self.undo_stack.createUndoAction(self, 'Undo')
        undo_action.setShortcuts(QKeySequence.Undo)
        
        redo_action = self.undo_stack.createRedoAction(self, 'Redo')
        redo_action.setShortcuts(QKeySequence.Redo)
        
        edit_menu = self.menuBar().addMenu('Edit')
        edit_menu.addAction(undo_action)
        edit_menu.addAction(redo_action)

    def setupAutosave(self):
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self.autosave)
        self.autosave_timer.start(300000)

    def autosave(self):
        print("Autosaving project...")

class WelcomeWindowUnsigned(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('uMovie - Welcome')
        self.setGeometry(300, 300, 800, 600)
        apply_window_style(self)

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        # Заголовок
        title_label = QLabel("uMovie")
        apply_title_style(title_label)
        main_layout.addWidget(title_label, alignment=Qt.AlignCenter)

        # Кнопки
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

        login_register_btn = QPushButton("Login/Register")
        apply_disabled_button_style(login_register_btn)
        login_register_btn.clicked.connect(self.open_login_register)
        buttons_layout.addWidget(login_register_btn)

        main_layout.addLayout(buttons_layout)

        # Ссылка "Why register?"
        why_register_btn = QPushButton("Why register?")
        apply_link_style(why_register_btn)
        why_register_btn.clicked.connect(self.open_why_register)
        main_layout.addWidget(why_register_btn, alignment=Qt.AlignCenter)

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

    def open_login_register(self):
        self.auth_window = AuthView()
        self.auth_window.show()

    def open_why_register(self):
        QDesktopServices.openUrl(QUrl("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))

class WelcomeWindowSigned(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('uMovie - Welcome')
        self.setGeometry(300, 300, 800, 600)
        apply_window_style(self)

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        # Заголовок
        title_label = QLabel("uMovie")
        apply_title_style(title_label)
        main_layout.addWidget(title_label, alignment=Qt.AlignCenter)

        # Кнопки
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
        apply_disabled_button_style(account_management_btn)
        account_management_btn.clicked.connect(self.open_account_management)
        buttons_layout.addWidget(account_management_btn)

        main_layout.addLayout(buttons_layout)

        # Recent Table
        recent_label = QLabel("Recent")
        apply_label_style(recent_label)
        main_layout.addWidget(recent_label, alignment=Qt.AlignRight)

        recent_table = QTableWidget(4, 3)
        recent_table.setHorizontalHeaderLabels(["Project", "Time", "Date"])
        recent_table.setFixedSize(300, 150)
        recent_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # For example:
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
        print("Opening Account Management (ui/settings_window.py would be called here)")

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # for a test: change is_signed_in on True/False to switch between two windows
    is_signed_in = False

    if is_signed_in:
        welcome_window = WelcomeWindowSigned()
    else:
        welcome_window = WelcomeWindowUnsigned()

    welcome_window.show()
    sys.exit(app.exec_())