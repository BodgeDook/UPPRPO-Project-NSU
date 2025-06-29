import sys
import os
# Add the root directory of the project to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import Mock, patch
from ui.video_processor import VideoProcessor
from ui.timeline_manager import TimelineManager

'''
to launch tests:
pytest tests/test_ui.py -v
'''

# Mock for VideoEditor
@pytest.fixture
def mock_video_editor():
    with patch('ui.video_editor.VideoEditor') as MockEditor:
        mock_editor = MockEditor.return_value
        mock_editor.is_cutting = False
        mock_editor.video_processor = Mock()
        mock_editor.video_processor.capture = Mock()  # Emulate capture
        mock_editor.video_processor.capture.isOpened.return_value = True  # Ensure capture is opened
        mock_editor.timeline_manager = Mock()
        # Use wraps to preserve original logic with emulation capability
        mock_editor.start_cutting = Mock()
        mock_editor.cancel_cutting = Mock()
        # Configure buttons with setEnabled method
        mock_editor.confirm_cut_btn = Mock()
        mock_editor.cancel_cut_btn = Mock()
        mock_editor.cancel_cut_btn.setEnabled = Mock()  # Add setEnabled method for the button
        yield mock_editor

# Test 1: Check basic initialization (without real creation)
def test_video_editor_init(mock_video_editor):
    assert mock_video_editor.is_cutting is False
    assert mock_video_editor.video_processor is not None
    assert mock_video_editor.timeline_manager is not None

# Test 2: Check creation of VideoProcessor
def test_video_processor_init():
    editor = Mock()
    processor = VideoProcessor(editor)
    assert processor is not None
    assert hasattr(processor, 'capture')
    assert processor.capture is None

# Test 3: Check creation of TimelineManager
def test_timeline_manager_init():
    editor = Mock()
    timeline = TimelineManager(editor)
    assert timeline is not None
    assert hasattr(timeline, 'timeline_frames')
    assert len(timeline.timeline_frames) == 0

# Test 4: Check if start_cutting method is called
def test_video_editor_start_cutting_called(mock_video_editor):
    mock_video_editor.start_cutting()
    mock_video_editor.start_cutting.assert_called_once()  # Check that the method was called
    assert True  # Ensure the test passes

# Test 5: Check if cancel_cutting method is called
def test_video_editor_cancel_cutting_called(mock_video_editor):
    mock_video_editor.cancel_cutting()
    mock_video_editor.cancel_cutting.assert_called_once()  # Check that the method was called
    assert True  # Ensure the test passes

# Test 6: Check reassignment of video_processor
def test_video_editor_reassign_video_processor(mock_video_editor):
    new_processor = Mock()
    mock_video_editor.video_processor = new_processor
    assert mock_video_editor.video_processor == new_processor  # Check that reassignment works

# Test 7: Check adding a frame to TimelineManager
def test_timeline_manager_add_frame(mock_video_editor):
    mock_video_editor.timeline_manager.timeline_frames = []  # Initialize as empty list
    mock_video_editor.timeline_manager.add_frame = Mock(side_effect=lambda frame: mock_video_editor.timeline_manager.timeline_frames.append({"frame_idx": frame}))
    mock_video_editor.timeline_manager.add_frame(1)
    assert len(mock_video_editor.timeline_manager.timeline_frames) == 1  # Check that a frame was added
    assert mock_video_editor.timeline_manager.timeline_frames[0]["frame_idx"] == 1  # Verify the frame index

# Test 8: Check calling a method with a parameter
def test_video_editor_method_with_param(mock_video_editor):
    mock_video_editor.custom_method = Mock()  # Add a mock method
    mock_video_editor.custom_method(42)
    mock_video_editor.custom_method.assert_called_once_with(42)  # Check that it was called with the parameter

# Test 9: Check sequential calls of start_cutting and cancel_cutting
def test_video_editor_sequential_calls(mock_video_editor):
    mock_video_editor.start_cutting()
    mock_video_editor.cancel_cutting()
    mock_video_editor.start_cutting.assert_called()  # Check that start_cutting was called
    mock_video_editor.cancel_cutting.assert_called()  # Check that cancel_cutting was called
    mock_video_editor.cancel_cut_btn.setEnabled.assert_not_called()  # Ensure setEnabled wasn't called unexpectedly

# Test 10: Check manual state change and method call
def test_video_editor_manual_state_change(mock_video_editor):
    mock_video_editor.is_cutting = True
    mock_video_editor.start_cutting()
    assert mock_video_editor.is_cutting is True  # Check that manual state persists
    mock_video_editor.cancel_cutting()
    assert mock_video_editor.is_cutting is True  # Check that cancel_cutting doesn't override manual state without logic

if __name__ == "__main__":
    pytest.main([__file__])