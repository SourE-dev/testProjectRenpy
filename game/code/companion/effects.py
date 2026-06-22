import os
import math
from PyQt6.QtCore import QTimer, QThreadPool
from PyQt6 import sip # Use this for all Qt memory safety checks
from PyQt6.QtWidgets import QApplication
from sprite_loader import ImageLoader
from utils import get_asset_path


# --- Strategy Pattern Interface ---
class MovementController:
    def update(self, widget):
        """Logic to move the widget. Returns True if movement is complete."""
        raise NotImplementedError

    def get_start_pos(self):
        """Returns the starting (x, y) coordinates of the movement."""
        raise NotImplementedError

# --- Concrete Strategy: Linear Movement ---
class LinearMovement(MovementController):
    def __init__(self, start_pos=(0, 0), end_pos=(500, 500), speed=5):
        self.start_pos = start_pos  # Store this for get_start_pos
        self.current_pos = [float(start_pos[0]), float(start_pos[1])]
        self.end_pos = end_pos
        self.speed = speed
        
    def get_start_pos(self):
        return self.start_pos

    def update(self, widget):
        dx = self.end_pos[0] - self.current_pos[0]
        dy = self.end_pos[1] - self.current_pos[1]
        dist = (dx**2 + dy**2)**0.5
        
        if dist > self.speed:
            self.current_pos[0] += (dx / dist) * self.speed
            self.current_pos[1] += (dy / dist) * self.speed
            widget.move(int(self.current_pos[0]), int(self.current_pos[1]))
            return False 
        else:
            widget.move(self.end_pos[0], self.end_pos[1])
            return True 

# --- Concrete Strategy: Cosine Path Movement ---
class CosinePathMovement(MovementController):
    def __init__(self, start_x=0, end_x=500, amplitude=50, frequency=0.05, start_y=500):
        self.start_x = start_x # Store this for get_start_pos
        self.start_y = start_y
        self.x = float(start_x)
        self.end_x = float(end_x)
        self.amp = amplitude
        self.freq = frequency

    def get_start_pos(self):
        # Calculate Y based on initial X to ensure perfect placement
        initial_y = self.start_y + math.cos(self.start_x * self.freq) * self.amp
        return (int(self.start_x), int(initial_y))

    def update(self, widget):
        self.x += 5 # Move speed increment
        y = self.start_y + math.cos(self.x * self.freq) * self.amp
        widget.move(int(self.x), int(y))
        return self.x >= self.end_x
class BaseEffect:
    def __init__(self, options=None):
        self.options = options or {}
    def apply_style(self, widget):
        return "color: white; background-color: rgba(0,0,0,180);"
    def start_animation(self, widget):
        pass
    def cleanup(self, widget):
        """Default cleanup for non-animated windows."""
        widget.hide()
        widget.close()

class AnimatedEffect(BaseEffect):
    FRAME_W = 32
    FRAME_H = 32
    DISPLAY_W = 32 
    DISPLAY_H = 32
    COLS = 1
    TOTAL_FRAMES = 1
    FRAME_INTERVAL_MS = 200
    MOVE_INTERVAL_MS = 20 
    CONTROLLER_MAP = {
        "linear": LinearMovement,
        "cosine": CosinePathMovement
    }
    def __init__(self, options=None):
        super().__init__(options)
        self.DISPLAY_W = self.options.get("scale_w", self.DISPLAY_W)
        self.DISPLAY_H = self.options.get("scale_h", self.DISPLAY_H)

    def start_animation(self, widget):
        widget.hide()

        
        loader = ImageLoader(self, get_asset_path) 
        loader.signals.finished.connect(lambda frames: self.on_frames_ready(frames, widget))
        QThreadPool.globalInstance().start(loader)

    def on_frames_ready(self, frames, widget):
        self.frames = frames
        self.current_frame = 0
        
        # 1. Handle Static Positioning (Fallback)
        # If no movement_type is set, we check for 'pos'. 
        # If no 'pos' is set, we default to center screen.
        pos = self.options.get("pos")
        if not self.options.get("movement_type"):
            if pos:
                widget.move(pos[0], pos[1])
            else:
                screen_geo = QApplication.primaryScreen().availableGeometry()
                widget.move(int(screen_geo.width() / 2), int(screen_geo.height() / 2))

        # 2. Handle Movement (if requested)
        move_type = self.options.get("movement_type")
        if move_type in self.CONTROLLER_MAP:
            params = self.options.get("movement_params", {})
            try:
                self.movement_controller = self.CONTROLLER_MAP[move_type](**params)
                
                # Set initial position based on controller
                if hasattr(self.movement_controller, 'get_start_pos'):
                    start = self.movement_controller.get_start_pos()
                    widget.move(start[0], start[1])
                
                self.move_timer = QTimer()
                self.move_timer.timeout.connect(lambda: self.run_movement(widget))
                self.move_timer.start(self.MOVE_INTERVAL_MS)
            except TypeError as e:
                print(f"Error initializing {move_type}: {e}")

        # 3. Show widget only after positioning is finalized
        widget.show()
        
        # Start Animation
        self.frame_timer = QTimer()
        self.frame_timer.timeout.connect(lambda: self.next_frame(widget))
        self.frame_timer.start(self.FRAME_INTERVAL_MS)
        self.next_frame(widget)
    def run_movement(self, widget):
        # The ultimate check: is the C++ memory already freed?
        if sip.isdeleted(widget):
            self.cleanup(widget)
            return

        try:
            finished = self.movement_controller.update(widget)
            if finished:
                self.move_timer.stop()
                if self.options.get("auto_hide", True):
                    self.cleanup(widget)
        except RuntimeError:
            self.cleanup(widget)
    def cleanup(self, widget):
        # Stop timers first to prevent further signals
        if hasattr(self, 'frame_timer'): self.frame_timer.stop()
        if hasattr(self, 'move_timer'): self.move_timer.stop()
        
        # Only touch the widget if it hasn't been deleted yet
        if not sip.isdeleted(widget):
            widget.hide()
            widget.deleteLater()
    def next_frame(self, widget):
        widget.update_frame(self.frames[self.current_frame])
        self.current_frame = (self.current_frame + 1) % self.TOTAL_FRAMES


class FireballEffect(AnimatedEffect):
    SPRITE_PATH = "images/sprites/red_fireball.png"
    FRAME_W = 32
    FRAME_H = 32
    DISPLAY_W = 128
    DISPLAY_H = 128
    COLS = 2
    TOTAL_FRAMES = 2
