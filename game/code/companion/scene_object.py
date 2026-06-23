from utils import log_debug
from widget_factory import WidgetFactory
from window_base import MessageWindow

class SceneObject:
    def __init__(self, logical_id, z_index, options=None):
        self.logical_id = logical_id
        self.z_index = z_index
        self.options = options or {}
        
        # Initialize the shell container
        self.widget = MessageWindow(text=self.options.get("msg", ""), options=self.options)
        self.child_widgets = {}
        
        log_debug(f"SceneObject[{self.logical_id}]: Container initialized.")

    def update_geometry(self, geom_data):
        if not geom_data: return
        log_debug(f"SceneObject[{self.logical_id}]: Updating geometry to {geom_data}")
        self.widget.setGeometry(
            geom_data.get("x", self.widget.x()),
            geom_data.get("y", self.widget.y()),
            geom_data.get("w", self.widget.width()),
            geom_data.get("h", self.widget.height())
        )
        self.widget.update()
    def update_text(self, new_text):
        """Updates the text inside the shell and adjusts window size."""
        # Check if the MessageWindow has an internal label
        if hasattr(self.widget, 'label'):
            self.widget.label.setText(new_text)
            self.widget.adjustSize()
            log_debug(f"SceneObject[{self.logical_id}]: Updated text to '{new_text}'")
        else:
            log_debug(f"SceneObject[{self.logical_id}]: Warning - No label to update.")
    def add_element(self, element_data):
        child_id = element_data.get('logical_id')
        if not child_id: return
        
        # Clean up existing if re-added
        if child_id in self.child_widgets:
            self.remove_child(child_id)
            
        new_widget = WidgetFactory.create_widget(element_data, parent_widget=self.widget)
        
        if new_widget:
            # 1. Extract geometry
            geom = element_data.get("geometry") or {}
            x = geom.get("x", 0)
            y = geom.get("y", 0)
            w = geom.get("w") # Keep as None if not provided
            h = geom.get("h")
            
            # 2. Apply position
            new_widget.move(x, y)
            
            # 3. Apply size if provided
            if w is not None and h is not None:
                new_widget.resize(w, h)
            
            self.child_widgets[child_id] = new_widget
            new_widget.show()
            log_debug(f"SceneObject[{self.logical_id}]: Added {child_id} at ({x}, {y}) size ({w}, {h})")
        else:
            log_debug(f"SceneObject: Failed to create_widget for {child_id}")
    def remove_child(self, child_logical_id):
        widget = self.child_widgets.pop(child_logical_id, None)
        if widget:
            self.widget.content_layout.removeWidget(widget)
            widget.deleteLater() 
            log_debug(f"SceneObject[{self.logical_id}]: Cleaned up {child_logical_id}")