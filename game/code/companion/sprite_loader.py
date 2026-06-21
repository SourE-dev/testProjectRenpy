import os
from PyQt6.QtCore import QRunnable, QObject, QThreadPool, pyqtSignal, QRect, Qt
from PyQt6.QtGui import QPixmap

class WorkerSignals(QObject):
    finished = pyqtSignal(list)

class ImageLoader(QRunnable):
    def __init__(self, effect):
        super().__init__()
        self.effect = effect
        self.signals = WorkerSignals()

    def run(self):
        # We need to access get_asset_path from the effect's module or define it here
        # Assuming you want to keep the helper logic consistent:
        from effects import get_asset_path 
        
        raw_sheet = QPixmap(get_asset_path(self.effect.SPRITE_PATH))
        frames = []
        
        for i in range(self.effect.TOTAL_FRAMES):
            # The simplified math
            col = i % self.effect.COLS
            row = i // self.effect.COLS
            
            rect = QRect(col * self.effect.FRAME_W, 
                         row * self.effect.FRAME_H, 
                         self.effect.FRAME_W, 
                         self.effect.FRAME_H)
            
            scaled = raw_sheet.copy(rect).scaled(
                self.effect.DISPLAY_W, self.effect.DISPLAY_H, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.FastTransformation
            )
            frames.append(scaled)
            
        self.signals.finished.emit(frames)
# Then in your AnimatedEffect:
    def start_animation(self, widget):
        loader = ImageLoader(self)
        loader.signals.finished.connect(lambda frames: self.on_frames_ready(frames, widget))
        QThreadPool.globalInstance().start(loader)

    def on_frames_ready(self, frames, widget):
        self.frames = frames
        # Now start the timer
        self.frame_timer.start(self.FRAME_INTERVAL_MS)