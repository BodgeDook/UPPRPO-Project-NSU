import sys

from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QKeySequence, QIcon
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QToolBar, QAction, QProgressBar, QLabel, QSlider, QComboBox,
                             QGraphicsView, QGraphicsScene, QSplitter, QCheckBox, QStyle,
                             QUndoStack, QGroupBox, QPushButton, QSpinBox)
from PyQt5.QtMultimediaWidgets import QVideoWidget

'''
video_editor/
│── main.py               # Entry point
│── main_window.py        # Main UI
│── video_player.py       # Video playback logic
│── timeline.py           # Timeline & clip management
│── toolbar.py            # Tools & actions
│── settings_window.py    # Separate window for settings
│── resources/            # Icons, UI assets, etc.
'''

class VideoEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setupUndoRedo()
        self.setupAutosave()

    def initUI(self):
        self.setWindowTitle('PyVideo Editor')
        self.setGeometry(0, 0, 1920, 1080)  # Окно на весь экран
        
        # Главный центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Верхняя часть с инструментами и видео
        top_splitter = QSplitter(Qt.Horizontal)
        
        # Левая панель инструментов
        tools_panel = QWidget()
        tools_layout = QHBoxLayout(tools_panel)
        
        # Создаем две колонки
        self.create_video_tools(tools_layout)
        self.create_audio_tools(tools_layout)

        # Правая панель превью
        self.preview_widget = QGraphicsView()
        self.preview_scene = QGraphicsScene()
        self.preview_widget.setScene(self.preview_scene)
        self.video_widget = QVideoWidget()
        self.preview_scene.addWidget(self.video_widget)

        # Добавляем панели в сплиттер
        top_splitter.addWidget(tools_panel)
        top_splitter.addWidget(self.preview_widget)
        top_splitter.setSizes([400, 900])

        # Таймлайн внизу
        timeline_widget = QGraphicsView()
        timeline_widget.setMinimumHeight(150)
        self.timeline_scene = QGraphicsScene()
        timeline_widget.setScene(self.timeline_scene)

        # Собираем главный лэйаут
        main_layout.addWidget(top_splitter)
        main_layout.addWidget(timeline_widget)

        # Создаем верхние тулбары
        self.createTopToolbars()

    def create_video_tools(self, parent_layout):
        # Видео инструменты
        video_group = QGroupBox("Video Tools")
        layout = QVBoxLayout()

        # Размер и пропорции
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

        # Цветокоррекция
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

        # Фильтры и фон
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
        # Аудио инструменты
        audio_group = QGroupBox("Audio Tools")
        layout = QVBoxLayout()

        # Громкость
        volume_group = QGroupBox("Volume Control")
        volume_layout = QVBoxLayout()
        
        self.volume_slider = self.create_slider("Master Volume:", 0, 200)
        volume_layout.addWidget(self.volume_slider)
        volume_group.setLayout(volume_layout)
        layout.addWidget(volume_group)

        # Эквалайзер
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

        # Шумоподавление
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
        # Первый тулбар (File operations)
        file_toolbar = QToolBar('File Toolbar')
        file_toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(Qt.TopToolBarArea, file_toolbar)

        # Правильные иконки из QStyle
        action_icons = {
            'New': QStyle.SP_FileIcon,
            'Open': QStyle.SP_DialogOpenButton,
            'Save': QStyle.SP_DialogSaveButton,
            'Export': QStyle.SP_DialogYesButton
        }

        for text, icon in action_icons.items():
            action = QAction(QIcon(''), text, self)  # Пустая иконка как заглушка
            if icon:
                action.setIcon(self.style().standardIcon(icon))
            file_toolbar.addAction(action)

        # Второй тулбар (Progress)
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
        self.autosave_timer.start(300000)  # 5 минут

    def autosave(self):
        print("Autosaving project...")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = VideoEditor()
    editor.show()
    sys.exit(app.exec_())