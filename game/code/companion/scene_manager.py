from utils import log_debug
from scene_object import SceneObject

class SceneManager:
    def __init__(self):
        log_debug("SceneManager: Initializing empty state.")
        self.objects = {} # Stores logical_id : SceneObject
        self.last_sync_id = -1

    def get_or_create(self, logical_id, z_index, options=None):
        if logical_id not in self.objects:
            log_debug(f"SceneManager: Creating container [{logical_id}]")
            self.objects[logical_id] = SceneObject(logical_id, z_index, options)
            self.objects[logical_id].widget.show()
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
        sync_id = packet["sync_id"]
        
        # FSM: Time progression logic
        if sync_id > self.last_sync_id:
            self.execute_animation(packet)
        else:
            self.execute_snap(packet)
            
        self.last_sync_id = sync_id

    def execute_snap(self, packet):
        log_debug(f"SceneManager: Executing SNAP for packet sync_id: {packet.get('sync_id')}")
        
        for obj_state in packet.get("data", []):
            eid = obj_state["logical_id"]
            geometry = obj_state.get("geometry", {})
            
            # ADD THIS LOG
            log_debug(f"SceneManager: Snapping {eid} to geometry={geometry}")
            
            parent_id = obj_state.get("parent_id", eid)
            obj = self.objects.get(parent_id)
            
            if obj:
                obj.stop_all_animations()
                
                if parent_id == eid:
                    # If this logs 'geometry={}' but you expected values, 
                    # the problem is in Ren'Py's state list!
                    obj.update_geometry(geometry)
                else:
                    obj.add_element(obj_state)

    def execute_animation(self, packet):
        """Dispatches animation intents to the relevant SceneObject."""
        for obj_state in packet.get("data", []):
            eid = obj_state["logical_id"]
            parent_id = obj_state.get("parent_id", eid)
            obj = self.objects.get(parent_id)

            if obj:
                anim_intent = obj_state.get("options", {}).get("animation", {})
                # Execute via the SceneObject's orchestration method
                obj.execute_animation_intent(eid, anim_intent, obj_state.get("geometry", {}))

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