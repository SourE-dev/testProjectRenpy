# widgets/base.py
from PyQt6.QtCore import QTimer
from PyQt6 import sip
from utils import resolve_image_path
class BaseEffect:
    def __init__(self, options=None):
        self.options = options or {}
        raw_path = self.options.get("image_path", "default")
        self.IMAGE_PATH = resolve_image_path(raw_path)
    def apply_style(self, widget):
        return "color: white; background-color: rgba(0,0,0,180);"
        
    def start_animation(self, widget):
        pass
        
    def cleanup(self, widget):
        if not sip.isdeleted(widget):
            widget.hide()
            widget.close()