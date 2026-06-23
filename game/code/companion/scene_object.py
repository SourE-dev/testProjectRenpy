# scene_object.py
from PyQt6.QtWidgets import QVBoxLayout
from window_base import MessageWindow
from widget_factory import WidgetFactory # Your new factory
from utils import log_debug
class SceneObject:
    def __init__(self, logical_id, z_index, options=None):
        self.logical_id = logical_id
        self.z_index = z_index
        self.widget = MessageWindow(text="", options=options or {})
        self.child_widgets = {}
        self.components = [] # Ensure this exists for your brains
    def update_geometry(self, geom_data):
        """Stateless: Ren'Py sets the state, Companion enforces it."""
        self.widget.setGeometry(
            geom_data.get("x", self.widget.x()),
            geom_data.get("y", self.widget.y()),
            geom_data.get("w", self.widget.width()),
            geom_data.get("h", self.widget.height())
        )
    def update_text(self, new_text):
        """Safely updates the text of the internal label."""
        if hasattr(self.widget, 'label') and self.widget.label:
            if self.widget.label.text() != new_text:
                self.widget.label.setText(new_text)
                self.widget.adjustSize()
                self.widget.update()
    def add_element(self, element_data):
        from widget_factory import WidgetFactory
        new_widget = WidgetFactory.create_widget(element_data)
        if new_widget:
            # IMPORTANT: Add to content_widget's layout, NOT the shell
            self.widget.layout.addWidget(new_widget) 
            self.child_widgets[element_data['logical_id']] = new_widget
            new_widget.show()
    def remove_child(self, child_logical_id):
        # Now this will successfully find the attribute
        widget = self.child_widgets.pop(child_logical_id, None)
        if widget:
            self.widget.layout().removeWidget(widget)
            widget.deleteLater()
    def add_component(self, component):
        """Attaches a logic 'Brain' to the container."""
        self.components.append(component)
        if hasattr(component, 'start'):
            # Some components need the widget (Body) to operate
            component.start(self.widget)