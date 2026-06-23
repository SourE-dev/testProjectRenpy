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
        log_debug("Companion: Initializing engine...")
        self.active_messages = {}
        self.scene_manager = SceneManager()
        self.child_to_parent_map = {}
        self.last_sync_id = -1
        self.server = QTcpServer()
        if not self.server.listen(QHostAddress.SpecialAddress.LocalHost, 12345):
            log_debug(f"Companion: CRITICAL: Unable to start server: {self.server.errorString()}")
        
        self.server.newConnection.connect(self.handle_connection)
        log_debug("Companion: Server listening on 127.0.0.1:12345")
        
        self.watchdog = QTimer(self)
        self.watchdog.timeout.connect(self.check_game_health)
        self.watchdog.start(3000)
        log_debug("Companion: Initialization complete.")
    def get_effect_config(self, effect_name):
        # 1. Load Custom Effects
        log_debug(f"Companion: Fetching config for effect: {effect_name}")
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
        log_debug("Companion: New socket connection incoming.")
        socket = self.server.nextPendingConnection()
        socket.readyRead.connect(lambda: self.process_packet(socket))
    
    def process_packet(self, socket):
        raw_data = socket.readAll().data()
        try:
            cmd_package = json.loads(raw_data.decode('utf-8'))
            
            # SEQUENCE ID CHECK
            packet_sync_id = cmd_package.get("sync_id", 0)
            if packet_sync_id < self.last_sync_id:
                log_debug(f"Companion: Discarding outdated packet (ID: {packet_sync_id} < {self.last_sync_id})")
                return
            
            self.last_sync_id = packet_sync_id
            cmd_type = cmd_package.get("event_type")
            
            log_debug(f"Companion: Packet received | Type: {cmd_type}")
            
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
            log_debug(f"Companion: ERROR processing packet: {e}")
            log_debug(f"Companion: Traceback: {traceback.format_exc()}")
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
        """
        Synchronizes the UI state with Ren'Py's current engine state.
        Enforces geometry from packets for rollback stability.
        """
        log_debug("Companion: Sync started.")
        # 1. Cleanup: Remove objects not present in the current target_states
        target_ids = {s['logical_id'] for s in target_states}
        
        # Cleanup Containers
        for eid in list(self.scene_manager.objects.keys()):
            if eid not in target_ids:
                log_debug(f"Companion: Cleaning up orphaned container: {eid}")
                self.clear_single_message(eid)
        
        # Cleanup Children
        for child_id in list(self.child_to_parent_map.keys()):
            if child_id not in target_ids:
                log_debug(f"Companion: Cleaning up orphaned child: {child_id}")
                self.clear_single_message(child_id)

        # 2. Process Containers
        for s in target_states:
            if "parent_id" in s:
                continue 
                
            eid = s['logical_id']
            z_idx = s.get("z_index", 0)
            
            # Prepare configuration
            effect_name = s.get("effect", "default")
            user_overrides = s.get("options", {})
            library_defaults = self.get_effect_config(effect_name)
            final_options = {**library_defaults, **user_overrides} 
            
            if eid not in self.scene_manager.objects:
                log_debug(f"DEBUG: Creating new Container: {eid}")
                obj = self.scene_manager.get_or_create(eid, z_idx, final_options)
                
                # Apply initial geometry if present
                if "geometry" in s:
                    obj.update_geometry(s["geometry"])
                
                if 'msg' in s and s['msg'] is not None:
                    obj.update_text(s['msg'])
                
                # Attach Brain
                effect_class = get_effect_class(final_options.get("class", "basic"))
                obj.effect = effect_class(options=final_options)
                obj.effect.start_animation(obj.widget)
                
                obj.widget.show()
            
            else:
                # Update existing Container
                obj = self.scene_manager.objects[eid]
                obj.z_index = z_idx
                
                # ENFORCE STATELESS GEOMETRY
                if "geometry" in s:
                    obj.update_geometry(s["geometry"])
                
                if 'msg' in s and s['msg'] is not None:
                    obj.update_text(s['msg'])

        # 3. Process Children
        for s in target_states:
            if "parent_id" in s:
                eid = s['logical_id']
                parent_id = s["parent_id"]
                self.child_to_parent_map[eid] = parent_id
                
                parent = self.scene_manager.objects.get(parent_id)
                if parent:
                    if eid not in parent.child_widgets:
                        log_debug(f"DEBUG: Adding child {eid} to parent {parent_id}")
                        parent.add_element(s)
                else:
                    # CRITICAL FIX: If parent is missing, treat the child as an error
                    # or a pending request. For now, log and clean up to prevent ghosts.
                    log_debug(f"WARNING: Child {eid} received, but parent {parent_id} not found. Skipping.")
                    self.clear_single_message(eid)
        # 4. Final visual layer sorting
        self.scene_manager.sort_and_stack_widgets()
        log_debug("Companion: Sync finished.")
    # In main.py
    def clear_all_messages(self):
        # Change from self.active_messages to the manager's collection
        log_debug("Companion: Clearing all messages.")
        for eid in list(self.scene_manager.objects.keys()):
            self.clear_single_message(eid)

    # In Companion class (main.py)
    # main.py

    def clear_single_message(self, eid):
        # 1. Handle Child Cleanup
        log_debug(f"Companion: Clearing message: {eid}")
        if eid in self.child_to_parent_map:
            parent_id = self.child_to_parent_map[eid]
            parent_obj = self.scene_manager.objects.get(parent_id)
            
            if parent_obj:
                log_debug(f"DEBUG: Attempting to remove child {eid} from parent {parent_id}")
                parent_obj.remove_child(eid)
                self.child_to_parent_map.pop(eid) # Remove from map
            else:
                log_debug(f"DEBUG: Parent {parent_id} gone, force-cleaning child {eid}")
                self.child_to_parent_map.pop(eid)
            return
        # 2. Handle Parent/Container Cleanup
        obj = self.scene_manager.objects.pop(eid, None)
        
        if obj:
            # Stop the Brain
            if hasattr(obj.effect, 'cleanup'):
                obj.effect.cleanup(obj.widget)
            
            # Destroy the Body (using sip to prevent dangling pointers)
            if obj.widget and not sip.isdeleted(obj.widget):
                obj.widget.hide()
                obj.widget.deleteLater()
                log_debug(f"Closed container: {eid}")
        else:
            log_debug(f"Skipping cleanup for {eid}: Not found in SceneManager")
        log_debug(f"Companion: Successfully cleared: {eid}")
    def save_custom_effect(self, name, data):
        # 1. Load existing custom effects
        log_debug(f"Companion: Saving custom effect: {name}")
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
        
        log_debug(f"Companion: Saved custom effect: {name}")

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