label start:
    "We are so ready!"

    # Test the linear projectile
    $ show_effect(
        "Launching Projectile!",
        effect="fast_fireball",
        logical_id="fireball_1",
        movement_params={"start_pos": (0, 300), "end_pos": (1200, 300), "speed": 40},
        scale_w=128, scale_h=128
    )
    
    "The fireball is active now."
    
    # Manually hide it before proceeding
    $ hide_effect("fireball_1")
    "Fireball 1 hidden."
    
    # Test the curved magic effect
    $ show_effect(
        "Magic Curving!",
        effect="curved_fireball",
        logical_id="fireball_2",
        movement_params={"start_pos": (200, 0), "end_pos": (800, 600), "speed": 15},
        scale_w=256, scale_h=256
    )
    
    "Registration and effects verified."
    $ hide_effect("fireball_2")
    "Fireball 2 hidden."

    # Test the third fireball
    $ show_effect(
        "Launching Projectile!",
        effect="fast_fireball",
        logical_id="fireball_3",
        movement_params={"start_pos": (0, 300), "end_pos": (1200, 300), "speed": 40},
        scale_w=128, scale_h=128
    )
    
    "Cool. Now clearing all manually."
    $ clear_all_effects()
    "Great"
    return
label after_rollback:
    $ clear_all_effects()
    return