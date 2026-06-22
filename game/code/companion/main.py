import sys
import json
import win32gui

from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtNetwork import QTcpServer, QHostAddress
# Local imports
import config
from utils import log_debug
# Assuming you move MessageWindow to window_base.py as planned
from window_base import MessageWindow 

class Companion(QWidget):
    """The core engine that listens for socket commands to sync UI."""
    def __init__(self):
        super().__init__()
        self.active_messages = {}
        
        # 1. Setup TCP Socket Server
        self.server = QTcpServer()
        # Listen on localhost (127.0.0.1) on port 12345
        if not self.server.listen(QHostAddress.SpecialAddress.LocalHost, 12345):
            log_debug(f"Critical: Unable to start server: {self.server.errorString()}")
        
        self.server.newConnection.connect(self.handle_connection)
        log_debug("Companion Server listening on 127.0.0.1:12345")
        
        # 2. Health Monitor (Keep this as is)
        self.watchdog = QTimer(self)
        self.watchdog.timeout.connect(self.check_game_health)
        self.watchdog.start(3000)
    def get_effect_config(effect_name):
        # 1. Load Custom Effects
        try:
            with open("user_custom_effects.json", "r") as f:
                custom = json.load(f)
                if effect_name in custom: return custom[effect_name]
        except: pass
        
        # 2. Load Core Library
        try:
            with open("effects_library.json", "r") as f:
                core = json.load(f)
                return core.get(effect_name, {})
        except: return {}
    def handle_connection(self):
        socket = self.server.nextPendingConnection()
        socket.readyRead.connect(lambda: self.process_packet(socket))
    
    def process_packet(self, socket):
        raw_data = socket.readAll().data()
        try:
            cmd_package = json.loads(raw_data.decode('utf-8'))
            cmd_type = cmd_package.get("type")
            
            if cmd_type == "clear_all": 
                self.clear_all_messages()
            elif cmd_type == "update": 
                self.sync_windows(cmd_package.get("data", []))
            elif cmd_type == "register_effect": 
                self.save_custom_effect(cmd_package.get("name"), cmd_package.get("data"))
        except Exception as e:
            log_debug(f"Packet error: {e}")
        finally:
            socket.disconnectFromHost()
            socket.deleteLater()
    def check_game_health(self):
        found = False
        def enum_handler(hwnd, lparam):
            nonlocal found
            if win32gui.GetWindowText(hwnd).startswith(config.GAME_WINDOW_TITLE): 
                found = True
        win32gui.EnumWindows(enum_handler, None)
        if not found: 
            log_debug("Warning: Game window not detected.")

    def sync_windows(self, target_states):
        target_ids = {s['id'] for s in target_states if isinstance(s, dict)}
        
        # Kill windows not in the new state
        for eid in list(self.active_messages.keys()):
            if eid not in target_ids: 
                self.clear_single_message(eid)
        
        # Spawn new windows
        for s in target_states:
            eid = s['id']
            if eid not in self.active_messages:
                log_debug(f"Spawning window: {eid}")
                
                # --- NEW DATA-DRIVEN MERGE LOGIC ---
                effect_name = s.get("effect", "default")
                user_overrides = s.get("options", {})
                
                # 1. Fetch library defaults
                library_defaults = self.get_effect_config(effect_name)
                
                # 2. Merge (Overrides beat Defaults)
                final_options = {**library_defaults, **user_overrides}
                
                # 3. Spawn with merged options
                self.active_messages[eid] = MessageWindow(
                    s['msg'], 
                    effect=effect_name, 
                    options=final_options
                )

    def clear_all_messages(self):
        for eid in list(self.active_messages.keys()):
            self.clear_single_message(eid)

    def clear_single_message(self, eid):
        widget = self.active_messages.pop(eid, None)
        if widget:
            if hasattr(widget, 'effect') and hasattr(widget.effect, 'cleanup'):
                widget.effect.cleanup(widget)
            widget.hide()
            widget.deleteLater()
            log_debug(f"Closed window: {eid}")
    def save_custom_effect(self, name, data):
        # 1. Load existing custom effects
        try:
            with open("user_custom_effects.json", "r") as f:
                library = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            library = {}
        
        # 2. Update with new data
        library[name] = data
        
        # 3. Save back
        with open("user_custom_effects.json", "w") as f:
            json.dump(library, f, indent=4)
        
        log_debug(f"Saved custom effect: {name}")

if __name__ == "__main__":
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL)
    app = QApplication(sys.argv)
    
    try:
        companion = Companion()
        exit_code = app.exec()
        sys.exit(exit_code)
    except Exception as e:
        log_debug(f"CRITICAL APPLICATION CRASH: {e}")
        import traceback
        with open("crash_report.txt", "w") as f:
            f.write(traceback.format_exc())
        sys.exit(1)