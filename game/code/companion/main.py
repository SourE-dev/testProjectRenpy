import sys
import json
import win32gui
import traceback
import os
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtNetwork import QTcpServer, QHostAddress
from PyQt6 import sip
from PyQt6.QtGui import QGuiApplication
# Local imports
import config
from utils import log_debug
from scene_manager import SceneManager
from widget_factory import WidgetFactory

os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"

class Companion(QWidget):
    """The core engine that listens for socket commands to sync UI."""
    def __init__(self):
        super().__init__()
        log_debug("Companion: Initializing engine (Component-Based)...")
        
        try:
            # 1. Cache current screen specs
            self.cache_screen_geometry()

            # 2. CONNECT SIGNALS DEFENSIVELY
            # FIX: We query the screen array object and hold a STRONG Python reference to it 
            # as an instance property ('self.primary_screen'). This prevents the garbage collector 
            # from dropping the memory pointers and throwing access violations!
            app_instance = QGuiApplication.instance()
            self.primary_screen = QGuiApplication.primaryScreen()
            
            if app_instance and self.primary_screen:
                # Target the initialized instance tracks cleanly
                app_instance.screenAdded.connect(self.handle_display_hardware_change)
                app_instance.screenRemoved.connect(self.handle_display_hardware_change)
                self.primary_screen.geometryChanged.connect(self.handle_display_hardware_change)
                log_debug("Companion: Display event listeners successfully bound via application instance.")
            else:
                log_debug("Companion: WARNING - Application instance or primary screen missing during signal bind.")
                
        except Exception as e:
            log_debug(f"Companion: CRITICAL initialization error in Display Layout binds: {e}\n{traceback.format_exc()}")

        try:
            # 3. Spin up subsystems
            self.scene_manager = SceneManager()
            self.child_to_parent_map = {}
            self.last_sync_id = -1
            
            self.server = QTcpServer()
            if not self.server.listen(QHostAddress.SpecialAddress.LocalHost, 12345):
                log_debug(f"Companion: CRITICAL: Unable to start server: {self.server.errorString()}")
            else:
                log_debug("Companion: Network TCP engine listening on port 12345.")
            
            self.server.newConnection.connect(self.handle_connection)
            
            self.watchdog = QTimer(self)
            self.watchdog.timeout.connect(self.check_game_health)
            self.watchdog.start(3000)
            log_debug("Companion: Initialization complete.")
            
        except Exception as e:
            log_debug(f"Companion: CRITICAL breakdown during subsystem initialization: {e}\n{traceback.format_exc()}")
        
    def cache_screen_geometry(self):
        """Caches the absolute physical desktop pixel bounds safely in local memory."""
        screen = QGuiApplication.primaryScreen()
        if not screen:
            log_debug("Companion: Cannot cache screen geometry - primary screen is missing.")
            return
            
        geom = screen.geometry()
        self.screen_x = geom.x()
        self.screen_y = geom.y()
        self.screen_w = geom.width()
        self.screen_h = geom.height()
        log_debug(f"Display Cache Updated: {self.screen_w}x{self.screen_h} at offset ({self.screen_x}, {self.screen_y})")

    def handle_display_hardware_change(self, *args):
        log_debug("OS Display Hardware Shift Detected! Recalculating canvas mapping cache...")
        # Re-bind the screen instance reference safely if the primary monitor changed identities
        self.primary_screen = QGuiApplication.primaryScreen()
        self.cache_screen_geometry()

    def handle_connection(self):
        socket = self.server.nextPendingConnection()
        socket.readyRead.connect(lambda: self.process_packet(socket))
    
    def process_packet(self, socket):
        raw_data = socket.readAll().data()
        try:
            # 1. DECODE RAW SOCKET TEXT
            decoded_text = raw_data.decode('utf-8')
            
            # =========================================================================
            # NETWORK WIRE AUDIT LOG
            # =========================================================================
            # This parses and pretty-prints EVERY incoming packet before your engine
            # touches it, allowing you to verify exactly what Ren'Py is broadcasting.
            try:
                parsed_json = json.loads(decoded_text)
                pretty_packet = json.dumps(parsed_json, indent=4)
                log_debug(
                    f"\n=== [NETWORK WIRE INBOUND] =====================================\n"
                    f"{pretty_packet}\n"
                    f"================================================================"
                )
            except Exception:
                # Fallback if the raw text is malformed string data
                log_debug(f"\n=== [NETWORK WIRE INBOUND (RAW TEXT)] ===\n{decoded_text}\n========================================")

            # 2. RUN STANDARD PROCESSOR MATCHES
            cmd_package = json.loads(decoded_text)
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
        
        # 1. Cleanup orphaned elements and containers (Unchanged)
        for eid in list(self.scene_manager.objects.keys()):
            if eid not in target_ids:
                log_debug(f"Companion: Cleaning up orphaned container: {eid}")
                self.clear_single_message(eid)
        
        for child_id in list(self.child_to_parent_map.keys()):
            if child_id not in target_ids:
                log_debug(f"Companion: Cleaning up orphaned child: {child_id}")
                self.clear_single_message(child_id)

        # 2. Sort: Process parents (no parent_id) before children (Unchanged)
        sorted_states = sorted(target_states, key=lambda s: 0 if not s.get("parent_id") else 1)
        
        # 3. PHASE A: CORE STRUCTURAL LAYOUT SYNCHRONIZATION
        # We process geometry setups first for all elements to establish solid baseline coordinates.
        for s in sorted_states:
            eid = s['logical_id']
            
            if "parent_id" in s:
                # Handle Child Component Injection
                parent_id = s["parent_id"]
                self.child_to_parent_map[eid] = parent_id
                parent = self.scene_manager.objects.get(parent_id)
                
                if parent:
                    log_debug(f"Companion: Syncing child {eid} to parent {parent_id}")
                    
                    # 1. Capture the child widget instance reference from the object canvas
                    # before updating its layout properties
                    child_obj = parent.child_widgets.get(eid)
                    if child_obj and hasattr(child_obj, "setProperty"):
                        # STATE CACHE FLUSH LAYER: If the incoming historical packet doesn't 
                        # contain custom anchoring policies, we MUST explicitly strip the leftover 
                        # future options flags out of the C++ widget memory space!
                        options = s.get("options", {})
                        
                        # Fallback to absolute/none positioning if the past frame has no layout rules
                        policy = options.get("anchor_policy", "Absolute") 
                        margin = options.get("bottom_margin", 0)
                        restrict = options.get("restrict_effects", True)
                        
                        child_obj.setProperty("ANCHOR_POLICY", policy)
                        child_obj.setProperty("BOTTOM_MARGIN", margin)
                        child_obj.setProperty("RESTRICT_EFFECTS", restrict)
                        log_debug(f"Companion: Re-syncing component property ledger trackers to: Policy={policy}, Margin={margin}")

                    parent.add_element(s)
                    
                    if hasattr(parent, "recalculate_child_layouts"):
                        log_debug(f"Companion: Forcing responsive anchor calculations on child [{eid}] post-mount.")
                        parent.recalculate_child_layouts()
                else:
                    log_debug(f"Companion: Warning - Parent {parent_id} not found for {eid}")
            
            else:
                # Handle Main Top-Level Window Container
                obj = self.scene_manager.get_or_create(eid, s.get("z_index", 0), s.get("options"))
                obj.z_index = s.get("z_index", obj.z_index)
                
                if "geometry" in s: 
                    # FIX: Read options to determine if an intentional, smooth geometric transition 
                    # is linked to this packet footprint. If so, we SKIP the hard visual layout snap 
                    # here, letting Phase B's Strategy Timeline drive the dimensions smoothly instead!
                    options = s.get("options", {})
                    has_structural_anim = "animation" in options and options["animation"] and options["animation"].get("type") in ["move", "scale"]
                    
                    if has_structural_anim:
                        log_debug(f"Companion: Active animation track detected for {eid}. Bypassing hard visual snap to preserve transition frames.")
                    else:
                        log_debug(f"Companion: Enforcing standard static script layout overrides for {eid}")
                        obj.update_geometry(s["geometry"])
                
                if not obj.widget.isVisible():
                    log_debug(f"Companion: Showing container {eid} after configuration.")
                    obj.widget.show()
        
        # Guarantee all widgets are in correct hierarchy windows positions
        self.scene_manager.sort_and_stack_widgets()

        # 4. PHASE B: EPHEMERAL INTENT DISPATCH & GLOBAL AMBIENT LOOPS

        for obj_state in target_states:
            eid = obj_state["logical_id"]
            parent_id = obj_state.get("parent_id", eid)
            
            if parent_id == eid:
                obj = self.scene_manager.objects.get(eid)
                if not obj: continue
                
                options = obj_state.get("options", {})
                loop_intent = options.get("loop_animation")
                
                # Rollback Layout Verification Gate
                is_rollback = self.last_sync_id <= self.scene_manager.last_sync_id
                if is_rollback and (not loop_intent or loop_intent.get("type") == "stop"):
                    for raw_state in target_states:
                        if raw_state["logical_id"] == eid:
                            historical_loop = raw_state.get("options", {}).get("loop_animation")
                            if historical_loop and historical_loop.get("type") != "stop":
                                loop_intent = historical_loop
                                break

                # Only spawn persistent loops here
                if loop_intent and loop_intent.get("type") != "stop":
                    l_type = loop_intent.get("type")
                    anim_key = (obj.widget, l_type)
                    active_loop = obj.active_animations.get(anim_key)
                    
                    from animation_registry import ANIMATION_REGISTRY
                    strategy = ANIMATION_REGISTRY.get(l_type)
                    
                    is_altered = True
                    if active_loop and strategy:
                        if strategy.matches_intent(active_loop, loop_intent):
                            is_altered = False
                    
                    if anim_key not in obj.active_animations or is_altered:
                        log_debug(f"Global Loop Engine: Booting persistent loop '{l_type}' for {eid}")
                        obj.execute_ephemeral_intents(eid, {"loop_animation": loop_intent}, obj_state.get("geometry", {}))

        log_debug("Companion: Sync finished.")

    def clear_single_message(self, eid):
        log_debug(f"Companion: Clearing {eid}")
        if eid in self.child_to_parent_map:
            parent_id = self.child_to_parent_map.pop(eid)
            parent = self.scene_manager.objects.get(parent_id)
            if parent: parent.remove_child(eid)
            return

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