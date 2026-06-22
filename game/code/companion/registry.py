# widgets/registry.py
from effects import AnimatedEffect
from base import BaseEffect


# The factory map
WIDGET_MAP = {
    "default": BaseEffect,
    "animated": AnimatedEffect,  # Generic handler
}

def get_effect_class(effect_name):
    """Factory function to return the correct class."""
    return WIDGET_MAP.get(effect_name, BaseEffect)