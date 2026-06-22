from PyQt6.QtCore import QRunnable, QObject, pyqtSignal, QRect, Qt
from PyQt6.QtGui import QPixmap
from utils import log_debug
class WorkerSignals(QObject):
    finished = pyqtSignal(list)

class ImageLoader(QRunnable):
    def __init__(self, effect, asset_path_func):
        super().__init__()
        self.effect = effect
        self.asset_path_func = asset_path_func # Pass the function as a dependency
        self.signals = WorkerSignals()

    def run(self):
        path = self.asset_path_func(self.effect.IMAGE_PATH)
        log_debug(f"DEBUG: ImageLoader loading asset: {path}")
        
        raw_sheet = QPixmap(path)
        
        if raw_sheet.isNull():
            log_debug(f"CRITICAL: Failed to load image at {path}")
            return

        log_debug(f"DEBUG: Sheet size: {raw_sheet.width()}x{raw_sheet.height()}")
        log_debug(f"DEBUG: Processing {self.effect.TOTAL_FRAMES} frames (W:{self.effect.FRAME_W}, H:{self.effect.FRAME_H})")

        frames = []
        for i in range(self.effect.TOTAL_FRAMES):
            col = i % self.effect.COLS
            row = i // self.effect.COLS
            
            rect = QRect(col * self.effect.FRAME_W, 
                         row * self.effect.FRAME_H, 
                         self.effect.FRAME_W, 
                         self.effect.FRAME_H)
            
            # This is where the scaling happens
            log_debug(f"DEBUG: Frame {i} rect: {rect} -> Target: {self.effect.DISPLAY_W}x{self.effect.DISPLAY_H}")
            
            scaled = raw_sheet.copy(rect).scaled(
                self.effect.DISPLAY_W, self.effect.DISPLAY_H, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.FastTransformation
            )
            frames.append(scaled)
            
        self.signals.finished.emit(frames)