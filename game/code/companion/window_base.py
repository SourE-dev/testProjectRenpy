from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter

# Corrected Imports
from widgets.registry import get_effect_class
from widgets.base import BaseEffect
from widgets.effects import AnimatedEffect # Import this for isinstance check

class MessageWindow(QWidget):
    def __init__(self, text, effect="default", options=None):
        super().__init__()
        self.options = options or {}
        
  
        effect_class = get_effect_class(effect) 
        self.effect = effect_class(options=options)
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Window flags logic
        if self.options.get("click_through", False):
            flags = Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint | \
                    Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowTransparentForInput
        else:
            flags = Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint | \
                    Qt.WindowType.FramelessWindowHint
        self.setWindowFlags(flags)
        
        self.sprite_frame = None 

        if isinstance(self.effect, AnimatedEffect):
            self.setFixedSize(self.effect.DISPLAY_W, self.effect.DISPLAY_H)
            self.setLayout(QVBoxLayout())
        else:
            self.setup_ui(text)
            
        self.show()
        self.effect.start_animation(self)


    def update_frame(self, pixmap):
        self.sprite_frame = pixmap
        self.update() 

    def paintEvent(self, event):
        if self.sprite_frame and not self.sprite_frame.isNull():
            painter = QPainter(self)
            painter.drawPixmap(0, 0, self.sprite_frame)
        else:
            super().paintEvent(event)

    def setup_ui(self, text):
        base_style = """
            QLabel {
                padding: 20px; border-radius: 15px; font-size: 20px; font-weight: bold;
                background-color: rgba(30, 30, 30, 255); border: 2px solid #555555; color: white;
            }
        """
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(text)
        self.label.setStyleSheet(base_style + self.effect.apply_style(self))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.show()