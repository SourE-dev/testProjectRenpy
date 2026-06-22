# widgets/movement.py
import math
from utils import log_debug
class MovementController:
    def update(self, widget):
        raise NotImplementedError

class LinearMovement(MovementController):
    def __init__(self, start_pos=(0, 0), end_pos=(500, 500), speed=5):
        self.start_pos = start_pos
        self.current_pos = [float(start_pos[0]), float(start_pos[1])]
        self.end_pos = end_pos
        self.speed = speed
        
    def get_start_pos(self): return self.start_pos

    def update(self, widget):
        dx = self.end_pos[0] - self.current_pos[0]
        dy = self.end_pos[1] - self.current_pos[1]
        dist = (dx**2 + dy**2)**0.5
        if dist > self.speed:
            self.current_pos[0] += (dx / dist) * self.speed
            self.current_pos[1] += (dy / dist) * self.speed
            widget.move(int(self.current_pos[0]), int(self.current_pos[1]))
            return False 
        widget.move(self.end_pos[0], self.end_pos[1])
        return True 

class CosinePathMovement(MovementController):
    def __init__(self, start_pos=(0, 300), end_pos=(1920, 300), amplitude=50, frequency=0.05, speed=5, **kwargs):
        log_debug(f"CosinePathMovement Init - Raw start_pos: {start_pos}, end_pos: {end_pos}, kwargs: {kwargs}")
        
        # 1. Handle start position
        if start_pos:
            self.start_x, self.start_y = start_pos
        else:
            self.start_x = kwargs.get('start_x', 0)
            self.start_y = kwargs.get('start_y', 0)
        
        # 2. Handle end position
        # Check if end_pos is a list/tuple or just None
        if end_pos and isinstance(end_pos, (list, tuple)):
            self.end_x = float(end_pos[0])
        else:
            self.end_x = float(kwargs.get('end_x', 500))
            
        log_debug(f"CosinePathMovement State - x: {self.start_x}, y: {self.start_y}, end_x: {self.end_x}")
            
        # 3. Initialize state
        self.x = float(self.start_x)
        self.amp = amplitude
        self.freq = frequency
        self.speed = speed # ADD THIS LINE

    def get_start_pos(self):
        try:
            y = self.start_y + math.cos(self.start_x * self.freq) * self.amp
            res = (int(self.start_x), int(y))
            log_debug(f"get_start_pos returning: {res}")
            return res
        except Exception as e:
            log_debug(f"get_start_pos CRASH: {e}")
            raise # Let it bubble up to your traceback

    def update(self, widget):
        self.x += self.speed 
        # Calculate raw y
        raw_y = self.start_y + math.cos(self.x * self.freq) * self.amp
        
        # Clamp to prevent going off-screen
        y = max(0, int(raw_y)) 
        
        widget.move(int(self.x), y)
        return self.x >= self.end_x