import sys
import json
import win32gui
import traceback

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtNetwork import QTcpServer, QHostAddress
from PyQt6 import sip

# Local imports
import config
from utils import log_debug
from scene_manager import SceneManager
from widget_factory import WidgetFactory

class Companion(QWidget):
    """The core engine that listens for socket commands to sync UI."""
    def __init__(self):
        super().__init__()
        log_debug("Companion: Initializing engine (Component-Based)...")
        self.scene_manager = SceneManager()
        self.child_to_parent_map = {}
        self.last_sync_id = -1
        
        self.server = QTcpServer()
        if not self.server.listen(QHostAddress.SpecialAddress.LocalHost, 12345):
            log_debug(f"Companion: CRITICAL: Unable to start server: {self.server.errorString()}")
        
        self.server.newConnection.connect(self.handle_connection)
        
        self.watchdog = QTimer(self)
        self.watchdog.timeout.connect(self.check_game_health)
        self.watchdog.start(3000)
        log_debug("Companion: Initialization complete.")

    def handle_connection(self):
        socket = self.server.nextPendingConnection()
        socket.readyRead.connect(lambda: self.process_packet(socket))
    
    def process_packet(self, socket):
        raw_data = socket.readAll().data()
        try:
            cmd_package = json.loads(raw_data.decode('utf-8'))
            packet_sync_id = cmd_package.get("sync_id", 0)
         
            self.last_sync_id = packet_sync_id
            cmd_type = cmd_package.get("event_type")
            
            if cmd_type == "clear_all": 
                log_debug("DEBUG: SceneManager received CLEAR command.")
                self.clear_all_messages()
            elif cmd_type == "update": 
                self.scene_manager.process_packet(cmd_package)
                self.sync_windows(cmd_package.get("data", []))

                
        except Exception as e:
            log_debug(f"Companion: ERROR processing packet: {e}\n{traceback.format_exc()}")
        finally:
            socket.disconnectFromHost()
            socket.deleteLater()

    def sync_windows(self, target_states):
        log_debug("Companion: Sync started.")
        target_ids = {s['logical_id'] for s in target_states}
        
        # 1. Cleanup orphaned elements and containers
        for eid in list(self.scene_manager.objects.keys()):
            if eid not in target_ids:
                log_debug(f"Companion: Cleaning up orphaned container: {eid}")
                self.clear_single_message(eid)
        
        for child_id in list(self.child_to_parent_map.keys()):
            if child_id not in target_ids:
                log_debug(f"Companion: Cleaning up orphaned child: {child_id}")
                self.clear_single_message(child_id)

        # 2. Sort: Process parents (no parent_id) before children
        sorted_states = sorted(target_states, key=lambda s: 0 if not s.get("parent_id") else 1)
        
        # 3. Process Containers & Children
        for s in sorted_states:
            eid = s['logical_id']
            
            if "parent_id" in s:
                # Handle Child
                parent_id = s["parent_id"]
                self.child_to_parent_map[eid] = parent_id
                parent = self.scene_manager.objects.get(parent_id)
                
                if parent:
                    log_debug(f"Companion: Syncing child {eid} to parent {parent_id}")
                    parent.add_element(s)
                else:
                    log_debug(f"Companion: Warning - Parent {parent_id} not found for {eid}")
            
            else:
                # Handle Container
                obj = self.scene_manager.get_or_create(eid, s.get("z_index", 0), s.get("options"))
                obj.z_index = s.get("z_index", obj.z_index)
                

                if "geometry" in s: 
                    log_debug(f"Companion: Enforcing script layout overrides for {eid}")
                    obj.update_geometry(s["geometry"]) # Explicit script bounds win!
                
                # Only show if not already visible (prevents repaint flicker)
                # By calling .show() here, AFTER update_geometry, 
                # we guarantee the window is sized correctly before the first draw.
                if not obj.widget.isVisible():
                    log_debug(f"Companion: Showing container {eid} after configuration.")
                    obj.widget.show()
                    
                    # === ADD THIS AUDIT LAYER ===
                    log_debug(f"=== WINDOW VISIBILITY AUDIT: {eid} ===")
                    log_debug(f" - Actual IsVisible: {obj.widget.isVisible()}")
                    log_debug(f" - Screen Geometry: {obj.widget.geometry()}")
                    log_debug(f" - Target Window Flags: {int(obj.widget.windowFlags())}")
                    log_debug(f" - Window Opacity Level: {obj.widget.windowOpacity()}")
        
        self.scene_manager.sort_and_stack_widgets()
        log_debug("Companion: Sync finished.")

    def clear_single_message(self, eid):
        log_debug(f"Companion: Clearing {eid}")
        
        # If it's a child, remove from parent
        if eid in self.child_to_parent_map:
            parent_id = self.child_to_parent_map.pop(eid)
            parent = self.scene_manager.objects.get(parent_id)
            if parent: parent.remove_child(eid)
            return

        # If it's a container, destroy it
        obj = self.scene_manager.objects.pop(eid, None)
        if obj and not sip.isdeleted(obj.widget):
            obj.widget.deleteLater()
            log_debug(f"Closed container: {eid}")

    def clear_all_messages(self):
        for eid in list(self.scene_manager.objects.keys()):
            self.clear_single_message(eid)

    def check_game_health(self):
        found = False
        def enum_handler(hwnd, lparam):
            nonlocal found
            if win32gui.GetWindowText(hwnd).startswith(config.GAME_WINDOW_TITLE): 
                found = True
        win32gui.EnumWindows(enum_handler, None)
        if not found: 
            log_debug("Warning: Game window not detected.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        companion = Companion()
        sys.exit(app.exec())
    except Exception as e:
        with open("crash_report.txt", "w") as f:
            f.write(traceback.format_exc())
        sys.exit(1)

