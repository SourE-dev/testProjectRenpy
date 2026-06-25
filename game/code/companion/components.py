from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import QTimer, Qt, QRect
from PyQt6.QtGui import QPixmap, QFont
from utils import log_debug
import os
class BaseComponent(QWidget):
    """Base class for all UI elements to ensure consistency."""
    def __init__(self, options=None):
        super().__init__()
        self.options = options or {}
        # Ensure widgets don't have their own window borders/decorations
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
class SpriteWidget(BaseComponent):
    """A self-contained widget that handles its own animation and loading."""
    def __init__(self, options=None, parent=None):
        super().__init__(options) 
        if parent:
            self.setParent(parent) # Explicitly set the parent
        log_debug(f"SpriteWidget: Initializing with options={self.options}")
        
        self.asset_path = self.options.get("asset_path")
        if not self.asset_path:
            log_debug("SpriteWidget: Error - missing asset_path in options")
            return
            
        # REMOVED: self.layout = QVBoxLayout(self)
        # Instead, we use a single Label as the core of the widget
        self.label = QLabel(self)
        self.label.setContentsMargins(0, 0, 0, 0)
        
        self.frames = []
        self.current_frame = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._next_frame)
        
        self._load_and_start(self.asset_path)

    def _load_and_start(self, path):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.normpath(os.path.join(base_dir, "..", "..", path))
        
        pixmap = QPixmap(full_path)
        if not pixmap.isNull():
            self.frames = [pixmap]
            self.label.setPixmap(self.frames[0])
            self.label.resize(pixmap.size()) # Resize the label to fit the image
            self.resize(pixmap.size())       # Resize the widget to fit the image
            self.timer.start(int(self.options.get("frame_interval", 200)))
        else:
            log_debug(f"SpriteWidget: Failed to load {full_path}")

    def _next_frame(self):
        if self.frames:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.label.setPixmap(self.frames[self.current_frame])

class TextWidget(BaseComponent):
    """A clean typography layout element managed by the parent container layout."""
    def __init__(self, text, options=None, parent=None):
        super().__init__(options)
        if parent:
            self.setParent(parent)
            
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel(text)
        
        # Apply your baseline Consolas styling directly to the component label
        font = QFont("Consolas", 14, QFont.Weight.Bold)
        self.label.setFont(font)
        self.label.setStyleSheet("color: #FFFFFF;")
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.layout.addWidget(self.label)

    def update_text(self, text):
        self.label.setText(text)
        
    def apply_styles(self, options):
        self.options = options
        if "msg" in options:
            self.update_text(options["msg"])