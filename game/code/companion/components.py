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
        self._raw_pixmap = QPixmap()
        self._load_and_start(self.asset_path)

    def _load_and_start(self, path):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.normpath(os.path.join(base_dir, "..", "..", path))
        
        self._raw_pixmap = QPixmap(full_path)
        if not self._raw_pixmap.isNull():
            self.frames = [self._raw_pixmap]
            self.label.setPixmap(self.frames[0])
            self.label.resize(self._raw_pixmap.size())
            self.resize(self._raw_pixmap.size())
            self.timer.start(int(self.options.get("frame_interval", 200)))
        else:
            log_debug(f"SpriteWidget: Failed to load {full_path}")
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._raw_pixmap.isNull():
            # Scale smoothly to fit whatever size the animation strategy dictates
            scaled_pixmap = self._raw_pixmap.scaled(
                self.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.label.setPixmap(scaled_pixmap)
            self.label.resize(self.size())

    def _next_frame(self):
        if self.frames:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.label.setPixmap(self.frames[self.current_frame])
# --- UPDATE THIS INSIDE components.py ---

class TextWidget(BaseComponent):
    """A clean typography layout element managed by the parent container layout with deep telemetry tracking."""
    def __init__(self, text, options=None, parent=None):
        super().__init__(options)
        log_debug(f"\n--- [TEXT COMPONENT LIFECYCLE: INIT] ---------------------------")
        log_debug(f" - Text Payload: '{text}'")
        log_debug(f" - Stated Options dict: {self.options}")
        
        if parent:
            self.setParent(parent)
            log_debug(f" - Parent Bound on Init: {parent.__class__.__name__} (Live Size: {parent.width()}x{parent.height()})")
            
        # Clean spacing layout initialization
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0) # Explicitly eliminate default internal layout padding
        
        self.label = QLabel(text)
        
        font = QFont("Consolas", 14, QFont.Weight.Bold)
        self.label.setFont(font)
        self.label.setStyleSheet("color: #FFFFFF; background: transparent;")
        self.label.setWordWrap(True)
        
        # Align Top-Left by default so relative geometry bounding boxes position text perfectly
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        self.layout.addWidget(self.label)
        log_debug(f" - Widget Core Built. Live Label Geometry: {self.label.geometry()}")
        log_debug(f"----------------------------------------------------------------")

    def update_text(self, text):
        log_debug(f"TEXT COMPONENT: Updating text buffer string payload -> '{text}'")
        self.label.setText(text)
        
    def apply_styles(self, options):
        self.options = options
        log_debug(f"TEXT COMPONENT: Hot-swapping styles configuration. Current keys: {list(options.keys())}")
        if "msg" in options:
            self.update_text(options["msg"])
            
        if "align" in options:
            log_debug(f" - Typography alignment override detected: '{options['align']}'")
            if options["align"] == "center":
                self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            elif options["align"] == "right":
                self.label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

    # DIAGNOSTIC INTERCEPTION HOOK
    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        # Capture exactly what sizing metrics are handed down across frame updates
        old_size = event.oldSize()
        new_size = event.size()
        parent_widget = self.parentWidget()
        parent_info = f"{parent_widget.width()}x{parent_widget.height()}" if parent_widget else "None"
        
        log_debug(
            f"\n=== [TEXT COMPONENT LAYOUT TELEMETRY] =========================\n"
            f" - Target Widget ID: {self.property('logical_id') or 'Unassigned'}\n"
            f" - Resizing Event Loop Triggered:\n"
            f"   * Old Footprint Size: {old_size.width()}x{old_size.height()}\n"
            f"   * New Target Canvas Size: {new_size.width()}x{new_size.height()}\n"
            f" - Current Parent Context Size: {parent_info}\n"
            f" - Active Anchor Tracking Policies:\n"
            f"   * ANCHOR_POLICY Cached Flag: {self.property('ANCHOR_POLICY')}\n"
            f"   * BOTTOM_MARGIN Cached Flag: {self.property('BOTTOM_MARGIN')}\n"
            f" - Internal Label Geometry Post-Fit: {self.label.geometry()}\n"
            f"================================================================"
        )
        
        # Enforce exact bounding match tracking layouts
        self.label.resize(self.size())