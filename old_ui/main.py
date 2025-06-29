import sys
import cv2
from PyQt5.QtCore import Qt, QTimer, QSize, QUrl, QRectF, pyqtSignal, QObject
from PyQt5.QtGui import QKeySequence, QIcon, QPixmap, QImage, QPainter
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QToolBar, QAction, QProgressBar, QLabel, QSlider, QComboBox,
                             QGraphicsView, QGraphicsScene, QSplitter, QCheckBox, QStyle,
                             QUndoStack, QGroupBox, QPushButton, QSpinBox, QFileDialog, QTableWidget,
                             QTableWidgetItem, QSizePolicy, QMessageBox)
from PyQt5.QtGui import QDesktopServices

from styles import (apply_button_style, apply_disabled_button_style, apply_label_style,
                    apply_title_style, apply_link_style, apply_window_style, apply_welcome_window_style, theme_manager)
from settings_window import SettingsWindow

class VideoEditor(QMainWindow):
    frameUpdated = pyqtSignal(int)  # Signal for frame updates

    def __init__(self):
        super().__init__()

        self.capture = None  # For OpenCV VideoCapture
        self.timeline_frames = []  # List of timeline frames
        self.current_preview = None  # Current preview frame
        self.last_frame_idx = -1  # Track the last frame
        self.current_frame_idx = 0  # Current frame index for animation
        self.animation_timer = QTimer(self)  # Timer for animation
        self.animation_timer.timeout.connect(self.animate_frame)
        self.cut_start_frame = None  # Start frame for cutting
        self.cut_end_frame = None  # End frame for cutting
        self.is_cutting = False  # State to track cutting mode
        self.initUI()
        self.setupUndoRedo()
        self.setupAutosave()
        theme_manager.theme_changed.connect(self.update_theme)
        self.frameUpdated.connect(self.update_preview_frame)

    def initUI(self):
        self.play_btn   = QPushButton("Play")
        self.pause_btn  = QPushButton("Pause")
        self.cut_btn    = QPushButton("Start Cut")
        self.confirm_cut_btn = QPushButton("Confirm Cut")
        self.confirm_cut_btn.setEnabled(False)
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

        # Toolbox слева
        toolbox = QWidget()
        toolbox_layout = QVBoxLayout(toolbox)
        for btn in (self.play_btn, self.pause_btn, self.cut_btn, self.confirm_cut_btn, self.export_btn):
            apply_button_style(btn)
            toolbox_layout.addWidget(btn)
        toolbox.setFixedWidth(150)
        tools_panel = QWidget()
        tools_layout = QHBoxLayout(tools_panel)
        self.create_video_tools(tools_layout)
        self.create_audio_tools(tools_layout)
        tools_layout.addWidget(toolbox)
        tools_panel.setLayout(tools_layout)

        # Превью-окно с QGraphicsView
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

        # Timeline
        self.timeline_widget = QGraphicsView()
        self.timeline_scene  = QGraphicsScene()
        self.timeline_widget.setScene(self.timeline_scene)
        self.timeline_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(self.timeline_widget)
        main_splitter.setStretchFactor(0, 2)
        main_splitter.setStretchFactor(1, 1)
        self.main_layout.addWidget(main_splitter)

        self.createTopToolbars()
        self.connect_buttons()
        self.timeline_widget.resizeEvent = self.resize_timeline

    def generate_timeline_frames(self):
        self.timeline_scene.clear()
        self.timeline_frames.clear()
        if self.capture is None or not self.capture.isOpened():
            return
        width = self.timeline_widget.width() - 20
        height = self.timeline_widget.height() - 20
        if width <= 50 or height <= 50:
            return

        total_frames = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = self.capture.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 1
        frame_step = max(1, total_frames // 10)  # 10 frames for timeline

        for i in range(0, total_frames, frame_step):
            self.capture.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = self.capture.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_width = int(width // 10)
                frame_height = int(height - 20)
                frame = cv2.resize(frame, (frame_width, frame_height))
                image = QImage(frame.data, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(image)
                frame_item = self.timeline_scene.addPixmap(pixmap)
                x_pos = min((i / total_frames) * width, width - frame_width)
                frame_item.setPos(x_pos, 10)
                self.timeline_frames.append({"item": frame_item, "pos": x_pos, "frame_idx": i})
        self.timeline_scene.setSceneRect(0, 0, self.timeline_widget.width(), self.timeline_widget.height())

    def resize_timeline(self, event):
        if self.timeline_frames:
            self.generate_timeline_frames()
        event.accept()
    
    def export_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Video", "", "Video Files (*.mp4 *.avi)")
        if not file_path:
            return
        if self.capture:
            self.capture.release()
        self.capture = cv2.VideoCapture(file_path)
        self.generate_timeline_frames()
        if self.timeline_frames:
            self.current_frame_idx = 0
            self.update_preview_frame(self.timeline_frames[0]["frame_idx"])

    def resize_preview(self, event):
        if self.current_preview and self.timeline_frames:
            self.update_preview_frame(self.timeline_frames[self.current_frame_idx]["frame_idx"])
        event.accept()

    def update_preview_frame(self, frame_idx):
        if self.timeline_frames:
            closest_frame = min(self.timeline_frames, key=lambda x: abs(x["frame_idx"] - frame_idx))
            if self.current_preview:
                self.preview_scene.removeItem(self.current_preview)
            pixmap = closest_frame["item"].pixmap()
            preview_width = self.preview_widget.width()
            preview_height = self.preview_widget.height()
            scaled_pixmap = pixmap.scaled(preview_width, preview_height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            self.current_preview = self.preview_scene.addPixmap(scaled_pixmap)
            self.current_preview.setPos(0, 0)
            self.current_frame_idx = self.timeline_frames.index(closest_frame)
            self.last_frame_idx = frame_idx
            self.preview_scene.setSceneRect(0, 0, preview_width, preview_height)

    def update_preview(self, event):
        pos = event.pos()
        if self.timeline_frames and self.capture is not None and self.capture.isOpened():
            total_width = self.timeline_widget.width() - 20
            frame_idx = int((pos.x() / total_width) * self.capture.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_idx = min(max(0, frame_idx), int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT) - 1))
            self.frameUpdated.emit(frame_idx)
        event.accept()

    def mousePressEvent(self, event):
        if self.timeline_widget.underMouse():
            pos = self.timeline_widget.mapFromGlobal(event.globalPos())
            if self.timeline_frames and self.capture is not None and self.capture.isOpened():
                total_width = self.timeline_widget.width() - 20
                frame_idx = int((pos.x() / total_width) * self.capture.get(cv2.CAP_PROP_FRAME_COUNT))
                frame_idx = min(max(0, frame_idx), int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT) - 1))
                self.frameUpdated.emit(frame_idx)
                if self.is_cutting:
                    if event.button() == Qt.LeftButton and self.cut_start_frame is None:
                        self.cut_start_frame = frame_idx
                        QMessageBox.information(self, "Cut Start", f"Set start frame: {frame_idx}")
                        self.confirm_cut_btn.setEnabled(True)
                    elif event.button() == Qt.LeftButton and self.cut_start_frame is not None and self.cut_end_frame is None:
                        self.cut_end_frame = frame_idx
                        QMessageBox.information(self, "Cut End", f"Set end frame: {frame_idx}")
        super().mousePressEvent(event)

    def connect_buttons(self):
        self.play_btn.clicked.connect(self.play_video)
        self.pause_btn.clicked.connect(self.pause_video)
        self.cut_btn.clicked.connect(self.start_cutting)
        self.confirm_cut_btn.clicked.connect(self.cut_video)
        self.export_btn.clicked.connect(self.export_video)
        self.timeline_widget.mouseMoveEvent = self.update_preview

    def animate_frame(self):
        if self.timeline_frames:
            self.current_frame_idx = (self.current_frame_idx + 1) % len(self.timeline_frames)
            frame = self.timeline_frames[self.current_frame_idx]
            if self.current_preview:
                self.preview_scene.removeItem(self.current_preview)
            pixmap = frame["item"].pixmap()
            preview_width = self.preview_widget.width()
            preview_height = self.preview_widget.height()
            scaled_pixmap = pixmap.scaled(preview_width, preview_height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            self.current_preview = self.preview_scene.addPixmap(scaled_pixmap)
            self.current_preview.setPos(0, 0)
            self.preview_scene.setSceneRect(0, 0, preview_width, preview_height)

    def play_video(self):
        if self.timeline_frames:
            self.animation_timer.start(103)  # ~10 FPS

    def pause_video(self):
        if self.animation_timer.isActive():
            self.animation_timer.stop()
            if self.timeline_frames and self.current_preview:
                frame = self.timeline_frames[self.current_frame_idx]
                self.preview_scene.removeItem(self.current_preview)
                pixmap = frame["item"].pixmap()
                preview_width = self.preview_widget.width()
                preview_height = self.preview_widget.height()
                scaled_pixmap = pixmap.scaled(preview_width, preview_height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                self.current_preview = self.preview_scene.addPixmap(scaled_pixmap)
                self.current_preview.setPos(0, 0)
                self.preview_scene.setSceneRect(0, 0, preview_width, preview_height)

    def start_cutting(self):
        if self.capture is None or not self.capture.isOpened():
            QMessageBox.warning(self, "Error", "Please import a video first.")
            return
        if not self.is_cutting:
            self.is_cutting = True
            self.cut_start_frame = None
            self.cut_end_frame = None
            self.confirm_cut_btn.setEnabled(False)
            QMessageBox.information(self, "Cutting Mode", "Click on the timeline to set the start frame, then the end frame.")
        else:
            QMessageBox.warning(self, "Cutting Mode", "Already in cutting mode. Select frames first.")

    def cut_video(self):
        if self.cut_start_frame is None or self.cut_end_frame is None:
            QMessageBox.warning(self, "Error", "Please set both start and end frames for cutting.")
            return

        if self.cut_start_frame > self.cut_end_frame:
            self.cut_start_frame, self.cut_end_frame = self.cut_end_frame, self.cut_start_frame

        output_path, _ = QFileDialog.getSaveFileName(self, "Save Cut Video", "", "Video Files (*.mp4 *.avi)")
        if not output_path:
            return

        fourcc = cv2.VideoWriter_fourcc(*'mp4v') # or 'XVID' для .avi
        fps = self.capture.get(cv2.CAP_PROP_FPS)
        width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        self.capture.set(cv2.CAP_PROP_POS_FRAMES, self.cut_start_frame)
        for frame_idx in range(self.cut_start_frame, self.cut_end_frame + 1):
            ret, frame = self.capture.read()
            if ret:
                out.write(frame)
            else:
                break

        out.release()
        QMessageBox.information(self, "Success", f"Video cut and saved to {output_path}")
        self.cut_start_frame = None
        self.cut_end_frame = None
        self.is_cutting = False
        self.confirm_cut_btn.setEnabled(False)

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
            self.rotation_buttonsp = self.rotation_buttons.addWidget(btn)
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    print("Application initialized")
    is_signed_in = True
    if is_signed_in:
        welcome_window = WelcomeWindowSigned()
    else:
        pass # welcome_window = WelcomeWindowUnsigned()
    welcome_window.show()
    print("Window shown, starting event loop")
    sys.exit(app.exec_())