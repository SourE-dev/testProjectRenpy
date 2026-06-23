import sys
import json
import win32gui

from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtNetwork import QTcpServer, QHostAddress
from PyQt6 import sip
# Local imports
import config
from utils import log_debug
from scene_manager import SceneManager
from window_base import MessageWindow 
from registry import get_effect_class
class Companion(QWidget):
    """The core engine that listens for socket commands to sync UI."""
    def __init__(self):
        super().__init__()
        self.active_messages = {}
        self.scene_manager = SceneManager()
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
    def get_effect_config(self, effect_name):
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
            # 1. Log raw data for verification
            decoded_data = raw_data.decode('utf-8')
            # log_debug(f"DEBUG: Raw Packet: {decoded_data}") # Uncomment if needed
            
            cmd_package = json.loads(decoded_data)
            cmd_type = cmd_package.get("event_type")
            
            log_debug(f"DEBUG: Processing event: {cmd_type}")
            
            if cmd_type == "clear_all": 
                self.clear_all_messages()
            elif cmd_type == "update": 
                data = cmd_package.get("data", [])
                log_debug(f"DEBUG: Received packet with {len(data)} items: {data}")
                # 2. Structural Debugging
                if not isinstance(data, list):
                    log_debug(f"ERROR: 'data' field is not a list! Found: {type(data)}")
                else:
                    for idx, item in enumerate(data):
                        if not isinstance(item, dict):
                            log_debug(f"ERROR: Data item {idx} is not a dict: {item}")
                        elif 'logical_id' not in item:
                            log_debug(f"ERROR: Data item {idx} missing 'logical_id'. Keys found: {list(item.keys())}")
                
                self.sync_windows(data)
                
            elif cmd_type == "register_effect": 
                self.save_custom_effect(cmd_package.get("name"), cmd_package.get("data"))
                
        except Exception as e:
            # 3. Enhanced Exception Debugging
            import traceback
            log_debug(f"Packet error: {e}")
            log_debug(f"Traceback: {traceback.format_exc()}")
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

    # main.py

    def sync_windows(self, target_states):
        # 1. Cleanup
        target_ids = {s['logical_id'] for s in target_states}
        log_debug(f"DEBUG: Syncing {len(target_states)} states.") # Check count
        for eid in list(self.scene_manager.objects.keys()):
            if eid not in target_ids:
                log_debug(f"DEBUG: Cleaning up {eid}")
                self.clear_single_message(eid)
        
        # 2. Spawn/Update
        for s in target_states:
            eid = s['logical_id']
            z_idx = s.get("z_index", 0)
            
            # Prepare options
            effect_name = s.get("effect", "default")
            user_overrides = s.get("options", {})
            library_defaults = self.get_effect_config(effect_name)
            final_options = {**library_defaults, **user_overrides} 
            
            if eid not in self.scene_manager.objects:
                # Create Body
                log_debug(f"DEBUG: Creating new widget for {eid}")
                widget = MessageWindow(s['msg'], options=final_options)
                
                # Create Brain
                effect_class = get_effect_class(final_options.get("class", "basic"))
                effect = effect_class(options=final_options)
                effect.start_animation(widget)
                
                # Register in SceneManager
                self.scene_manager.get_or_create(eid, z_idx, widget, effect)
                widget.show()
            else:
                # Update Z-Index for existing object
                log_debug(f"DEBUG: Updating existing {eid} (Z: {z_idx})")
                obj = self.scene_manager.objects[eid]
                # Update Z-Index
                obj.z_index = z_idx
                
                # Update Text/Content
                # Access the label directly if it exists in your MessageWindow
                if hasattr(obj.widget, 'label'):
                    if obj.widget.label.text() != s['msg']:
                        obj.widget.label.setText(s['msg'])
                
                log_debug(f"DEBUG: Updated existing {eid} (Z: {z_idx})")
                
        # 3. Final visual layer sorting (This triggers the raise_ logic)
        self.scene_manager.sort_and_stack_widgets()
        for eid, obj in self.scene_manager.objects.items():
            log_debug(f"DEBUG: Object {eid} is at Z={obj.z_index}")
    # In main.py
    def clear_all_messages(self):
        # Change from self.active_messages to the manager's collection
        for eid in list(self.scene_manager.objects.keys()):
            self.clear_single_message(eid)

    # In Companion class (main.py)
    # main.py

    def clear_single_message(self, eid):
        # Pop from the manager instead of active_messages
        obj = self.scene_manager.objects.pop(eid, None)
        
        if obj:
            # Stop the Brain
            if hasattr(obj.effect, 'cleanup'):
                obj.effect.cleanup(obj.widget)
            
            # Destroy the Body
            if obj.widget and not sip.isdeleted(obj.widget):
                obj.widget.hide()
                obj.widget.deleteLater()
                log_debug(f"Closed window: {eid}")
        else:
            log_debug(f"Skipping cleanup for {eid}: Not found in SceneManager")
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