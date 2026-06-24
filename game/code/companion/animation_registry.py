# animation_registry.py
from animation_strategies import MoveStrategy, ScaleStrategy

ANIMATION_REGISTRY = {
    "move": MoveStrategy(),
    "scale": ScaleStrategy(),
    # Adding a new animation is now just one line:
    # "shake": ShakeStrategy(), 
}