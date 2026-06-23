# scene_manager.py
# Import the updated SceneObject which now handles its own widget/layout
from scene_object import SceneObject

class SceneManager:
    def __init__(self):
        self.objects = {} # Stores logical_id : SceneObject

    def get_or_create(self, logical_id, z_index, options=None):
        """
        Creates a new SceneObject container if it doesn't exist.
        The SceneObject now encapsulates the MessageWindow (the container).
        """
        if logical_id not in self.objects:
            self.objects[logical_id] = SceneObject(logical_id, z_index, options)
        return self.objects[logical_id]

    def sort_and_stack_widgets(self):
        """
        Sorts the containers by z_index and updates their visual stacking.
        """
        # Sort by z_index ascending (lowest z_index at bottom, highest at top)
        sorted_objs = sorted(self.objects.values(), key=lambda o: o.z_index)
        for obj in sorted_objs:
            if obj.widget:
                obj.widget.raise_()