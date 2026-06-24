from PyQt6.QtWidgets import QWidget
from utils import log_debug
from widget_factory import WidgetFactory
from window_base import MessageWindow
from animation_registry import ANIMATION_REGISTRY

class SceneObject:
    def __init__(self, logical_id, z_index, options=None):
        self.logical_id = logical_id
        self.z_index = z_index
        self.options = options or {}
        
        self.widget = MessageWindow(text=self.options.get("msg", ""), options=self.options)
        self.child_widgets = {}
        self.active_animations = {}
        
        log_debug(f"SceneObject[{self.logical_id}]: Initialized.")

    def stop_all_animations(self):
        for widget, anim in list(self.active_animations.items()):
            anim.stop()
            anim.deleteLater()
        self.active_animations.clear()

    def execute_animation_intent(self, target_id, intent, target_geom):
        """Dispatches animation to the registry-based strategy system."""
        target_widget = self.widget if target_id == self.logical_id else self.child_widgets.get(target_id)
        if not target_widget: 
            return

        anim_type = intent.get("type")
        strategy = ANIMATION_REGISTRY.get(anim_type)
        
        if strategy:
            # 1. Clean up existing animation for this specific widget
            if target_widget in self.active_animations:
                self.active_animations[target_widget].stop()
                self.active_animations[target_widget].deleteLater()

            # 2. Execute via Strategy
            anim = strategy.execute(target_widget, target_geom, intent)
            
            # 3. Track and Start
            self.active_animations[target_widget] = anim
            anim.finished.connect(lambda: self.active_animations.pop(target_widget, None))
            anim.start()
        else:
            log_debug(f"SceneObject: No strategy found for animation type '{anim_type}'")
   
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
        if hasattr(self.widget, 'label'):
            self.widget.label.setText(new_text)
            self.widget.adjustSize()
            log_debug(f"SceneObject[{self.logical_id}]: Updated text to '{new_text}'")

    # In scene_object.py
    def add_element(self, element_data):
        child_id = element_data.get('logical_id')
        if not child_id: return
        
        # Clean up existing if re-added
        if child_id in self.child_widgets:
            self.remove_child(child_id)
            
        # Bind child to our container's widget
        new_widget = WidgetFactory.create_widget(element_data, parent_widget=self.widget)
        
        if new_widget:
            # Apply properties
            geom = element_data.get("geometry") or {}
            new_widget.z_index = element_data.get("z_index", 0)
            new_widget.move(geom.get("x", 0), geom.get("y", 0))
            if "w" in geom: new_widget.resize(geom["w"], geom.get("h", geom["w"]))
            
            self.child_widgets[child_id] = new_widget
            self.reorder_children()
            new_widget.show()
            log_debug(f"SceneObject[{self.logical_id}]: Added {child_id} (z_index: {new_widget.z_index})")

    def reorder_children(self):
        sorted_widgets = sorted(self.child_widgets.values(), key=lambda w: getattr(w, 'z_index', 0))
        for i in range(len(sorted_widgets) - 1):
            sorted_widgets[i].stackUnder(sorted_widgets[i+1])

    def remove_child(self, child_logical_id):
        widget = self.child_widgets.pop(child_logical_id, None)
        if widget:
            if hasattr(self.widget, 'content_layout'):
                self.widget.content_layout.removeWidget(widget)
            widget.deleteLater()