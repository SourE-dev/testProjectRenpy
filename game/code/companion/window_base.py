from utils import log_debug
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush

class MessageWindow(QWidget):
    def __init__(self, text="", options=None):
        super().__init__()
        self.options = options or {}
        
        # 1. Shell settings
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 2. Extract Styling Data
        self.bg_color = self.options.get("bg_color", None)
        # Handle border string (e.g., "2px solid #FFFFFF")
        border_str = self.options.get("border", "2px solid #555555")
        self.border_width = int(border_str.split('px')[0]) if 'px' in border_str else 2
        
        # 3. Layout setup
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10) # Added margin for border visibility
        self.content_layout = self.layout
        
        if text:
            self.label = QLabel(text)
            self.label.setStyleSheet("color: white; padding: 10px;")
            self.layout.addWidget(self.label)
        
        log_debug(f"MessageWindow: Initialized with bg_color={self.bg_color}")

    def paintEvent(self, event):
        """Custom painting to ensure background/border render with transparency."""
        if not self.bg_color:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw Background
        rect = self.rect().adjusted(self.border_width, self.border_width, -self.border_width, -self.border_width)
        painter.setBrush(QBrush(QColor(self.bg_color)))
        painter.setPen(QPen(QColor("#FFFFFF"), self.border_width)) # Or extract color from border_str
        
        painter.drawRoundedRect(rect, 15, 15)

    def update_text(self, new_text):
        if hasattr(self, 'label'):
            self.label.setText(new_text)
            self.adjustSize()