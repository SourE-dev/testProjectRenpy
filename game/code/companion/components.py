# components.py
from PyQt6.QtCore import QTimer
class AnimationComponent:
    def __init__(self, frames, interval):
        self.frames = frames
        self.interval = interval
        self.timer = QTimer()
        self.current_frame = 0

    def start(self, widget, callback):
        self.timer.timeout.connect(lambda: callback(self.get_next_frame(widget)))
        self.timer.start(self.interval)

class MovementComponent:
    def __init__(self, controller):
        self.controller = controller
        self.timer = QTimer()

    def start(self, widget):
        self.timer.timeout.connect(lambda: self.controller.update(widget))
        self.timer.start(20)