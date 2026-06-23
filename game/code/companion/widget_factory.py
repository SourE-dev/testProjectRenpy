from utils import log_debug
from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPixmap

class WidgetFactory:
    @staticmethod
    def create_widget(element_data):
        kind = element_data.get("element_kind")
        eid = element_data.get("logical_id", "unknown")
        log_debug(f"WidgetFactory: Attempting to create widget [{eid}] of kind: {kind}")
        
        if kind == "label":
            text = element_data.get("text", "")
            log_debug(f"WidgetFactory: Creating label [{eid}] with text: '{text}'")
            return QLabel(text)
            
        elif kind == "sprite":
            asset_path = element_data.get("asset_path", "")
            log_debug(f"WidgetFactory: Creating sprite [{eid}] from path: '{asset_path}'")
            
            widget = QLabel()
            pixmap = QPixmap(asset_path)
            
            if not pixmap.isNull():
                log_debug(f"WidgetFactory: Successfully loaded asset for [{eid}]")
                widget.setPixmap(pixmap)
                widget.setScaledContents(True)
                widget.setFixedSize(pixmap.size())
            else:
                log_debug(f"WidgetFactory: ERROR: Failed to load pixmap for [{eid}] at path: '{asset_path}'")
            
            widget.setStyleSheet("border: 2px solid red;")
            return widget
            
        log_debug(f"WidgetFactory: Unknown element_kind '{kind}' for [{eid}]. Returning None.")
        return None