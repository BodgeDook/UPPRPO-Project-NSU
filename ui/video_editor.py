# ui/video_editor.py
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGraphicsView, QGraphicsScene, QPushButton, QGroupBox, QToolBar, QAction, QProgressBar, QFileDialog, QMessageBox, QComboBox, QCheckBox, QSlider, QSpinBox, QUndoStack, QSizePolicy, QStyle, QLabel
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt5.QtGui import QPainter, QIcon, QPixmap, QImage, QKeySequence

from styles import apply_button_style, apply_window_style, apply_label_style, theme_manager
from video_processor import VideoProcessor
from timeline_manager import TimelineManager

class VideoEditor(QMainWindow):
    frameUpdated = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.video_processor = VideoProcessor(self)
        self.current_preview = None
        self.last_frame_idx = -1
        self.current_frame_idx = 0
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate_frame)
        self.cut_start_frame = None
        self.cut_end_frame = None
        self.is_cutting = False
        self.initUI()
        self.timeline_manager = TimelineManager(self)
        self.timeline_manager.setup()  # Добавлено
        self.setupUndoRedo()
        self.setupAutosave()
        theme_manager.theme_changed.connect(self.update_theme)
        self.frameUpdated.connect(self.update_preview_frame)

    def initUI(self):
        self.play_btn = QPushButton("Play")
        self.pause_btn = QPushButton("Pause")
        self.cut_btn = QPushButton("Start Cut")
        self.confirm_cut_btn = QPushButton("Confirm Cut")
        self.confirm_cut_btn.setEnabled(False)
        self.cancel_cut_btn = QPushButton("Cancel Cut")
        self.cancel_cut_btn.setEnabled(False)
        self.export_btn = QPushButton("Export")

        self.setWindowTitle('PyVideo Editor')
        self.setGeometry(100, 100, 1280, 720)
        apply_window_style(self)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        main_splitter = QSplitter(Qt.Vertical)
        top_splitter = QSplitter(Qt.Horizontal)

        toolbox = QWidget()
        toolbox_layout = QVBoxLayout(toolbox)
        for btn in (self.play_btn, self.pause_btn, self.cut_btn, self.confirm_cut_btn, self.cancel_cut_btn, self.export_btn):
            apply_button_style(btn)
            toolbox_layout.addWidget(btn)
        toolbox.setFixedWidth(150)
        tools_panel = QWidget()
        tools_layout = QHBoxLayout(tools_panel)
        self.create_video_tools(tools_layout)
        self.create_audio_tools(tools_layout)
        tools_layout.addWidget(toolbox)
        tools_panel.setLayout(tools_layout)

        self.preview_widget = QGraphicsView()
        self.preview_widget.setRenderHint(QPainter.SmoothPixmapTransform)
        self.preview_scene = QGraphicsScene()
        self.preview_widget.setScene(self.preview_scene)
        self.preview_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.preview_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.preview_widget.setAlignment(Qt.AlignCenter)
        self.preview_widget.resizeEvent = self.resize_preview

        top_splitter.addWidget(tools_panel)
        top_splitter.addWidget(self.preview_widget)
        top_splitter.setStretchFactor(0, 0)
        top_splitter.setStretchFactor(1, 1)

        self.timeline_widget = QGraphicsView()
        self.timeline_scene = QGraphicsScene()
        self.timeline_widget.setScene(self.timeline_scene)
        self.timeline_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(self.timeline_widget)
        main_splitter.setStretchFactor(0, 2)
        main_splitter.setStretchFactor(1, 1)
        self.main_layout.addWidget(main_splitter)

        self.createTopToolbars()
        self.connect_buttons()

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
        action_icons = {'New': QStyle.SP_FileIcon, 'Open': QStyle.SP_DialogOpenButton,
                       'Save': QStyle.SP_DialogSaveButton, 'Export': QStyle.SP_DialogYesButton}
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

    def resize_preview(self, event):
        if self.current_preview and self.timeline_manager.timeline_frames:
            self.update_preview_frame(self.timeline_manager.timeline_frames[self.current_frame_idx]["frame_idx"])
        event.accept()

    def update_preview_frame(self, frame_idx):
        if self.timeline_manager.timeline_frames:
            closest_frame = min(self.timeline_manager.timeline_frames, key=lambda x: abs(x["frame_idx"] - frame_idx))
            if self.current_preview:
                self.preview_scene.removeItem(self.current_preview)
            pixmap = closest_frame["item"].pixmap()
            preview_width = self.preview_widget.width()
            preview_height = self.preview_widget.height()
            scaled_pixmap = pixmap.scaled(preview_width, preview_height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            self.current_preview = self.preview_scene.addPixmap(scaled_pixmap)
            self.current_preview.setPos(0, 0)
            self.current_frame_idx = self.timeline_manager.timeline_frames.index(closest_frame)
            self.last_frame_idx = frame_idx
            self.preview_scene.setSceneRect(0, 0, preview_width, preview_height)

    def animate_frame(self):
        if self.timeline_manager.timeline_frames:
            self.current_frame_idx = (self.current_frame_idx + 1) % len(self.timeline_manager.timeline_frames)
            frame = self.timeline_manager.timeline_frames[self.current_frame_idx]
            if self.current_preview:
                self.preview_scene.removeItem(self.current_preview)
            pixmap = frame["item"].pixmap()
            preview_width = self.preview_widget.width()
            preview_height = self.preview_widget.height()
            scaled_pixmap = pixmap.scaled(preview_width, preview_height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            self.current_preview = self.preview_scene.addPixmap(scaled_pixmap)
            self.current_preview.setPos(0, 0)
            self.preview_scene.setSceneRect(0, 0, preview_width, preview_height)

    def connect_buttons(self):
        self.play_btn.clicked.connect(self.play_video)
        self.pause_btn.clicked.connect(self.pause_video)
        self.cut_btn.clicked.connect(self.start_cutting)
        self.confirm_cut_btn.clicked.connect(self.cut_video)
        self.cancel_cut_btn.clicked.connect(self.cancel_cutting)
        self.export_btn.clicked.connect(self.video_processor.export_video)

    def play_video(self):
        if self.timeline_manager.timeline_frames:
            self.animation_timer.start(103)

    def pause_video(self):
        if self.animation_timer.isActive():
            self.animation_timer.stop()
            if self.timeline_manager.timeline_frames and self.current_preview:
                frame = self.timeline_manager.timeline_frames[self.current_frame_idx]
                self.preview_scene.removeItem(self.current_preview)
                pixmap = frame["item"].pixmap()
                preview_width = self.preview_widget.width()
                preview_height = self.preview_widget.height()
                scaled_pixmap = pixmap.scaled(preview_width, preview_height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                self.current_preview = self.preview_scene.addPixmap(scaled_pixmap)
                self.current_preview.setPos(0, 0)
                self.preview_scene.setSceneRect(0, 0, preview_width, preview_height)

    def start_cutting(self):
        if self.video_processor.capture is None or not self.video_processor.capture.isOpened():
            QMessageBox.warning(self, "Error", "Please import a video first.")
            return
        if not self.is_cutting:
            self.is_cutting = True
            self.cut_start_frame = None
            self.cut_end_frame = None
            self.confirm_cut_btn.setEnabled(False)
            self.cancel_cut_btn.setEnabled(True)  # Активируем кнопку отмены
            QMessageBox.information(self, "Cutting Mode", "Click on the timeline to set the start frame, then the end frame.")
        else:
            QMessageBox.warning(self, "Cutting Mode", "Already in cutting mode. Select frames or cancel first.")

    def cut_video(self):
        if self.cut_start_frame is None or self.cut_end_frame is None:
            QMessageBox.warning(self, "Error", "Please set both start and end frames for cutting.")
            return
        if self.cut_start_frame > self.cut_end_frame:
            self.cut_start_frame, self.cut_end_frame = self.cut_end_frame, self.cut_start_frame
        self.video_processor.cut_video(self.cut_start_frame, self.cut_end_frame)
        self.cut_start_frame = None
        self.cut_end_frame = None
        self.is_cutting = False
        self.confirm_cut_btn.setEnabled(False)
        self.cancel_cut_btn.setEnabled(False)

    def cancel_cutting(self):
        if self.is_cutting:
            self.is_cutting = False
            self.cut_start_frame = None
            self.cut_end_frame = None
            self.confirm_cut_btn.setEnabled(False)
            self.cancel_cut_btn.setEnabled(False)
            QMessageBox.information(self, "Cutting Mode", "Cutting mode canceled.")