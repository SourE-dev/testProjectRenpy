from utils import log_debug
from scene_object import SceneObject

class SceneManager:
    def __init__(self):
        log_debug("SceneManager: Initializing empty state.")
        self.objects = {} # Stores logical_id : SceneObject
        self.last_sync_id = -1

    # scene_manager.py

    def get_or_create(self, logical_id, z_index, options=None):
        if logical_id not in self.objects:
            log_debug(f"DEBUG: [Manager] Spawning {logical_id}")
            # Create object but don't show yet
            self.objects[logical_id] = SceneObject(logical_id, z_index, options)
        else:
            log_debug(f"SceneManager: Reusing existing object [{logical_id}]")
            self.objects[logical_id].z_index = z_index
        return self.objects[logical_id]

    def sort_and_stack_widgets(self):
        sorted_objs = sorted(self.objects.values(), key=lambda o: o.z_index)
        for obj in sorted_objs:
            if obj.widget:
                obj.widget.raise_()

    def process_packet(self, packet):
        sync_id = packet.get("sync_id", 0)
        
        # FORCE SNAP on Rollback
        if sync_id <= self.last_sync_id:
            log_debug(f"Manager: Rollback detected (ID {sync_id} < {self.last_sync_id}). Forcing SNAP.")
            self.execute_snap(packet)
        else:
            # Replaced execute_animation with a broader dispatcher
            self.execute_ephemeral_effects(packet)
            
        self.last_sync_id = sync_id

    def execute_snap(self, packet):
        log_debug(f"SceneManager: Executing SNAP for packet sync_id: {packet.get('sync_id')}")
        
        # 1. Sort: Process parents (containers) first so they exist before building children
        sorted_states = sorted(packet.get("data", []), key=lambda s: 0 if not s.get("parent_id") else 1)
        
        for obj_state in sorted_states:
            eid = obj_state["logical_id"]
            geometry = obj_state.get("geometry", {})
            options = obj_state.get("options", {})
            parent_id = obj_state.get("parent_id", eid)
            
            # 2. Get or create the underlying window track or structure
            obj = self.get_or_create(
                parent_id, 
                z_index=obj_state.get("z_index", 0), 
                options=options
            )
            
            obj.stop_all_animations()
            
            if parent_id == eid:
                # Handle Container Window Window Frame Properties
                if hasattr(obj.widget, "apply_styles"):
                    obj.widget.apply_styles(options)
                if geometry:
                    obj.update_geometry(geometry)
                if not obj.widget.isVisible():
                    obj.widget.show()
            else:
                # Route text/sprite configuration properties downward to children
                obj.add_element(obj_state)
    def execute_ephemeral_effects(self, packet):
        """Dispatches all one-shot ephemeral intents (animations, shakes, glitches)."""
        for obj_state in packet.get("data", []):
            eid = obj_state["logical_id"]
            parent_id = obj_state.get("parent_id", eid)
            obj = self.objects.get(parent_id)

            if obj:
                options = obj_state.get("options", {})
                if options:
                    # Pass the entire options dict down to the SceneObject
                    obj.execute_ephemeral_intents(eid, options, obj_state.get("geometry", {}))

    def clear_all(self):
        log_debug("SceneManager: Clearing all objects.")
        for obj_id in list(self.objects.keys()):
            self.remove_object(obj_id)

    def remove_object(self, logical_id):
        obj = self.objects.pop(logical_id, None)
        if obj:
            obj.stop_all_animations()
            obj.widget.close()
            obj.widget.deleteLater()
            log_debug(f"SceneManager: Closed container: {logical_id}")