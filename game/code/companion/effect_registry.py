from effects_strategies import ShakeStrategy, OpacityGlitchStrategy

EFFECT_REGISTRY = {
    "shake": ShakeStrategy(),
    "glitch": OpacityGlitchStrategy(),
    # "audio_jumpscare": AudioStrategy(), # Easy to add later!
}