# ui/timeline_manager.py
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
import cv2
from PyQt5.QtWidgets import QMessageBox

class TimelineManager:
    def __init__(self, editor):
        self.editor = editor
        self.timeline_frames = []
        self.timeline_widget = None
        self.timeline_scene = None

    def setup(self):
        self.timeline_widget = self.editor.timeline_widget
        self.timeline_scene = self.editor.timeline_scene
        self.timeline_widget.mousePressEvent = self.mousePressEvent
        self.timeline_widget.mouseMoveEvent = self.update_preview

    def generate_timeline_frames(self):
        if self.timeline_scene is None or self.timeline_widget is None:
            return
        self.timeline_scene.clear()
        self.timeline_frames.clear()
        if self.editor.video_processor.capture is None or not self.editor.video_processor.capture.isOpened():
            return
        width = self.timeline_widget.width() - 20
        height = self.timeline_widget.height() - 20
        if width <= 50 or height <= 50:
            return

        total_frames = int(self.editor.video_processor.capture.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = self.editor.video_processor.capture.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 1
        frame_step = max(1, total_frames // 10)

        for i in range(0, total_frames, frame_step):
            self.editor.video_processor.capture.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = self.editor.video_processor.capture.read()
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

    def update_preview(self, event):
        if self.timeline_widget is None or self.timeline_scene is None:
            return
        pos = event.pos()
        if self.timeline_frames and self.editor.video_processor.capture is not None and self.editor.video_processor.capture.isOpened():
            total_width = self.timeline_widget.width() - 20
            frame_idx = int((pos.x() / total_width) * self.editor.video_processor.capture.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_idx = min(max(0, frame_idx), int(self.editor.video_processor.capture.get(cv2.CAP_PROP_FRAME_COUNT) - 1))
            self.editor.frameUpdated.emit(frame_idx)
        event.accept()

    def mousePressEvent(self, event):
        if self.timeline_widget is None or not self.timeline_widget.underMouse():
            return
        pos = self.timeline_widget.mapFromGlobal(event.globalPos())
        if self.timeline_frames and self.editor.video_processor.capture is not None and self.editor.video_processor.capture.isOpened():
            total_width = self.timeline_widget.width() - 20
            frame_idx = int((pos.x() / total_width) * self.editor.video_processor.capture.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_idx = min(max(0, frame_idx), int(self.editor.video_processor.capture.get(cv2.CAP_PROP_FRAME_COUNT) - 1))
            self.editor.frameUpdated.emit(frame_idx)
            if self.editor.is_cutting:
                if event.button() == Qt.LeftButton and self.editor.cut_start_frame is None:
                    self.editor.cut_start_frame = frame_idx
                    QMessageBox.information(self.editor, "Cut Start", f"Set start frame: {frame_idx}")
                    self.editor.confirm_cut_btn.setEnabled(True)
                elif event.button() == Qt.LeftButton and self.editor.cut_start_frame is not None and self.editor.cut_end_frame is None:
                    self.editor.cut_end_frame = frame_idx
                    QMessageBox.information(self.editor, "Cut End", f"Set end frame: {frame_idx}")
        event.accept()