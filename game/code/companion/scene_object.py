from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QPoint
from utils import log_debug
from widget_factory import WidgetFactory
from window_base import MessageWindow
from animation_registry import ANIMATION_REGISTRY
from effect_registry import EFFECT_REGISTRY
class SceneObject:
    def __init__(self, logical_id, z_index, options=None):
        self.logical_id = logical_id
        self.z_index = z_index
        self.options = options or {}
        
        # Pass only options to the clean container window shell
        self.widget = MessageWindow(options=self.options)
        self.widget.hide() 
        self.child_widgets = {}
        self.active_animations = {}
        log_debug(f"DEBUG: [Lifecycle] {self.logical_id} Instance Created. Widget size: {self.widget.size()}")

    def stop_all_animations(self):
        for widget, anim in list(self.active_animations.items()):
            anim.stop()
            anim.deleteLater()
        self.active_animations.clear()
    def execute_ephemeral_intents(self, target_id, options, target_geom):
        """Dynamically discovers and executes layout animations and horror effects."""
        target_widget = self.widget if target_id == self.logical_id else self.child_widgets.get(target_id)
        if not target_widget: 
            log_debug(f"Warning: target_widget not found for ID {target_id}")
            return

        # Core visual configurations to skip over during effect sweeps
        STYLE_KEYS = ["bg_color", "border", "msg"]

        # 1. Real-time Hot-swapping update: Apply properties forward smoothly
        if target_id == self.logical_id and hasattr(target_widget, "apply_styles"):
            target_widget.apply_styles(options)

        for key, intent in options.items():
            if not intent or key in STYLE_KEYS:
                continue
                
            if key == "animation":
                effect_type = intent.get("type")
                self._dispatch_strategy(
                    target_widget, target_id, effect_type, intent, target_geom, ANIMATION_REGISTRY
                )
            elif key in EFFECT_REGISTRY:
                self._dispatch_strategy(
                    target_widget, target_id, key, intent, target_geom, EFFECT_REGISTRY
                )
            elif key == "loop_animation":
                effect_type = intent.get("type") if intent else None
                anim_key = (target_widget, "loop_animation")
                
                if effect_type == "stop" or not intent:
                    if anim_key in self.active_animations:
                        self.active_animations[anim_key].stop()
                        self.active_animations[anim_key].deleteLater()
                        self.active_animations.pop(anim_key, None)
                    target_widget.setProperty("loop_offset", QPoint(0, 0))
                else:
                    if anim_key in self.active_animations:
                        continue
                    self._dispatch_strategy(target_widget, target_id, effect_type, intent, target_geom, ANIMATION_REGISTRY)
            else:
                log_debug(f"SceneObject: Received unknown option key '{key}'. Ignoring.")
     
    def _dispatch_strategy(self, target_widget, target_id, effect_type, intent, target_geom, registry):
        log_debug(f"[Strategy Lookup] Inspecting registry for effect_type: '{effect_type}'")
        strategy = registry.get(effect_type)
        
        if strategy:
            anim_key = (target_widget, effect_type)
            
            if anim_key in self.active_animations:
                # If an uninterruptible animation is playing, do not overwrite it
                if self.active_animations[anim_key].property("uninterruptible"):
                    return
                self.active_animations[anim_key].stop()
                self.active_animations[anim_key].deleteLater()

            if not target_geom:
                target_geom = {
                    "x": target_widget.x(), "y": target_widget.y(),
                    "w": target_widget.width(), "h": target_widget.height(),
                    "target": [target_widget.x(), target_widget.y()]
                }

            if target_widget.property("canonicalPos") is None:
                target_widget.setProperty("canonicalPos", target_widget.pos())

            anim = strategy.execute(target_widget, target_geom, intent)
            if intent.get("uninterruptible", False):
                anim.setProperty("uninterruptible", True)
            self.active_animations[anim_key] = anim
            
            def on_finished():
                # FIX 4: Safety gate against C++ runtime deletion errors
                try:
                    # Check if widget still exists or has been garbage collected
                    if target_widget is None or RuntimeError: 
                        # This safely attempts a sip check if needed, 
                        # but checking objectName reference avoids the crash
                        target_widget.objectName() 
                except RuntimeError:
                    return # Exit cleanly, widget was destroyed by clear_all_effects()

                self.active_animations.pop(anim_key, None)
                if registry == ANIMATION_REGISTRY:
                    self.update_geometry(target_geom, target_id=target_id, internal_call=True) 
                
            anim.finished.connect(on_finished)
            anim.start()

    def update_geometry(self, geom_data, target_id=None, internal_call=False):
        if not geom_data: return
        
        target_id = target_id or self.logical_id
        target_widget = self.widget if target_id == self.logical_id else self.child_widgets.get(target_id)
        if not target_widget: return

        # 1. INTERCEPTION LAYER
        if not internal_call:
            for anim_key, anim in list(self.active_animations.items()):
                if anim_key[0] == target_widget and anim_key[1] in ["move", "scale"]:
                    
                    # FIX: If marked uninterruptible, don't KILL the animation track,
                    # but DO NOT return early here. Let the size updates fall through below!
                    if anim.property("uninterruptible"):
                        continue
                        
                    try:
                        anim.finished.disconnect()
                    except Exception:
                        pass
                    
                    if hasattr(anim, "endValue"):
                        prop_name = anim.propertyName().data().decode()
                        target_widget.setProperty(prop_name, anim.endValue())
                    
                    anim.stop()
                    anim.deleteLater()
                    self.active_animations.pop(anim_key, None)

        # 2. SAFETY CHECK: Only drop updates on internal completion double-fires
        if internal_call and any(key[0] == target_widget for key in self.active_animations if key[1] in ["move", "scale"]):
            return

        # 3. COORDINATE RESOLUTION
        if "target" in geom_data:
            x, y = geom_data["target"]
        else:
            x = geom_data.get("x", target_widget.x())
            y = geom_data.get("y", target_widget.y())

        # 4. APPLICATION LAYER
        if target_id == self.logical_id:
            w = geom_data.get("w", target_widget.width())
            h = geom_data.get("h", target_widget.height())
            
            # If an uninterruptible move is actively running, don't force a hard x/y position snap
            # on top of it, but DO force the w/h dimensions to counteract adjustSize()!
            is_moving = any(k[0] == target_widget and k[1] == "move" for k in self.active_animations)
            if is_moving and not internal_call:
                target_widget.resize(w, h)
            else:
                target_widget.update_window_geometry(x, y, w, h)
        else:
            if target_widget.metaObject().indexOfProperty("canonicalPos") >= 0:
                target_widget.setProperty("canonicalPos", QPoint(x, y))
            else:
                target_widget.move(x, y)
                
            if "size" in geom_data:
                w, h = geom_data["size"]
                target_widget.resize(w, h)
                
        target_widget.update()
    

    # In scene_object.py
    def add_element(self, element_data):
        child_id = element_data.get('logical_id')
        if not child_id: return
        
        geom = element_data.get("geometry") or {}
        options = element_data.get("options", {})
        
        # If it already exists, hot-swap values and adjust geometry
        if child_id in self.child_widgets:
            child_widget = self.child_widgets[child_id]
            child_widget.z_index = element_data.get("z_index", getattr(child_widget, 'z_index', 0))
            if hasattr(child_widget, "apply_styles"):
                child_widget.apply_styles(options)
                
            self.update_geometry(geom, target_id=child_id)
            return

        # Instantiate NEW child component cleanly nested inside the window container background
        new_widget = WidgetFactory.create_widget(element_data, self.widget)
        if new_widget:
            new_widget.z_index = element_data.get("z_index", 0)
            self.child_widgets[child_id] = new_widget
            
            # CRITICAL: Do NOT add it to a QVBoxLayout. Let it sit in free canvas space!
            new_widget.show()
            self.update_geometry(geom, target_id=child_id)
            self.reorder_children()
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