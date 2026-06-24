# animation_strategies.py
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QSize

class AnimationStrategy:
    """Base class for all animation strategies."""
    def execute(self, widget, target_geom, intent):
        raise NotImplementedError("Strategy must implement execute()")

class MoveStrategy(AnimationStrategy):
    def execute(self, widget, target_geom, intent):
        anim = QPropertyAnimation(widget, b"pos")
        # Pull duration from intent, default to 500ms
        anim.setDuration(intent.get("duration", 500))
        anim.setStartValue(widget.pos())
        
        # Pull target coordinates from geometry
        target = target_geom.get("target") # Expects [x, y]
        anim.setEndValue(QPoint(target[0], target[1]))
        
        # Apply easing curve from intent, default to InOutCubic
        curve_name = intent.get("easing", "InOutCubic")
        anim.setEasingCurve(getattr(QEasingCurve.Type, curve_name))
        
        return anim

class ScaleStrategy(AnimationStrategy):
    def execute(self, widget, target_geom, intent):
        anim = QPropertyAnimation(widget, b"size")
        anim.setDuration(intent.get("duration", 500))
        anim.setStartValue(widget.size())
        
        # Pull size from geometry
        size = target_geom.get("size") # Expects [w, h]
        anim.setEndValue(QSize(size[0], size[1]))
        
        anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        return anim