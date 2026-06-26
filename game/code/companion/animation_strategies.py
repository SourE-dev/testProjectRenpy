from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QSize, Qt 
from utils import log_debug
from window_base import MessageWindow

class AnimationStrategy:
    def can_execute(self, widget) -> bool:
        if widget.property("RESTRICT_ANIMATIONS") == True:
            return False
        return True

    def verify_property_track(self, widget, property_name: str) -> bool:
        """Centralized check to ensure target widget contains the required Qt property track."""
        if widget.metaObject().indexOfProperty(property_name) < 0:
            from utils import log_debug
            log_debug(f"ANIMATION BLOCK: {widget.__class__.__name__} missing critical property tracking: '{property_name}'")
            return False
        return True

    def matches_intent(self, active_anim, new_intent) -> bool:
        return False

    def execute(self, widget, target_geom, intent):
        raise NotImplementedError("Strategy must implement execute()")

class MoveStrategy(AnimationStrategy):
    def execute(self, widget, target_geom, intent):
        if not self.can_execute(widget):
            log_debug(f"ANIMATION BLOCK: Target class {widget.__class__.__name__} rejected 'move'.")
            return None

        # NATIVE AUTO-DETECTION: Check if it's our top-level container class
        is_top_level = isinstance(widget, MessageWindow)
        property_target = b"canonicalPos" if is_top_level else b"pos"
        
        anim = QPropertyAnimation(widget, property_target)
        anim.setDuration(intent.get("duration", 500))
        
        if is_top_level:
            anim.setStartValue(widget.property("canonicalPos") or widget.pos())
            target = target_geom.get("target")
            if target:
                anim.setEndValue(QPoint(target[0], target[1]))
        else:
            anim.setStartValue(widget.pos())
            target = target_geom.get("target") or [target_geom.get("x", 0), target_geom.get("y", 0)]
            anim.setEndValue(QPoint(target[0], target[1]))
            
        curve_name = intent.get("easing", "InOutCubic")
        anim.setEasingCurve(getattr(QEasingCurve.Type, curve_name, QEasingCurve.Type.InOutCubic))
        
        log_debug(f"Strategy EXECUTE: Moving {widget.__class__.__name__} via '{property_target.decode()}'")
        return anim
class ScaleStrategy(AnimationStrategy):
    def execute(self, widget, target_geom, intent):
        if not self.can_execute(widget): 
            log_debug("SCALE STRATEGY: Execution rejected by can_execute guard.")
            return None
        
        is_top_level = isinstance(widget, MessageWindow)
        log_debug(f"SCALE STRATEGY: Sparking calculation for target class: {widget.__class__.__name__} (IsTopLevel={is_top_level})")
        
        # 1. EVALUATE ORIGINAL BASELINE SIZE
        current_live_size = widget.size()
        cached_canonical_size = widget.property("canonicalSize")
        
        log_debug(f"SCALE STRATEGY: Current live widget.size() metrics: {current_live_size.width()}x{current_live_size.height()}")
        if cached_canonical_size:
            log_debug(f"SCALE STRATEGY: Found cached property 'canonicalSize': {cached_canonical_size.width()}x{cached_canonical_size.height()}")
        else:
            log_debug("SCALE STRATEGY: Cached property 'canonicalSize' is empty (None).")

        # Live transition interception check
        old_size = None
        if hasattr(widget, "lifecycle_owner") and widget.lifecycle_owner:
            active_anims = widget.lifecycle_owner.active_animations
            current_scale_anim = active_anims.get((widget, "scale"))
            
            if current_scale_anim and current_scale_anim.state() == QPropertyAnimation.State.Running:
                old_size = current_live_size
                log_debug(f"SCALE STRATEGY INTERCEPT: Active running timeline caught! Sampling live transition frames: {old_size.width()}x{old_size.height()}")

        if old_size is None:
            old_size = cached_canonical_size if cached_canonical_size is not None else current_live_size
            
        # 2. RESOLVE TARGET DESTINATION SIZE
        if is_top_level and "rel_w" in target_geom and "rel_h" in target_geom:
            companion_engine = widget.window()
            screen_w = getattr(companion_engine, "screen_w", 1920)
            screen_h = getattr(companion_engine, "screen_h", 1080)
            target_w = int(screen_w * target_geom["rel_w"])
            target_h = int(screen_h * target_geom["rel_h"])
            end_size = QSize(target_w, target_h)
            log_debug(f"SCALE STRATEGY: Proportional resolution mapping resolved to: {target_w}x{target_h} based on screen {screen_w}x{screen_h}")
        else:
            size = target_geom.get("size") or [target_geom.get("w", 100), target_geom.get("h", 100)]
            end_size = QSize(size[0], size[1])
            log_debug(f"SCALE STRATEGY: Direct pixel configuration targets parsed: {end_size.width()}x{end_size.height()}")
            
        # 3. BUILD INTERPOLATION TIMELINE
        anim = QPropertyAnimation(widget, b"size")
        anim.setDuration(intent.get("duration", 500))
        anim.setStartValue(old_size)
        anim.setEndValue(end_size)
        anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        log_debug(f"SCALE STRATEGY COMPLETE: Vector Track Map -> From ({anim.startValue().width()}x{anim.startValue().height()}) TO ({anim.endValue().width()}x{anim.endValue().height()}) over {anim.duration()}ms")
        
        # Assign structural backup records
        widget.setProperty("canonicalSize", end_size)
        
        return anim

class BobStrategy(AnimationStrategy):
    def matches_intent(self, active_anim, new_intent) -> bool:
        if not active_anim: return False
        if active_anim.property("strategy_type") != "bob": return False
        
        old_amp = active_anim.property("amplitude")
        old_dur = active_anim.property("duration")
        
        new_amp = new_intent.get("amplitude", 15)
        new_dur = new_intent.get("duration", 2000)
        
        return old_amp == new_amp and old_dur == new_dur

    def execute(self, target_widget, target_geom, intent):
        if not self.can_execute(target_widget): return None
        
        # Centralized check verifies loop_offset is available natively
        if not self.verify_property_track(target_widget, "loop_offset"):
            return None

        amplitude = intent.get("amplitude", 15)
        duration = intent.get("duration", 2000)
        
        anim = QPropertyAnimation(target_widget, b"loop_offset")
        anim.setDuration(duration)
        anim.setStartValue(QPoint(0, 0))
        anim.setKeyValueAt(0.5, QPoint(0, -amplitude))
        anim.setEndValue(QPoint(0, 0))
        anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        anim.setLoopCount(-1)
        
        # Cache parameter state maps dynamically for snap verification tracking
        anim.setProperty("strategy_type", "bob")
        anim.setProperty("amplitude", amplitude)
        anim.setProperty("duration", duration)
        
        return anim