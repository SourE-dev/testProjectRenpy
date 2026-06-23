from utils import log_debug
from widget_factory import WidgetFactory

# ADD THIS LINE:
from window_base import MessageWindow
class SceneObject:
    def __init__(self, logical_id, z_index, options=None):
        self.logical_id = logical_id
        self.z_index = z_index
        log_debug(f"SceneObject[{self.logical_id}]: Initializing with z_index={self.z_index}")
        
        self.widget = MessageWindow(text="", options=options or {})
        self.child_widgets = {}
        self.components = []
        log_debug(f"SceneObject[{self.logical_id}]: Widget created.")

    def update_geometry(self, geom_data):
        log_debug(f"SceneObject[{self.logical_id}]: Updating geometry to {geom_data}")
        self.widget.setGeometry(
            geom_data.get("x", self.widget.x()),
            geom_data.get("y", self.widget.y()),
            geom_data.get("w", self.widget.width()),
            geom_data.get("h", self.widget.height())
        )

    def update_text(self, new_text):
        if hasattr(self.widget, 'label') and self.widget.label:
            if self.widget.label.text() != new_text:
                log_debug(f"SceneObject[{self.logical_id}]: Updating text to '{new_text}'")
                self.widget.label.setText(new_text)
                self.widget.adjustSize()
                self.widget.update()
            else:
                log_debug(f"SceneObject[{self.logical_id}]: Text unchanged, skipping update.")

    def add_element(self, element_data):
        child_id = element_data.get('logical_id', 'unknown')
        log_debug(f"SceneObject[{self.logical_id}]: Adding child element {child_id}")
        
        new_widget = WidgetFactory.create_widget(element_data)
        if new_widget:
            self.widget.content_layout.addWidget(new_widget) 
            self.child_widgets[child_id] = new_widget
            new_widget.show()
            log_debug(f"SceneObject[{self.logical_id}]: Child {child_id} successfully added to layout.")
        else:
            log_debug(f"SceneObject[{self.logical_id}]: Failed to create child widget {child_id}.")

    def remove_child(self, child_logical_id):
        log_debug(f"SceneObject[{self.logical_id}]: Attempting to remove child {child_logical_id}")
        widget = self.child_widgets.pop(child_logical_id, None)
        if widget:
            self.widget.content_layout.removeWidget(widget)
            widget.deleteLater()
            log_debug(f"SceneObject[{self.logical_id}]: Child {child_logical_id} removed and queued for deletion.")
        else:
            log_debug(f"SceneObject[{self.logical_id}]: Child {child_logical_id} not found, nothing to remove.")

    def add_component(self, component):
        log_debug(f"SceneObject[{self.logical_id}]: Attaching component: {type(component).__name__}")
        self.components.append(component)
        if hasattr(component, 'start'):
            component.start(self.widget)
            log_debug(f"SceneObject[{self.logical_id}]: Component started.")