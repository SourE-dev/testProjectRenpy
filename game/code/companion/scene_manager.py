# scene_manager.py
from window_base import MessageWindow

class SceneObject:
    def __init__(self, logical_id, z_index, widget, effect_instance):
        self.logical_id = logical_id
        self.z_index = z_index
        self.widget = widget
        self.effect = effect_instance

class SceneManager:
    def __init__(self):
        self.objects = {} # Stores logical_id : SceneObject

    def get_or_create(self, logical_id, z_index, widget, effect):
        if logical_id not in self.objects:
            self.objects[logical_id] = SceneObject(logical_id, z_index, widget, effect)
        return self.objects[logical_id]

    def sort_and_stack_widgets(self):
        # Sort by z_index ascending (lowest z_index at bottom, highest at top)
        sorted_objs = sorted(self.objects.values(), key=lambda o: o.z_index)
        for obj in sorted_objs:
            if obj.widget:
                obj.widget.raise_()