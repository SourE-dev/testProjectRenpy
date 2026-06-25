from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QSize, Qt 
from utils import log_debug

class AnimationStrategy:
    """Base class providing permission verification gates and structural logging."""
    def can_execute(self, widget) -> bool:
        # Check explicit restrictions. If a widget sets a block flag, deny it.
        if widget.property("RESTRICT_ANIMATIONS") == True:
            return False
        return True

    def execute(self, widget, target_geom, intent):
        raise NotImplementedError("Strategy must implement execute()")

class MoveStrategy(AnimationStrategy):
    def execute(self, widget, target_geom, intent):
        if not self.can_execute(widget):
            log_debug(f"ANIMATION BLOCK: Target class {widget.__class__.__name__} rejected 'move'.")
            return None

        # NATIVE AUTO-DETECTION LAYER
        # Top-level windows use our tracking architecture; children use standard relative canvas pos
        is_top_level = widget.windowFlags() & Qt.WindowType.WindowHint
        property_target = b"canonicalPos" if is_top_level else b"pos"
        
        anim = QPropertyAnimation(widget, property_target)
        anim.setDuration(intent.get("duration", 500))
        
        if is_top_level:
            anim.setStartValue(widget.property("canonicalPos") or widget.pos())
            target = target_geom.get("target")
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
        if not self.can_execute(widget): return None
        
        anim = QPropertyAnimation(widget, b"size")
        anim.setDuration(intent.get("duration", 500))
        anim.setStartValue(widget.size())
        
        size = target_geom.get("size") or [target_geom.get("w", 100), target_geom.get("h", 100)]
        anim.setEndValue(QSize(size[0], size[1]))
        anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        return anim

class BobStrategy(AnimationStrategy):
    def execute(self, target_widget, target_geom, intent):
        if not self.can_execute(target_widget): return None
        
        # Safety filter: Bob requires our vector offset pipeline
        if target_widget.metaObject().indexOfProperty("loop_offset") < 0:
            log_debug(f"ANIMATION BLOCK: {target_widget.__class__.__name__} missing loop_offset property track.")
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
        return anim