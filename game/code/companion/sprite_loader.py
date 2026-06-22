from PyQt6.QtCore import QRunnable, QObject, pyqtSignal, QRect, Qt
from PyQt6.QtGui import QPixmap

class WorkerSignals(QObject):
    finished = pyqtSignal(list)

class ImageLoader(QRunnable):
    def __init__(self, effect, asset_path_func):
        super().__init__()
        self.effect = effect
        self.asset_path_func = asset_path_func # Pass the function as a dependency
        self.signals = WorkerSignals()

    def run(self):
        # 1. REMOVE the 'from effects import get_asset_path'
        # Importing inside a thread can lead to circular import issues.
        # Use a passed-in function instead.
        
        raw_sheet = QPixmap(self.asset_path_func(self.effect.SPRITE_PATH))
        frames = []
        
        for i in range(self.effect.TOTAL_FRAMES):
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