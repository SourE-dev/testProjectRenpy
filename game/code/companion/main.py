import sys
import json
import time
import win32gui
import os
import ctypes
from ctypes import wintypes

from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap, QPainter
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from effects import AnimatedEffect, BaseEffect, FireballEffect

# --- Configuration & Constants ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
EVENTS_FILE = os.path.join(BASE_DIR, "game_events.json")
LOG_FILE = os.path.join(BASE_DIR, "companion.log")
GAME_WINDOW_TITLE = "testProject"
ENUM_CURRENT_SETTINGS = -1


# --- Helper Functions ---
def log_debug(msg):
    """Writes a timestamped message to the log file and prints to console."""
    timestamp = time.strftime("%H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    with open(LOG_FILE, "a") as f: f.write(formatted + "\n")
    print(formatted)


# --- UI Components ---
class MessageWindow(QWidget):
    EFFECT_REGISTRY = {"fireball": FireballEffect, "default": BaseEffect}

    def __init__(self, text, effect="default", options=None):
        super().__init__()
        self.options = options or {} # Defaults to empty dict
        self.effect = self.EFFECT_REGISTRY.get(effect, BaseEffect)(options=options)
        
        # 2. Window flags
        if self.options.get("click_through", False):
            flags = Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint | \
                    Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowTransparentForInput
        else:
            flags = Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint | \
                    Qt.WindowType.FramelessWindowHint
        self.setWindowFlags(flags)
        self.sprite_frame = None 

        # 3. Now you can safely use self.effect
        if isinstance(self.effect, AnimatedEffect):
            self.setFixedSize(self.effect.DISPLAY_W, self.effect.DISPLAY_H)
            self.setLayout(QVBoxLayout())
        else:
            self.setup_ui(text)
            
        self.show()
        self.effect.start_animation(self)
    def update_frame(self, pixmap):
        self.sprite_frame = pixmap
        self.update() 

    def paintEvent(self, event):
        # print("DEBUG: PaintEvent running...") # Add this
        if self.sprite_frame:
            painter = QPainter(self)
            painter.drawPixmap(0, 0, self.sprite_frame)
        else:
            super().paintEvent(event)

    def setup_ui(self, text):
        base_style = """
            QLabel {
                padding: 20px; border-radius: 15px; font-size: 20px; font-weight: bold;
                background-color: rgba(30, 30, 30, 200); border: 2px solid #555555; color: white;
            }
        """
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(text)
        self.label.setStyleSheet(base_style + self.effect.apply_style(self))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.show()

# --- Watchdog System ---
class EventSignal(QObject): 
    """Custom signal to bridge filesystem events to the UI thread."""
    trigger = pyqtSignal()

class FileChangeHandler(FileSystemEventHandler):
    """Monitors the JSON file for changes and triggers an update signal."""
    def __init__(self, signal): 
        self.signal = signal
    def on_modified(self, event): 
        if event.src_path.replace("\\", "/").endswith("game_events.json"):
            self.signal.trigger.emit()

# --- Main Application Logic ---
class Companion(QWidget):
    """The core engine that syncs game state events to UI windows."""
    def __init__(self):
        super().__init__()
        self.active_messages = {}
        self.last_content = None
        
        # Setup File Watcher
        self.signal = EventSignal()
        self.signal.trigger.connect(self.process_events)
        self.observer = Observer()
        self.observer.schedule(FileChangeHandler(self.signal), BASE_DIR, recursive=False)
        self.observer.start()
        
        # Health Monitor
        self.watchdog = QTimer(self)
        self.watchdog.timeout.connect(self.check_game_health)
        self.watchdog.start(3000)

    def check_game_health(self):
        """Verifies if the game process is still active."""
        found = False
        def enum_handler(hwnd, lparam):
            nonlocal found
            if win32gui.GetWindowText(hwnd).startswith(GAME_WINDOW_TITLE): found = True
        win32gui.EnumWindows(enum_handler, None)
        if not found: log_debug("Warning: Game window not detected.")

    def process_events(self):
        """Parses the JSON state file and synchronizes active UI windows."""
        try:
            if not os.path.exists(EVENTS_FILE): return
            with open(EVENTS_FILE, "r") as f: content = f.read()
            if not content or content == self.last_content: return
            
            cmd_package = json.loads(content)
            self.last_content = content
            
            if cmd_package.get("type") == "clear_all": 
                self.clear_all_messages()
            elif cmd_package.get("type") == "update": 
                self.sync_windows(cmd_package.get("data", []))
        except (IOError, PermissionError, json.JSONDecodeError): 
            pass
        except Exception as e: 
            log_debug(f"Unexpected error: {e}")

    def sync_windows(self, target_states):
        """Ensures active windows match the target game state."""
        target_ids = {s['id'] for s in target_states if isinstance(s, dict)}
        
        # Kill windows not in the new state
        for eid in list(self.active_messages.keys()):
            if eid not in target_ids: 
                self.clear_single_message(eid)
        
        # Spawn new windows
        for s in target_states:
            eid = s['id']
            if eid not in self.active_messages:
                log_debug(f"Spawning window: {eid}") # LOGGING RESTORED
                options = s.get("options", {})
                self.active_messages[eid] = MessageWindow(
                    s['msg'], 
                    effect=s.get("effect", "default"), 
                    options=options
                )

    def clear_single_message(self, eid):
        if eid in self.active_messages:
            self.active_messages[eid].close()
            del self.active_messages[eid]
            log_debug(f"Closed window: {eid}") # LOGGING RESTORED

    def clear_all_messages(self):
        for eid in list(self.active_messages.keys()): self.clear_single_message(eid)

if __name__ == "__main__":
    # 1. Enable hardware acceleration (Supported in PyQt6)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL)
    
    # NOTE: AA_EnableHighDpiScaling is removed in PyQt6 because 
    # it is now the default behavior of the framework.

    app = QApplication(sys.argv)
    
    # 2. Create the instance
    companion = Companion()
    
    # 3. Standard execution
    sys.exit(app.exec())