import time
import os
from PyQt6.QtCore import QRect, QTimer, Qt, QThreadPool
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication
from sprite_loader import ImageLoader
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
GAME_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))

def get_asset_path(relative_path):
    return os.path.join(GAME_DIR, relative_path)
class BaseEffect:
    def __init__(self, options=None):
        self.options = options or {}
    def apply_style(self, widget):
        return "color: white; background-color: rgba(0,0,0,180);"
    def start_animation(self, widget):
        pass


class AnimatedEffect(BaseEffect):
    # Default Configuration
    FRAME_W = 32
    FRAME_H = 32
    DISPLAY_W = 32 
    DISPLAY_H = 32
    COLS = 1
    TOTAL_FRAMES = 1
    FRAME_INTERVAL_MS = 200
    def __init__(self, options=None):
        super().__init__(options)
        # Check for dynamic overrides
        self.DISPLAY_W = self.options.get("scale_w", self.DISPLAY_W)
        self.DISPLAY_H = self.options.get("scale_h", self.DISPLAY_H)
    def start_animation(self, widget):
        # 1. Trigger the background loader instead of loading directly
        loader = ImageLoader(self)
        loader.signals.finished.connect(lambda frames: self.on_frames_ready(frames, widget))
        QThreadPool.globalInstance().start(loader)
        
        # NOTE: We do NOT start the timer or init_movement here 
        # because the frames aren't ready yet!

    def on_frames_ready(self, frames, widget):
        # 2. This runs on the UI thread once the background thread is done
        self.frames = frames
        self.current_frame = 0
        
        # 3. Setup Timer and Movement now that frames are ready
        self.frame_timer = QTimer()
        self.frame_timer.timeout.connect(lambda: self.next_frame(widget))
        self.frame_timer.start(self.FRAME_INTERVAL_MS)
        
        self.init_movement(widget)
        
        # Immediate first frame
        self.next_frame(widget)

    def next_frame(self, widget):
        # Now self.frames is guaranteed to exist
        widget.update_frame(self.frames[self.current_frame])
        self.current_frame = (self.current_frame + 1) % self.TOTAL_FRAMES
    def init_movement(self, widget):
        widget.move(500, 500)

    def cleanup(self, widget):
        if hasattr(self, 'frame_timer'):
            self.frame_timer.stop()
        widget.hide()
        widget.close()

class FireballEffect(AnimatedEffect):
    SPRITE_PATH = "images/sprites/red_fireball.png"
    FRAME_W = 32
    FRAME_H = 32
    DISPLAY_W = 128 # The size you want on screen
    DISPLAY_H = 128
    COLS = 2
    TOTAL_FRAMES = 2
    def init_movement(self, widget):
        # Override position if provided in Ren'Py
        pos = self.options.get("pos", None)
        if pos:
            widget.move(pos[0], pos[1])
        else:
            # Default center logic
            screen_geo = QApplication.primaryScreen().availableGeometry()
            widget.move(int(screen_geo.width() / 2), int(screen_geo.height() / 2))