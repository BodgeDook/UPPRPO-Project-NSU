# ui/video_processor.py
import cv2
from PyQt5.QtWidgets import QFileDialog, QMessageBox

class VideoProcessor:
    def __init__(self, editor):
        self.editor = editor
        self.capture = None

    def export_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self.editor, "Import Video", "", "Video Files (*.mp4 *.avi)")
        if not file_path:
            return
        if self.capture:
            self.capture.release()
        self.capture = cv2.VideoCapture(file_path)
        self.editor.timeline_manager.generate_timeline_frames()
        if self.editor.timeline_manager.timeline_frames:
            self.editor.current_frame_idx = 0
            self.editor.update_preview_frame(self.editor.timeline_manager.timeline_frames[0]["frame_idx"])

    def cut_video(self, start_frame, end_frame):
        output_path, _ = QFileDialog.getSaveFileName(self.editor, "Save Cut Video", "", "Video Files (*.mp4 *.avi)")
        if not output_path:
            return

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = self.capture.get(cv2.CAP_PROP_FPS)
        width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        self.capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        for frame_idx in range(start_frame, end_frame + 1):
            ret, frame = self.capture.read()
            if ret:
                out.write(frame)
            else:
                break

        out.release()
        QMessageBox.information(self.editor, "Success", f"Video cut and saved to {output_path}")