from utils import log_debug
from scene_object import SceneObject

class SceneManager:
    def __init__(self):
        log_debug("SceneManager: Initializing empty state.")
        self.objects = {} # Stores logical_id : SceneObject

    def get_or_create(self, logical_id, z_index, options=None):
        if logical_id not in self.objects:
            log_debug(f"SceneManager: Creating container [{logical_id}]")
            self.objects[logical_id] = SceneObject(logical_id, z_index, options)
            self.objects[logical_id].widget.show()
        else:
            # Update property if it exists
            self.objects[logical_id].z_index = z_index
        return self.objects[logical_id]

    def sort_and_stack_widgets(self):
        # Sort objects by z_index ascending
        sorted_objs = sorted(self.objects.values(), key=lambda o: o.z_index)
        
        for obj in sorted_objs:
            if obj.widget:
                log_debug(f"SceneManager: Raising widget for [{obj.logical_id}] (z_index: {obj.z_index})")
                # Bringing to front brings it above previous (lower z) objects
                obj.widget.raise_()

    def clear_all(self):
        log_debug("SceneManager: Clearing all objects.")
        for obj_id in list(self.objects.keys()):
            self.remove_object(obj_id)

    def remove_object(self, logical_id):
        obj = self.objects.pop(logical_id, None)
        if obj:
            obj.widget.close()
            obj.widget.deleteLater()
            log_debug(f"SceneManager: Closed container: {logical_id}")