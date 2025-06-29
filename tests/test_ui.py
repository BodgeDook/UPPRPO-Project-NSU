# tests/test_ui.py
import sys
import os
# adding the root directory of the project in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QMainWindow, QGraphicsScene, QPushButton
from ui.video_editor import VideoEditor
from ui.video_processor import VideoProcessor
from ui.timeline_manager import TimelineManager

'''
to launch tests:
pytest tests/test_ui.py -v
'''

# Мок для cv2.VideoCapture
@pytest.fixture
def mock_video_capture():
    with patch('cv2.VideoCapture') as mock_capture:
        mock_instance = mock_capture.return_value
        mock_instance.isOpened.return_value = True
        mock_instance.get.side_effect = lambda x: 30 if x == 5 else 1280 if x == 3 else 720 if x == 4 else 1  # FPS, width, height, frame count
        mock_instance.read.return_value = (True, Mock())  # Эмуляция успешного чтения кадра
        yield mock_instance

# Тест 1: Проверка инициализации VideoEditor
def test_video_editor_init():
    editor = VideoEditor()
    assert isinstance(editor, QMainWindow)
    assert isinstance(editor.play_btn, QPushButton)
    assert isinstance(editor.timeline_manager, TimelineManager)
    assert editor.is_cutting is False

# Тест 2: Проверка импорта видео в VideoProcessor
def test_video_processor_export_video(mock_video_capture):
    editor = VideoEditor()
    processor = VideoProcessor(editor)
    processor.export_video()
    assert mock_video_capture.called
    assert editor.timeline_manager.generate_timeline_frames.called

# Тест 3: Проверка генерации таймлайна
def test_timeline_manager_generate_frames(mock_video_capture):
    editor = VideoEditor()
    timeline = TimelineManager(editor)
    timeline.setup()
    timeline.generate_timeline_frames()
    assert len(timeline.timeline_frames) > 0
    assert isinstance(timeline.timeline_frames[0]["item"], QGraphicsScene.GraphicsItem)

# Тест 4: Проверка обновления превью при клике
def test_timeline_manager_update_preview(mock_video_capture):
    editor = VideoEditor()
    timeline = TimelineManager(editor)
    timeline.setup()
    timeline.generate_timeline_frames()
    event = Mock()
    event.pos.return_value = Mock(x=100)
    with patch.object(editor, 'frameUpdated') as mock_signal:
        timeline.update_preview(event)
        mock_signal.emit.assert_called_once()

# Тест 5: Проверка старта воспроизведения
def test_video_editor_play_video(mock_video_capture):
    editor = VideoEditor()
    editor.timeline_manager.generate_timeline_frames()
    with patch.object(editor.animation_timer, 'start') as mock_start:
        editor.play_video()
        mock_start.assert_called_once_with(103)

# Тест 6: Проверка паузы воспроизведения
def test_video_editor_pause_video(mock_video_capture):
    editor = VideoEditor()
    editor.timeline_manager.generate_timeline_frames()
    editor.current_preview = Mock()
    with patch.object(editor.animation_timer, 'isActive', return_value=True):
        with patch.object(editor.animation_timer, 'stop') as mock_stop:
            editor.pause_video()
            mock_stop.assert_called_once()

# Тест 7: Проверка старта режима обрезки
def test_video_editor_start_cutting(mock_video_capture):
    editor = VideoEditor()
    editor.video_processor.capture = mock_video_capture
    editor.start_cutting()
    assert editor.is_cutting is True
    assert editor.cancel_cut_btn.isEnabled() is True

# Тест 8: Проверка отмены режима обрезки
def test_video_editor_cancel_cutting(mock_video_capture):
    editor = VideoEditor()
    editor.is_cutting = True
    editor.cancel_cutting()
    assert editor.is_cutting is False
    assert editor.cancel_cut_btn.isEnabled() is False

# Тест 9: Проверка обрезки видео
def test_video_processor_cut_video(mock_video_capture):
    editor = VideoEditor()
    processor = VideoProcessor(editor)
    processor.capture = mock_video_capture
    editor.cut_start_frame = 0
    editor.cut_end_frame = 10
    with patch('PyQt5.QtWidgets.QFileDialog.getSaveFileName', return_value=("test.mp4", None)):
        processor.cut_video(0, 10)
        assert mock_video_capture.set.called
        assert mock_video_capture.read.called

# Тест 10: Проверка обработки ошибки при отсутствии видео
def test_video_editor_start_cutting_no_video():
    editor = VideoEditor()
    with patch('PyQt5.QtWidgets.QMessageBox.warning') as mock_warning:
        editor.start_cutting()
        mock_warning.assert_called_once()
        assert "Please import a video first." in mock_warning.call_args[0][2]

if __name__ == "__main__":
    pytest.main([__file__])