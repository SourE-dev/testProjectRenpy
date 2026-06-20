import sys, json, time, win32gui, os
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QObject
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import random 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EVENTS_FILE = os.path.join(BASE_DIR, "game_events.json")
LOG_FILE = os.path.join(BASE_DIR, "companion.log")
GAME_WINDOW_TITLE = "testProject"

def log_debug(msg):
    timestamp = time.strftime("%H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    with open(LOG_FILE, "a") as f: f.write(formatted + "\n")
    print(formatted)

import random # Add this at the top of companion.py

class MessageWindow(QWidget):
    def __init__(self, text, effect="default"):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Tool | 
                            Qt.WindowType.WindowStaysOnTopHint | 
                            Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        base_style = "padding: 20px; border-radius: 10px; font-size: 20px; font-weight: bold;"
        
        # Random offset logic: screen center-ish area (adjust 400/300 to your monitor size)
        # This keeps fireballs scattered within a 200px variance
        rand_x = random.randint(300, 700)
        rand_y = random.randint(200, 500)
        
        if effect == "fireball":
            color_style = "color: #FF4500; background-color: rgba(20, 0, 0, 200); border: 2px solid #FF4500;"
            self.move(rand_x, rand_y) 
        elif effect == "system":
            color_style = "color: #ADD8E6; background-color: rgba(0, 0, 80, 200); border: 1px solid #ADD8E6;"
            self.move(100, 100)
        else:
            color_style = "color: white; background-color: rgba(0,0,0,180);"
            self.move(100, 100)
            
        layout = QVBoxLayout()
        label = QLabel(text)
        label.setStyleSheet(base_style + color_style)
        layout.addWidget(label)
        self.setLayout(layout)
        self.show()
class EventSignal(QObject): trigger = pyqtSignal()
class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, s): self.s = s
    def on_modified(self, e): 
        # Add this print - it will appear in the companion terminal
        print(f"DEBUG: File modification detected on: {e.src_path}")
        if e.src_path.replace("\\", "/").endswith("game_events.json"):
            self.s.trigger.emit()
class Companion(QWidget):
    def __init__(self):
        super().__init__()
        log_debug(f"Companion started. Watching: {EVENTS_FILE}")
        self.active_messages = {}
        self.processed_ids = set()
        self.last_content = None  # <--- ADD THIS LINE HERE
        self.signal = EventSignal()
        self.signal.trigger.connect(self.process_events)
        
        self.observer = Observer()
        self.observer.schedule(FileChangeHandler(self.signal), BASE_DIR, recursive=False)
        self.observer.start()
        
        self.watchdog = QTimer(self)
        self.watchdog.timeout.connect(self.check_game_health)
        self.watchdog.start(3000)

    def check_game_health(self):
        found = False
        def enum_handler(hwnd, lparam):
            nonlocal found
            if win32gui.GetWindowText(hwnd).startswith(GAME_WINDOW_TITLE): found = True
        win32gui.EnumWindows(enum_handler, None)
        if not found: log_debug("Warning: Game window not detected.")


    def process_events(self):
        try:
            if not os.path.exists(EVENTS_FILE) or os.path.getsize(EVENTS_FILE) == 0:
                return 

            with open(EVENTS_FILE, "r") as f:
                content = f.read()
            
            if content == self.last_content:
                return
            self.last_content = content
            log_debug(f"DEBUG: Companion read content: {content}")
            # target_states is now the full list of what SHOULD be on screen
            target_states = json.loads(content)
            if not isinstance(target_states, list):
                log_debug(f"CRITICAL: Expected list, got {type(target_states)}. Content: {content}")
                return
            
            # Ensure every item is a dictionary
            target_ids = {s['id'] for s in target_states if isinstance(s, dict) and 'id' in s}
            # ---------------------------

            # 1. KILL: Remove windows that are no longer in the Source of Truth
            for eid in list(self.active_messages.keys()):
                if eid not in target_ids:
                    self.clear_single_message(eid)

            # 2. SPAWN: Add windows that are in the state but not yet rendered
            for s in target_states:
                eid = s['id']
                if eid not in self.active_messages:
                    log_debug(f"Spawning window: {eid}")
                    self.active_messages[eid] = MessageWindow(
                        s['msg'], 
                        effect=s.get("effect", "default")
                    )
        except Exception as e:
            log_debug(f"Error in process_events: {e}")

    def clear_single_message(self, eid):
        if eid in self.active_messages:
            self.active_messages[eid].close()
            del self.active_messages[eid]
            log_debug(f"Closed window: {eid}")

    def clear_all_messages(self):
        for eid in list(self.active_messages.keys()):
            self.clear_single_message(eid)
        log_debug("Cleared all messages.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Companion()
    window.hide()
    sys.exit(app.exec())