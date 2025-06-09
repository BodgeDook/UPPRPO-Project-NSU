# desktop-app/widgets/toolbox.py
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTabWidget, QSizePolicy

import json

class AssetItem:
    def __init__(self, name, type, thumbnail_path, template_path):
        self.name = name
        self.type = type
        self.thumbnail_path = thumbnail_path
        self.template_path = template_path
        self.selected = False

class ToolboxWidget(QWidget):
    tool_selected = pyqtSignal(str)  # “Select”, “Cut”, “Trim”, etc.
    asset_selected = pyqtSignal(AssetItem)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(300)  # Увеличим ширину для вкладок
        self.assets = []
        self.selected_item = None

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Добавляем вкладки
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.backgrounds_tab = QWidget()
        self.titles_tab = QWidget()
        self.transitions_tab = QWidget()

        self.tabs.addTab(self.backgrounds_tab, "Backgrounds")
        self.tabs.addTab(self.titles_tab, "Titles")
        self.tabs.addTab(self.transitions_tab, "Transitions")

        # Инициализируем вкладку Backgrounds с одним тестовым фоном
        self.init_backgrounds_tab()
        layout.addStretch(1)

    def init_backgrounds_tab(self):
        layout = QVBoxLayout(self.backgrounds_tab)
        # Тестовый JSON с одним фоном
        test_data = [
            {"name": "Solid Red", "type": "background", "thumbnail_path": "", "template_path": "templates/solid_red"}
        ]
        for item in test_data:
            asset = AssetItem(item["name"], item["type"], item["thumbnail_path"], item["template_path"])
            self.assets.append(asset)
        self.backgrounds_tab.setLayout(layout)

    def paintEvent(self, event):
        painter = QPainter(self.backgrounds_tab)
        w, h = self.backgrounds_tab.width(), self.backgrounds_tab.height()
        item_size = 100
        items_per_row = w // (item_size + 10)
        painter.fillRect(0, 0, w, h, QColor(30, 30, 30))

        for i, asset in enumerate(self.assets):
            row = i // items_per_row
            col = i % items_per_row
            x = col * (item_size + 10) + 10
            y = row * (item_size + 10) + 10

            # Рисуем прямоугольник (монотонный цвет вместо миниатюры)
            painter.fillRect(x, y, item_size, item_size, QColor(255, 0, 0) if asset.name == "Solid Red" else QColor(0, 0, 0))
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.drawText(x + 5, y + item_size - 5, asset.name)

            # Рамка при выборе
            if asset.selected:
                painter.setPen(QPen(QColor(0, 255, 0), 2))
                painter.drawRect(x, y, item_size, item_size)

    def mousePressEvent(self, event):
        if event.widget() != self.backgrounds_tab:
            return
        w, h = self.backgrounds_tab.width(), self.backgrounds_tab.height()
        item_size = 100
        items_per_row = w // (item_size + 10)
        x, y = event.x(), event.y()

        col = (x - 10) // (item_size + 10)
        row = (y - 10) // (item_size + 10)
        index = row * items_per_row + col

        if 0 <= index < len(self.assets):
            for asset in self.assets:
                asset.selected = False
            self.assets[index].selected = True
            self.selected_item = self.assets[index]
            self.asset_selected.emit(self.selected_item)
            self.update()

    # Существующие методы остаются
    def add_tool_button(self, tool_name):
        btn = QPushButton(tool_name)
        btn.clicked.connect(lambda: self.tool_selected.emit(tool_name))
        self.layout().addWidget(btn)