from utils import log_debug
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter

class MessageWindow(QWidget):
    def __init__(self, text, options=None):
        super().__init__()
        self.options = options or {}
        self.sprite_frame = None
        log_debug(f"MessageWindow: Initializing shell for text: '{text}'")
        
        # 1. Shell: Rigid Geometry Control
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # 2. Content: Layout Control
        self.content_widget = QWidget(self)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 3. Setup Initial UI
        self.label = None
        self.setup_ui(text)
        log_debug("MessageWindow: Shell initialization complete.")

    def resizeEvent(self, event):
        log_debug(f"MessageWindow: Resize event triggered. New size: {self.size().width()}x{self.size().height()}")
        self.content_widget.resize(self.size())
        super().resizeEvent(event)

    def setup_ui(self, text):
        log_debug(f"MessageWindow: Setting up UI elements.")
        bg_hex = self.options.get("bg_color", "#1E1E1E")
        style = f"background-color: {bg_hex}; border-radius: 15px; border: 2px solid #555555; color: white; padding: 10px;"
        
        self.label = QLabel(text)
        self.label.setStyleSheet(style)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.content_layout.addWidget(self.label)
        log_debug("MessageWindow: UI elements attached to content_layout.")

    def update_frame(self, pixmap):
        log_debug("MessageWindow: update_frame called from Animation component.")
        self.sprite_frame = pixmap
        self.update() 

    def paintEvent(self, event):
        # We limit the paintEvent logging to avoid log spamming during every frame of an animation
        if self.sprite_frame and not self.sprite_frame.isNull():
            painter = QPainter(self)
            painter.drawPixmap(0, 0, self.sprite_frame)
        else:
            super().paintEvent(event)