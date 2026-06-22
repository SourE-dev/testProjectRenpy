# widgets/effects.py
from PyQt6.QtCore import QTimer, QThreadPool, Qt
from PyQt6.QtWidgets import QApplication
from PyQt6 import sip
from base import BaseEffect
from movement import LinearMovement, CosinePathMovement
from sprite_loader import ImageLoader
from utils import get_asset_path, log_debug

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
        # Scale/Display size
        raw_scale = self.options.get("scale_w", "NOT_FOUND")
        log_debug(f"DEBUG: AnimatedEffect incoming scale_w: {raw_scale}")
        self.DISPLAY_W = self.options.get("scale_w", self.DISPLAY_W)
        self.DISPLAY_H = self.options.get("scale_h", self.DISPLAY_H)
        
        # NEW: Override frame dimensions if provided in options
        self.FRAME_W = self.options.get("frame_w", self.FRAME_W)
        self.FRAME_H = self.options.get("frame_h", self.FRAME_H)
        
        # Also useful to allow dynamic columns/total frames if needed
        self.COLS = self.options.get("cols", self.COLS)
        self.TOTAL_FRAMES = self.options.get("total_frames", self.TOTAL_FRAMES)
        log_debug(f"DEBUG: AnimatedEffect applied DISPLAY_W: {self.DISPLAY_W}")
    def start_animation(self, widget):
        widget.hide()

        
        loader = ImageLoader(self, get_asset_path) 
        loader.signals.finished.connect(lambda frames: self.on_frames_ready(frames, widget))
        QThreadPool.globalInstance().start(loader)
    def on_frames_ready(self, frames, widget):
        # 0. Safety Check: If the window was destroyed during the loading thread, abort.
        if sip.isdeleted(widget):
       
            log_debug(f"DEBUG: Widget {widget} was destroyed before frames loaded. Ignoring.")
            return
            

        self.frames = frames
        self.current_frame = 0
        
        # 1. Handle Static Positioning (Fallback)
        # If no movement_type is set, we check for 'pos'. 
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
            # Copy params to prevent modification of original options
            params = self.options.get("movement_params", {}).copy()
            
            # Convert JSON lists to Tuples for the MovementController
            if "start_pos" in params:
                params["start_pos"] = tuple(params["start_pos"])
            if "end_pos" in params:
                params["end_pos"] = tuple(params["end_pos"])

            try:
                self.movement_controller = self.CONTROLLER_MAP[move_type](**params)
                
                # Set initial position based on controller
                # In effects.py, inside on_frames_ready
                if hasattr(self.movement_controller, 'get_start_pos'):
                    start = self.movement_controller.get_start_pos()
                    
                    # CLAMPING: Ensure the widget is visible on screen
                    screen_geo = QApplication.primaryScreen().availableGeometry()
                    safe_x = max(0, min(start[0], screen_geo.width() - self.DISPLAY_W))
                    safe_y = max(0, min(start[1], screen_geo.height() - self.DISPLAY_H))
                    
                    log_debug(f"Moving widget to: ({safe_x}, {safe_y})")
                    widget.move(safe_x, safe_y)
                
                self.move_timer = QTimer()
                self.move_timer.timeout.connect(lambda: self.run_movement(widget))
                self.move_timer.start(self.MOVE_INTERVAL_MS)
            except Exception as e:
                import traceback
                print(f"Error initializing {move_type}: {e}")
                print(traceback.format_exc())
                self.cleanup(widget)
                return # Abort if movement controller fails

        # 3. Finalize and Show widget
        if not sip.isdeleted(widget):
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
    # In effects.py
    def next_frame(self, widget):
        # Check if widget is deleted OR marked inactive
        if sip.isdeleted(widget) or (hasattr(widget, 'is_active') and not widget.is_active):
            return
        widget.update_frame(self.frames[self.current_frame])
        self.current_frame = (self.current_frame + 1) % self.TOTAL_FRAMES