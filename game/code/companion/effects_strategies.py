import random
from PyQt6.QtCore import QPropertyAnimation, QPoint, Qt  # <-- Added Qt here
from PyQt6.QtWidgets import QGraphicsOpacityEffect
from utils import log_debug
class EffectStrategy:
    def can_execute(self, widget) -> bool:
        if widget.property("RESTRICT_EFFECTS") == True:
            return False
        return True

class ShakeStrategy(EffectStrategy):
    def execute(self, widget, target_geom, intent):
        if not self.can_execute(widget): return None
        
        # Fall back to standard position jittering if the component isn't using structural tracks
        has_track = widget.metaObject().indexOfProperty("shakeOffset") >= 0
        property_target = b"shakeOffset" if has_track else b"pos"
        
        anim = QPropertyAnimation(widget, property_target)
        duration = intent.get("duration", 300)
        intensity = intent.get("intensity", 15)
        
        anim.setDuration(duration)
        base_pos = QPoint(0, 0) if has_track else widget.pos()
        
        anim.setKeyValueAt(0.0, base_pos)
        for i in range(1, 9):
            offset_x = random.randint(-intensity, intensity)
            offset_y = random.randint(-intensity, intensity)
            anim.setKeyValueAt(i / 10.0, base_pos + QPoint(offset_x, offset_y))
        anim.setKeyValueAt(1.0, base_pos)
        
        return anim

class OpacityGlitchStrategy(EffectStrategy):
    def execute(self, widget, target_geom, intent):
        if not self.can_execute(widget): return None
        
        # OS Windows animate windowOpacity natively. Child widgets use QGraphicsOpacityEffect.
        is_top_level = widget.windowFlags() & Qt.WindowType.WindowHint
        
        if is_top_level:
            anim = QPropertyAnimation(widget, b"windowOpacity")
        else:
            # Bind an explicit graphic proxy to safely flicker nested typography/assets
            eff = widget.graphicsEffect()
            if not eff:
                eff = QGraphicsOpacityEffect(widget)
                widget.setGraphicsEffect(eff)
            anim = QPropertyAnimation(eff, b"opacity")
            
        duration = intent.get("duration", 400)
        anim.setDuration(duration)
        anim.setKeyValueAt(0.0, 1.0)
        anim.setKeyValueAt(0.2, 0.1)
        anim.setKeyValueAt(0.4, 0.8)
        anim.setKeyValueAt(0.6, 0.0)
        anim.setKeyValueAt(0.8, 0.9)
        anim.setKeyValueAt(1.0, 1.0)
        
        return anim