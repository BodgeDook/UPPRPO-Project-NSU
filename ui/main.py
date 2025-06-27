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

from styles import (apply_button_style, apply_disabled_button_style, apply_label_style,
                    apply_title_style, apply_link_style, apply_window_style, apply_welcome_window_style, theme_manager)
from settings_window import SettingsWindow

class VideoEditor(QMainWindow):

    def __init__(self):
        super().__init__()

        self.initUI()  # Вызываем initUI первым
        self.setupUndoRedo()
        self.setupAutosave()
        theme_manager.theme_changed.connect(self.update_theme)

    def initUI(self):
        self.setWindowTitle('PyVideo Editor')
        self.setGeometry(0, 0, 1920, 1080)
        apply_window_style(self)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)  # Сохраняем ссылку на layout
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Верхний сплиттер для инструментов и предпросмотра
        top_splitter = QSplitter(Qt.Horizontal)
        
        # Панель инструментов (расширенная)
        toolbox = QWidget()
        toolbox_layout = QVBoxLayout(toolbox)
        self.play_btn = QPushButton("Play")
        self.pause_btn = QPushButton("Pause")
        self.trim_btn = QPushButton("Trim")
        self.export_btn = QPushButton("Export")
        apply_button_style(self.play_btn)
        apply_button_style(self.pause_btn)
        apply_button_style(self.trim_btn)
        apply_button_style(self.export_btn)
        toolbox_layout.addWidget(self.play_btn)
        toolbox_layout.addWidget(self.pause_btn)
        toolbox_layout.addWidget(self.trim_btn)
        toolbox_layout.addWidget(self.export_btn)
        toolbox.setFixedWidth(150)

        tools_panel = QWidget()
        tools_layout = QHBoxLayout(tools_panel)
        self.create_video_tools(tools_layout)
        self.create_audio_tools(tools_layout)
        tools_layout.addWidget(toolbox)  # Добавляем новую панель
        tools_panel.setLayout(tools_layout)

        self.preview_widget = QGraphicsView()
        self.preview_scene = QGraphicsScene()
        self.preview_widget.setScene(self.preview_scene)
        self.video_widget = QVideoWidget()
        self.preview_scene.addWidget(self.video_widget)

        top_splitter.addWidget(tools_panel)
        top_splitter.addWidget(self.preview_widget)
        top_splitter.setSizes([600, 900])  # Устанавливаем пропорции (600 для инструментов, 900 для предпросмотра)

        # Таймлайн
        timeline_widget = QGraphicsView()
        timeline_widget.setMinimumHeight(150)
        self.timeline_scene = QGraphicsScene()
        timeline_widget.setScene(self.timeline_scene)
        clip = self.timeline_scene.addRect(10, 10, 200, 50, brush=Qt.blue)
        self.timeline_clips = [{"item": clip, "start": 0, "duration": 200}]  # Инициализация списка

        # Собираем всё в вертикальный layout
        self.main_layout.addWidget(top_splitter)
        self.main_layout.addWidget(timeline_widget)

        self.createTopToolbars()
        self.connect_buttons()  # Подключаем действия кнопок после создания всех виджетов

    def init_timeline(self):
        timeline_widget = QGraphicsView()
        timeline_widget.setMinimumHeight(150)
        self.timeline_scene = QGraphicsScene()
        timeline_widget.setScene(self.timeline_scene)

        # Исправленный вызов addRect без указания pen=None
        clip = self.timeline_scene.addRect(10, 10, 200, 50, brush=Qt.blue)
        self.timeline_clips.append({"item": clip, "start": 0, "duration": 200})
        timeline_widget.setScene(self.timeline_scene)
        self.main_layout.addWidget(timeline_widget)

    def trim_video(self):
        if self.timeline_clips:
            clip_data = self.timeline_clips[0]
            current_width = clip_data["item"].rect().width()
            if current_width > 50:  # Минимальная длина клипа
                clip_data["item"].setRect(10, 10, current_width - 20, 50)
                clip_data["duration"] -= 20
                print(f"Trimmed clip to {clip_data['duration']} units")

    def connect_buttons(self):
        self.play_btn.clicked.connect(self.play_video)
        self.pause_btn.clicked.connect(self.pause_video)
        self.trim_btn.clicked.connect(self.trim_video)
        self.export_btn.clicked.connect(self.export_video)

    def play_video(self):
        print("Playing video...")  # Заглушка, нужно интегрировать QMediaPlayer

    def pause_video(self):
        print("Pausing video...")  # Заглушка

    def trim_video(self):
        print("Trimming video...")  # Заглушка, реализуем в таймлайне

    def export_video(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Video", "", "Video Files (*.mp4 *.avi)")
        if file_path:
            print(f"Exporting to {file_path}")  # Заглушка

    def create_video_tools(self, parent_layout):
        video_group = QGroupBox("Video Tools")
        layout = QVBoxLayout()

        size_group = QGroupBox("Size & Orientation")
        size_layout = QVBoxLayout()
        
        self.aspect_ratio_combo = QComboBox()
        self.aspect_ratio_combo.addItems(["16:9", "4:3", "1:1", "9:16", "Custom"])
        size_layout.addWidget(QLabel("Aspect Ratio:"))
        apply_label_style(size_layout.itemAt(size_layout.count()-1).widget())
        size_layout.addWidget(self.aspect_ratio_combo)

        self.rotation_buttons = QHBoxLayout()
        for angle in [0, 90, 180, 270]:
            btn = QPushButton(f"{angle}°")
            apply_button_style(btn)
            self.rotation_buttons.addWidget(btn)
        size_layout.addWidget(QLabel("Rotation:"))
        apply_label_style(size_layout.itemAt(size_layout.count()-1).widget())
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
        apply_label_style(effects_layout.itemAt(effects_layout.count()-1).widget())
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
        apply_label_style(noise_layout.itemAt(noise_layout.count()-1).widget())
        noise_layout.addWidget(self.noise_threshold)
        noise_group.setLayout(noise_layout)
        layout.addWidget(noise_group)

        audio_group.setLayout(layout)
        parent_layout.addWidget(audio_group)

    def create_slider(self, label, min_val, max_val):
        container = QWidget()
        layout = QVBoxLayout()
        lbl = QLabel(label)
        apply_label_style(lbl)
        layout.addWidget(lbl)
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

    def update_theme(self, theme):
        apply_window_style(self)
        for widget in self.findChildren(QPushButton):
            apply_button_style(widget)
        for widget in self.findChildren(QLabel):
            apply_label_style(widget)
        self.update()

class WelcomeWindowUnsigned(QWidget):
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

        login_register_btn = QPushButton("Login/Register")
        apply_disabled_button_style(login_register_btn)
        login_register_btn.clicked.connect(self.open_login_register)
        buttons_layout.addWidget(login_register_btn)

        main_layout.addLayout(buttons_layout)

        why_register_btn = QPushButton("Why register?")
        apply_link_style(why_register_btn)
        why_register_btn.clicked.connect(self.open_why_register)
        main_layout.addWidget(why_register_btn, alignment=Qt.AlignCenter)

        recent_label = QLabel("Recent")
        apply_label_style(recent_label)
        main_layout.addWidget(recent_label, alignment=Qt.AlignRight)

        recent_table = QTableWidget(4, 3)
        recent_table.setHorizontalHeaderLabels(["Project", "Time", "Date"])
        recent_table.setFixedSize(300, 150)
        recent_table.setEditTriggers(QTableWidget.NoEditTriggers)

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
        from auth_window import AuthView, AuthViewModel, AuthModel
        self.auth_window = AuthView(AuthViewModel(AuthModel()))
        self.auth_window.show()

    def open_why_register(self):
        QDesktopServices.openUrl(QUrl("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))

    def update_theme(self, theme):
        apply_welcome_window_style(self)
        for widget in self.findChildren(QPushButton):
            if widget.text() == "Login/Register":
                apply_disabled_button_style(widget)
            elif widget.text() == "Why register?":
                apply_link_style(widget)
            else:
                apply_button_style(widget)
        for widget in self.findChildren(QLabel):
            if widget.text() == "uMovie":
                apply_title_style(widget)
            else:
                apply_label_style(widget)
        self.update()

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    print("Application initialized")
    is_signed_in = True # False for new users
    if is_signed_in:
        welcome_window = WelcomeWindowSigned()
    else:
        welcome_window = WelcomeWindowUnsigned()
    welcome_window.show()
    print("Window shown, starting event loop")
    sys.exit(app.exec_())