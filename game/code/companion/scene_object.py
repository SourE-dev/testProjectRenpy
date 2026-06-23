# scene_object.py
from window_base import MessageWindow

class SceneObject:
    def __init__(self, obj_id, z_index=0):
        self.widget = MessageWindow() # A clean, dumb widget
        self.components = []
        self.z_index = z_index

    def add_component(self, component):
        self.components.append(component)
        # If the component needs to start (like animation), trigger it
        if hasattr(component, 'start'):
            component.start(self.widget)