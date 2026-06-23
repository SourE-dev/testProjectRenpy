from utils import log_debug
from PyQt6.QtCore import QTimer

class AnimationComponent:
    def __init__(self, frames, interval):
        self.frames = frames
        self.interval = interval
        self.timer = QTimer()
        self.current_frame = 0
        log_debug(f"AnimationComponent: Initialized with {len(frames)} frames, {interval}ms interval.")

    def start(self, widget, callback):
        log_debug("AnimationComponent: Starting timer.")
        self.timer.timeout.connect(lambda: callback(self.get_next_frame(widget)))
        self.timer.start(self.interval)

    def get_next_frame(self, widget):
        # We avoid logging inside this method to prevent console spam
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        return self.frames[self.current_frame]

class MovementComponent:
    def __init__(self, controller):
        self.controller = controller
        self.timer = QTimer()
        log_debug("MovementComponent: Initialized.")

    def start(self, widget):
        log_debug("MovementComponent: Starting movement timer at 20ms interval.")
        self.timer.timeout.connect(lambda: self.controller.update(widget))
        self.timer.start(20)