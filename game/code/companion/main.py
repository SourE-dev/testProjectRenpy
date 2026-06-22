import sys
import json
import win32gui
import os
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap, QPainter
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Local imports
import config
from utils import log_debug
from effects import AnimatedEffect, BaseEffect, FireballEffect

# --- UI Components ---
class MessageWindow(QWidget):
    EFFECT_REGISTRY = {"fireball": FireballEffect, "default": BaseEffect}

    def __init__(self, text, effect="default", options=None):
        super().__init__()
        self.options = options or {} # Defaults to empty dict
        self.effect = self.EFFECT_REGISTRY.get(effect, BaseEffect)(options=options)
        #  Now to enable qtransparency and click-through, we need to set the appropriate window flags and attributes.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
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
        if self.sprite_frame and not self.sprite_frame.isNull(): # ADDED NULL CHECK
            painter = QPainter(self)
            painter.drawPixmap(0, 0, self.sprite_frame)
        else:
            super().paintEvent(event)

    def setup_ui(self, text):
        base_style = """
            QLabel {
                padding: 20px; border-radius: 15px; font-size: 20px; font-weight: bold;
                background-color: rgba(30, 30, 30, 255); border: 2px solid #555555; color: white;
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
        self.observer.schedule(FileChangeHandler(self.signal), config.BASE_DIR, recursive=False)
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
            if win32gui.GetWindowText(hwnd).startswith(config.GAME_WINDOW_TITLE): found = True
        win32gui.EnumWindows(enum_handler, None)
        if not found: log_debug("Warning: Game window not detected.")

    def process_events(self):
        """Parses the JSON state file and synchronizes active UI windows."""
        try:
            if not os.path.exists(config.EVENTS_FILE): return
            with open(config.EVENTS_FILE, "r") as f: content = f.read()
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

    def clear_all_messages(self):
        # We use a list to iterate, but clear_single_message handles the removal
        # individually. This is clean and correct.
        for eid in list(self.active_messages.keys()):
            self.clear_single_message(eid)

    def clear_single_message(self, eid):
        # Using pop safely retrieves and removes the item in one step
        widget = self.active_messages.pop(eid, None)
        if widget:
            # Safely call cleanup (now that BaseEffect supports it)
            if hasattr(widget.effect, 'cleanup'):
                widget.effect.cleanup(widget)
            widget.hide()
            widget.deleteLater()
            log_debug(f"Closed window: {eid}")

if __name__ == "__main__":
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL)
    
    app = QApplication(sys.argv)
    
    # We use a try-except block to catch Python-level crashes
    try:
        companion = Companion()
        # app.exec() starts the main event loop
        # The return code is captured here
        exit_code = app.exec()
        sys.exit(exit_code)
        
    except Exception as e:
        # This will catch errors during initialization or runtime 
        # that aren't caught by internal class try/excepts
        log_debug(f"CRITICAL APPLICATION CRASH: {e}")
        
        # Optionally, write the full traceback to a file for review
        import traceback
        with open("crash_report.txt", "w") as f:
            f.write(traceback.format_exc())
            
        sys.exit(1)