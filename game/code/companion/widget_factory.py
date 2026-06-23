# widget_factory.py
from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPixmap

class WidgetFactory:
    @staticmethod
    def create_widget(element_data):
        # Use element_kind instead of type to avoid reserved keyword issues
        kind = element_data.get("element_kind")
        
        if kind == "label":
            return QLabel(element_data.get("text", ""))
            
        elif kind == "sprite":
            widget = QLabel()
            pixmap = QPixmap(element_data.get("asset_path", ""))
            if not pixmap.isNull():
                widget.setPixmap(pixmap)
                widget.setScaledContents(True) # Force it to show the image
                widget.setFixedSize(pixmap.size()) # Ensure it doesn't shrink to 0
            widget.setStyleSheet("border: 2px solid red;")
            return widget
            
        return None