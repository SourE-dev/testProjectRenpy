from utils import log_debug
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont

class MessageWindow(QWidget):
    def __init__(self, options=None):
        super().__init__()
        self.options = options or {}
        
        self._canonical_pos = QPoint(0, 0)
        self._shake_offset = QPoint(0, 0)
        self._loop_offset = QPoint(0, 0)
        
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        self.apply_styles(self.options)
        
        # REMOVED QVBoxLayout! The canvas is now a pure coordinate plane.

    def apply_styles(self, options):
        self.options = options
        raw_color = self.options.get("bg_color", "#2e2e2e") 
        self.bg_color = None if raw_color == "transparent" else raw_color
        
        self.border_str = self.options.get("border", "2px solid #555555")
        self.border_width = int(self.border_str.split('px')[0]) if 'px' in self.border_str else 2
        self.update()

    def update_window_geometry(self, x, y, w, h):
        self._canonical_pos = QPoint(x, y)
        self.setGeometry(x, y, w, h)
        self._compose_absolute_position()
        self.update()
    # In window_base.py inside MessageWindow
    def resizeEvent(self, event):
        """Natively catches any OS or QPropertyAnimation sizing updates."""
        super().resizeEvent(event)
        # If a tracking scene object is hooked up, force it to reflow child positions
        if hasattr(self, "lifecycle_owner") and self.lifecycle_owner:
            self.lifecycle_owner.recalculate_child_layouts()
    def _compose_absolute_position(self):
        self.move(self.canonicalPos + self._shake_offset + self._loop_offset)

    @pyqtProperty(QPoint)
    def canonicalPos(self):
        if self._canonical_pos == QPoint(0, 0) and self.pos() != QPoint(0, 0):
            return self.pos()
        return self._canonical_pos

    @canonicalPos.setter
    def canonicalPos(self, point):
        self._canonical_pos = point
        self._compose_absolute_position()

    @pyqtProperty(QPoint)
    def shakeOffset(self): return self._shake_offset

    @shakeOffset.setter
    def shakeOffset(self, point):
        self._shake_offset = point
        self._compose_absolute_position()

    @pyqtProperty(QPoint)
    def loop_offset(self): return self._loop_offset

    @loop_offset.setter
    def loop_offset(self, point):
        self._loop_offset = point
        self._compose_absolute_position()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.bg_color:
            rect = self.rect().adjusted(self.border_width, self.border_width, -self.border_width, -self.border_width)
            painter.setBrush(QBrush(QColor(self.bg_color)))
            
            pen_color = "#FFFFFF"
            pen_style = Qt.PenStyle.SolidLine
            if hasattr(self, 'border_str'):
                if "dashed" in self.border_str:
                    pen_style = Qt.PenStyle.DashLine
                if "#" in self.border_str:
                    pen_color = "#" + self.border_str.split("#")[-1]
                    
            painter.setPen(QPen(QColor(pen_color), self.border_width, pen_style))
            painter.drawRoundedRect(rect, 15, 15)