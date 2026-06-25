from animation_strategies import MoveStrategy, ScaleStrategy, BobStrategy

ANIMATION_REGISTRY = {
    "move": MoveStrategy(),
    "scale": ScaleStrategy(),
    "bob": BobStrategy(), 
}