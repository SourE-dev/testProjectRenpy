from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter
from utils import log_debug # Ensure this is imported
# Corrected Imports
from registry import get_effect_class
from base import BaseEffect
from effects import AnimatedEffect # Import this for isinstance check

class MessageWindow(QWidget):
    def __init__(self, text, effect="default", options=None):
        super().__init__()
        self.options = options or {}
        self.is_active = True
        # 1. Fetch config first to find out what "class" it is
        # Note: You need a way to access get_effect_config here.
        # You might need to pass the config object in, or use a global helper.
        from registry import get_effect_class # Ensure this is your registry import
        
        # 2. Determine the class based on the "class" key in options
        # Since final_options is already merged, it contains 'class': 'animated'
        class_type = self.options.get("class", "basic") 
        effect_class = get_effect_class(class_type) 
        
        log_debug(f"DEBUG: Selected class {class_type} -> {effect_class}")
        
        self.effect = effect_class(options=self.options)
   
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

        effect_type_name = self.effect.__class__.__name__
        is_animated = (effect_type_name == "AnimatedEffect")

        log_debug(f"DEBUG: Effect type name is: {effect_type_name}")
        
        if is_animated:
            log_debug(f"DEBUG: window_base.py sees DISPLAY_W as {self.effect.DISPLAY_W}")
            self.setFixedSize(self.effect.DISPLAY_W, self.effect.DISPLAY_H)
            self.setLayout(QVBoxLayout())
        else:
            log_debug(f"DEBUG: Falling back to setup_ui for effect '{effect}'")
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