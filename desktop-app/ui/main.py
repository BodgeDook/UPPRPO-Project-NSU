import os
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
# from styles import (apply_button_style, apply_disabled_button_style, apply_label_style,
#                     apply_title_style, apply_link_style, apply_window_style)
# from auth_window import AuthView  # for Login/Register

from hello_window import HelloView, HelloViewModel, HelloModel

if __name__ == '__main__':
    if os.getenv("DEVELOP_MACHINE"):
        print("Running on the development machine.")

    # QApplication.setAttribute(Qt.AA_MacUseFullKeyboardNavigation, True)
    app = QApplication(sys.argv)

    model = HelloModel()
    view_model = HelloViewModel(model)
    window = HelloView(view_model)

    window.show()
    sys.exit(app.exec_())