label start:
    "System Test Initiated."

    # 1. TEST: Linear Movement Strategy
    # We now pass the type constant and a parameters dictionary.
    python:
        update_companion_state(
            "Moving Fireball (Linear Strategy)",
            effect=EFFECT_FIREBALL,
            cleanup=CLEANUP_MANUAL,
            logical_id="fireball_move",
            movement_type=MOVE_LINEAR,
            movement_params={
                "start_pos": (100, 100),
                "end_pos": (800, 500),
                "speed": 5
            }
        )

    "The fireball should be moving using the LinearMovement strategy."
    "Try rolling back and coming forward; the state will persist correctly."
    $ remove_companion_state_by_logic("fireball_move")
    # 2. TEST: Cosine Movement Strategy
    python:
        update_companion_state(
            "Wavy Fireball",
            effect=EFFECT_FIREBALL,
            cleanup=CLEANUP_MANUAL,
            logical_id="fireball_wave",
            movement_type=MOVE_COSINE,
            movement_params={
                "start_x": 0,
                "end_x": 1000,
                "amplitude": 50,
                "frequency": 0.05
            }
        )

    # 3. PERSISTENT: Ghost Window
    python:
        update_companion_state(
            "Ghost Window",
            effect=EFFECT_DEFAULT,
            cleanup=CLEANUP_MANUAL,
            logical_id="ghost_window",
            click_through=True,
            pos=(100, 100)
        )

    "Three persistent elements are active."

    # 4. TRANSIENT (One-off)
    python:
        update_companion_state(
            "I am a Transient (One-off) window!",
            effect=EFFECT_SYSTEM
        )

    "Look at the screen. You should see four windows total."
    "Roll back to: 'Three persistent elements are active.'"

    "If working correctly, the Transient window should vanish upon rollback."

    # Cleanup persistent windows
    python:
        
        remove_companion_state_by_logic("fireball_wave")
        remove_companion_state_by_logic("ghost_window")

    "Persistence test complete."
    return

label after_rollback:
    $ send_event(None, clear=True)
    return