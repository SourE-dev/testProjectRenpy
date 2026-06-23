from utils import log_debug
from scene_object import SceneObject

class SceneManager:
    def __init__(self):
        log_debug("SceneManager: Initializing empty state.")
        self.objects = {} # Stores logical_id : SceneObject

    def get_or_create(self, logical_id, z_index, options=None):
        """
        Creates a new SceneObject container if it doesn't exist.
        """
        if logical_id not in self.objects:
            log_debug(f"SceneManager: Creating new SceneObject [{logical_id}] with z_index={z_index}")
            self.objects[logical_id] = SceneObject(logical_id, z_index, options)
        else:
            log_debug(f"SceneManager: Fetching existing SceneObject [{logical_id}]")
        
        return self.objects[logical_id]

    def sort_and_stack_widgets(self):
        """
        Sorts the containers by z_index and updates their visual stacking.
        """
        log_debug("SceneManager: Starting sort_and_stack_widgets.")
        
        # Sort by z_index ascending (lowest z_index at bottom, highest at top)
        sorted_objs = sorted(self.objects.values(), key=lambda o: o.z_index)
        
        for obj in sorted_objs:
            if obj.widget:
                log_debug(f"SceneManager: Raising widget for [{obj.logical_id}] (z_index: {obj.z_index})")
                obj.widget.raise_()
        
        log_debug("SceneManager: Finished stacking widgets.")