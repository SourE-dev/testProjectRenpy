from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter
from utils import log_debug

class MessageWindow(QWidget):
    """
    A 'Dumb' UI Container. 
    It no longer handles effect initialization or timers.
    It only displays what is passed to it.
    """
    def __init__(self, text, options=None):
        super().__init__()
        self.options = options or {}
        self.sprite_frame = None 
        
        # Window flags
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        if self.options.get("click_through", False):
            flags = Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint | \
                    Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowTransparentForInput
        else:
            flags = Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint | \
                    Qt.WindowType.FramelessWindowHint
        self.setWindowFlags(flags)

        # Handle initialization differently based on type
        if "frame_w" in self.options:
            self.setFixedSize(self.options["frame_w"], self.options["frame_h"])
            # No setup_ui(text) here because it's a sprite
        else:
            self.setup_ui(text)
   

    def update_frame(self, pixmap):
        """Called by the external Effect/Animation component."""
        self.sprite_frame = pixmap
        self.update() 

    def paintEvent(self, event):
        if self.sprite_frame and not self.sprite_frame.isNull():
            painter = QPainter(self)
            painter.drawPixmap(0, 0, self.sprite_frame)
        else:
            super().paintEvent(event)

    def setup_ui(self, text):
        """Initializes the text-based UI with dynamic background/transparency."""
        # 1. Parse Options
        bg_hex = self.options.get("bg_color", "#1E1E1E")
        opacity = self.options.get("opacity", 1.0) # 0.0 to 1.0
        border_color = self.options.get("border_color", "#555555")
        min_w = self.options.get("min_width", 0)
        min_h = self.options.get("min_height", 0)
        # 2. Convert Hex to RGBA
        hex_color = bg_hex.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        alpha_int = int(opacity * 255)
        bg_rgba = f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha_int})"
        
        # 3. Apply Style
        style = f"""
            QLabel {{
                padding: 20px; 
                border-radius: 15px; 
                font-size: 20px; 
                font-weight: bold;
                background-color: {bg_rgba}; 
                border: 2px solid {border_color}; 
                color: white;
            }}
        """
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel(text)
        
        # APPLY CONSTRAINTS:
        if min_w > 0: self.label.setMinimumWidth(min_w)
        if min_h > 0: self.label.setMinimumHeight(min_h)
        
        self.label.setStyleSheet(style)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self.setLayout(layout)