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
        self.widget.lifecycle_owner = self # <-- Pass self back as owner reference
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
        target_widget = self.widget if target_id == self.logical_id else self.child_widgets.get(target_id)
        if not target_widget: 
            log_debug(f"INTENT DEBUG: Target widget '{target_id}' not found in active scene objects pool.")
            return

        STYLE_KEYS = ["bg_color", "border", "msg"]

        if target_id == self.logical_id and hasattr(target_widget, "apply_styles"):
            target_widget.apply_styles(options)

        log_debug(f"INTENT DEBUG: Evaluating incoming intents for [{target_id}]. Content: {list(options.keys())}")

        for key, intent in options.items():
            if not intent or key in STYLE_KEYS:
                continue
                
            log_debug(f"INTENT DEBUG: Processing key slot -> '{key}' with intent payload: {intent}")
                
            if key == "animation":
                effect_type = intent.get("type")
                log_debug(f"INTENT DEBUG: Dispatching animation category. Sub-type rule: '{effect_type}'")
                self._dispatch_strategy(target_widget, target_id, effect_type, intent, target_geom, ANIMATION_REGISTRY)
            elif key in EFFECT_REGISTRY:
                self._dispatch_strategy(target_widget, target_id, key, intent, target_geom, EFFECT_REGISTRY)
                
            elif key == "loop_animation":
                effect_type = intent.get("type") if intent else None
                if effect_type == "stop" or not intent:
                    for anim_key, anim in list(self.active_animations.items()):
                        if anim_key[0] == target_widget and (anim_key[1] == "bob" or getattr(anim, 'propertyName', lambda: b'')() == b"loop_offset"):
                            try:
                                anim.stop()
                                anim.deleteLater()
                            except Exception:
                                pass
                            self.active_animations.pop(anim_key, None)
                    if hasattr(target_widget, "setProperty"):
                        target_widget.setProperty("loop_offset", QPoint(0, 0))
                        if hasattr(target_widget, "_compose_absolute_position"):
                            target_widget._compose_absolute_position()
                else:
                    self._dispatch_strategy(target_widget, target_id, effect_type, intent, target_geom, ANIMATION_REGISTRY)

    def _dispatch_strategy(self, target_widget, target_id, effect_type, intent, target_geom, registry):
        strategy = registry.get(effect_type)
        if not strategy: 
            log_debug(f"STRATEGY ERROR: Lookup failed for type token '{effect_type}' inside registry target.")
            return

        anim_key = (target_widget, effect_type)
        log_debug(f"STRATEGY DEBUG: Target verified. Key mapping: {anim_key}. Registry lookup successful.")
        
        if anim_key in self.active_animations:
            old_anim = self.active_animations.pop(anim_key, None)
            if old_anim:
                if old_anim.property("uninterruptible"):
                    log_debug(f"STRATEGY BLOCKED: Active animation slot '{effect_type}' is protected as uninterruptible.")
                    self.active_animations[anim_key] = old_anim
                    return
                try:
                    old_anim.stop()
                    old_anim.deleteLater()
                except Exception:
                    pass

        if not target_geom:
            target_geom = {
                "x": target_widget.x(), "y": target_widget.y(),
                "w": target_widget.width(), "h": target_widget.height(),
                "target": [target_widget.x(), target_widget.y()]
            }

        if target_widget.property("canonicalPos") is None:
            target_widget.setProperty("canonicalPos", target_widget.pos())

        # Let's verify if the strategy file successfully returns an initialized timeline
        anim = strategy.execute(target_widget, target_geom, intent)
        if not anim: 
            log_debug(f"STRATEGY WARNING: Strategy handler class failed to generate a QPropertyAnimation instance.")
            return 
        
        if intent.get("uninterruptible", False):
            anim.setProperty("uninterruptible", True)
            
        self.active_animations[anim_key] = anim
        log_debug(f"STRATEGY SUCCESS: Sparking timeline for type: '{effect_type}' lasting {anim.duration()}ms")
        
        def on_finished():
            try:
                target_widget.objectName() 
            except RuntimeError:
                return
            self.active_animations.pop(anim_key, None)
            if registry == ANIMATION_REGISTRY and effect_type != "bob":
                self.update_geometry(target_geom, target_id=target_id, internal_call=True) 
            
        anim.finished.connect(on_finished)
        anim.start()

    def update_geometry(self, geom_data, target_id=None, internal_call=False):
        if not geom_data: return
        
        target_id = target_id or self.logical_id
        target_widget = self.widget if target_id == self.logical_id else self.child_widgets.get(target_id)
        if not target_widget: return

        # =========================================================================
        # 1. INTERCEPTION LAYER & DUPLICATE PACKET GUARD
        # =========================================================================
        if not internal_call:
            for anim_key, anim in list(self.active_animations.items()):
                if anim_key[0] == target_widget and anim_key[1] in ["move", "scale"]:
                    
                    # --- DUPLICATE PACKET PROTECTION ---
                    # Check if the running animation is already heading toward this exact size
                    if anim_key[1] == "scale" and hasattr(anim, "endValue"):
                        target_w = geom_data.get("w", target_widget.width())
                        target_h = geom_data.get("h", target_widget.height())
                        if anim.endValue().width() == target_w and anim.endValue().height() == target_h:
                            # It's a duplicate layout payload! Let the animation run cleanly.
                            continue

                    # Check if the running animation is already heading toward this exact position
                    if anim_key[1] == "move" and hasattr(anim, "endValue"):
                        target_pos = geom_data.get("target") or [geom_data.get("x", target_widget.x()), geom_data.get("y", target_widget.y())]
                        if anim.endValue().x() == target_pos[0] and anim.endValue().y() == target_pos[1]:
                            # Duplicate position payload! Ignore hard snap.
                            continue
                    
                    # --- STANDARD INTERCEPTION ---
                    if anim.property("uninterruptible"):
                        continue
                        
                    try:
                        anim.finished.disconnect()
                    except Exception:
                        pass
                    
                    if hasattr(anim, "endValue"):
                        prop_name = anim.propertyName().data().decode()
                        target_widget.setProperty(prop_name, anim.endValue())
                        if prop_name == "size":
                            target_widget.setProperty("canonicalSize", anim.endValue())
                    
                    anim.stop()
                    anim.deleteLater()
                    self.active_animations.pop(anim_key, None)

        # =========================================================================
        # 2. SAFETY CHECK: Only drop updates on internal completion double-fires
        # =========================================================================
        if internal_call and any(key[0] == target_widget for key in self.active_animations if key[1] in ["move", "scale"]):
            return

        # =========================================================================
        # 3. HIGH-PERFORMANCE COORDINATE RESOLUTION VIA CACHE LOOKUP
        # =========================================================================
        if target_id == self.logical_id and "rel_x" in geom_data and "rel_y" in geom_data:
            # Safely crawl up the widget context chain to find the Companion container instance properties
            companion_engine = target_widget.window()
            
            # Read straight from the super-fast memory cache variables we set up on boot
            base_x = getattr(companion_engine, "screen_x", 0)
            base_y = getattr(companion_engine, "screen_y", 0)
            width_scalar = getattr(companion_engine, "screen_w", 1920)
            height_scalar = getattr(companion_engine, "screen_h", 1080)
            
            # Map percentages cleanly onto the actual resolution space
            x = int(base_x + (width_scalar * geom_data["rel_x"]))
            y = int(base_y + (height_scalar * geom_data["rel_y"]))
        elif "target" in geom_data:
            x, y = geom_data["target"]
        else:
            x = geom_data.get("x", target_widget.x())
            y = geom_data.get("y", target_widget.y())

        # =========================================================================
        # 4. APPLICATION LAYER & BACKUP PROPERTY CACHE RE-SYNC
        # =========================================================================
        if target_id == self.logical_id:
            w = geom_data.get("w", target_widget.width())
            h = geom_data.get("h", target_widget.height())
            
            is_moving = any(k[0] == target_widget and k[1] == "move" for k in self.active_animations)
            if is_moving and not internal_call:
                target_widget.resize(w, h)
            else:
                target_widget.update_window_geometry(x, y, w, h)
            
            # STATE FIX: Force absolute tracking properties to update alongside changes.
            # This handles hard snaps during rollback recovery frames cleanly!
            from PyQt6.QtCore import QSize, QPoint
            target_widget.setProperty("canonicalSize", QSize(w, h))
            target_widget.setProperty("canonicalPos", QPoint(x, y))
        else:
            # CHILD COMPONENT LAYOUT TRACK
            if target_widget.metaObject().indexOfProperty("canonicalPos") >= 0:
                target_widget.setProperty("canonicalPos", QPoint(x, y))
            else:
                target_widget.move(x, y)
                
            w, h = target_widget.width(), target_widget.height()
            if "size" in geom_data:
                w, h = geom_data["size"]
                target_widget.resize(w, h)
            elif "w" in geom_data and "h" in geom_data:
                w, h = geom_data["w"], geom_data["h"]
                target_widget.resize(w, h)
                
            # Mirror layout tracking context properties down onto internal children
            from PyQt6.QtCore import QSize
            target_widget.setProperty("canonicalSize", QSize(w, h))
                
        target_widget.update()

    # In scene_object.py
    def add_element(self, element_data):
        child_id = element_data.get('logical_id')
        if not child_id: return
        
        geom = element_data.get("geometry") or {}
        options = element_data.get("options", {})
        msg_content = element_data.get("msg") # <-- FIX: Grab top-level message text
        
        # Update existing child component
        if child_id in self.child_widgets:
            child_widget = self.child_widgets[child_id]
            child_widget.z_index = element_data.get("z_index", getattr(child_widget, 'z_index', 0))
            
            if hasattr(child_widget, "apply_styles"):
                child_widget.apply_styles(options)
                
            # FIX: Ensure existing text gets hot-swapped dynamically
            if hasattr(child_widget, "update_text") and msg_content:
                child_widget.update_text(msg_content)
                
            # FIX: Pass internal_call=True so sub-element snaps do not kill parent window tracks
            self.update_geometry(geom, target_id=child_id, internal_call=True)
            return

        # Instantiate NEW child component
        new_widget = WidgetFactory.create_widget(element_data, self.widget)
        if new_widget:
            new_widget.z_index = element_data.get("z_index", 0)
            self.child_widgets[child_id] = new_widget
            
            if hasattr(new_widget, "update_text") and msg_content:
                new_widget.update_text(msg_content)
            
            new_widget.show()
            self.update_geometry(geom, target_id=child_id, internal_call=True)
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
    def recalculate_child_layouts(self):
        """Iterates over all internal child elements and adjusts their positions 
        relative to the parent window's real-time dimensions."""
        parent_w = self.widget.width()
        parent_h = self.widget.height()

        for child_id, child_widget in self.child_widgets.items():
            policy = child_widget.property("ANCHOR_POLICY")
            if not policy:
                continue # Default static positioning if no policy is set
                
            current_w = child_widget.width()
            current_h = child_widget.height()
            
            # --- ANCHOR PATTERN RESOLUTION ---
            if policy == "BottomCenter":
                # Keep centered horizontally, lock to bottom margin edge
                margin = child_widget.property("BOTTOM_MARGIN") or 10
                new_x = int((parent_w - current_w) / 2)
                new_y = int(parent_h - current_h - margin)
                child_widget.move(new_x, new_y)
                
            elif policy == "BottomStretch":
                # Stretches across the bottom of the screen (like a dialogue box)
                margin = child_widget.property("BOTTOM_MARGIN") or 10
                padding_x = 15
                new_w = parent_w - (padding_x * 2)
                new_x = padding_x
                new_y = int(parent_h - current_h - margin)
                child_widget.setGeometry(new_x, new_y, new_w, current_h)
                
            elif policy == "Proportional":
                # True percentage mapping (useful for character sprites)
                # Expects values between 0.0 and 1.0 cached on creation
                pct_x = child_widget.property("PCT_X") or 0.5
                pct_y = child_widget.property("PCT_Y") or 0.5
                
                new_x = int(parent_w * pct_x - (current_w / 2))
                new_y = int(parent_h * pct_y - (current_h / 2))
                child_widget.move(new_x, new_y)