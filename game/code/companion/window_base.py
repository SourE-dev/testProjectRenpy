from utils import log_debug
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter

class MessageWindow(QWidget):
    def __init__(self, text, options=None):
        super().__init__()
        self.options = options or {}
        self.sprite_frame = None
        
        # 1. Shell: Rigid Geometry Control
        # Tool window + Frameless prevents taskbar icons and OS chrome
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # 2. Content: Layout Control
        # This inner widget handles the stacking of labels/sprites/children
        self.content_widget = QWidget(self)
        self.layout = QVBoxLayout(self.content_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 3. Setup Initial UI
        self.label = None
        self.setup_ui(text)

    def resizeEvent(self, event):
        # Ensure the content area always matches the shell dimensions
        self.content_widget.resize(self.size())
        super().resizeEvent(event)

    def setup_ui(self, text):
        bg_hex = self.options.get("bg_color", "#1E1E1E")
        # Ensure style is applied correctly to the label
        style = f"background-color: {bg_hex}; border-radius: 15px; border: 2px solid #555555; color: white; padding: 10px;"
        
        self.label = QLabel(text)
        self.label.setStyleSheet(style)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # CRITICAL: Add to the content_widget's layout, not the shell itself
        self.layout.addWidget(self.label)

    def update_frame(self, pixmap):
        """Called by the external Effect/Animation component."""
        self.sprite_frame = pixmap
        self.update() 

    def paintEvent(self, event):
        # The Shell draws the animation (if any) or remains transparent/filled
        if self.sprite_frame and not self.sprite_frame.isNull():
            painter = QPainter(self)
            painter.drawPixmap(0, 0, self.sprite_frame)
        else:
            super().paintEvent(event)