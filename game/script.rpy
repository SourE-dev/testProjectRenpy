label start:
    "System Test Initiated."

    # 1. PERSISTENT: Spawning a fireball that should survive dialogue
    python:
        update_companion_state(
            "Persistent Fireball", 
            effect=EFFECT_FIREBALL,
            cleanup=CLEANUP_MANUAL, 
            logical_id="fireball_main", 
            scale_w=256, scale_h=256
        )

    "The fireball should be on screen now. Try rolling back to 'System Test Initiated' and coming forward again."
    "If working correctly, the fireball will NOT flicker or redraw."

    # 2. PERSISTENT: Spawning a ghost window
    python:
        update_companion_state(
            "Ghost Window", 
            effect=EFFECT_DEFAULT,
            cleanup=CLEANUP_MANUAL, 
            logical_id="ghost_window", 
            click_through=True, pos=(100, 100)
        )

    "Now we have two persistent windows."

    # 3. TRANSIENT (One-off): Spawning a window WITHOUT a logical_id
    python:
        # Since this has no logical_id, it is NOT rollback-safe.
        # If you rollback past this line, it will spawn a NEW ID/window.
        update_companion_state(
            "I am a Transient (One-off) window!", 
            effect=EFFECT_SYSTEM
        )

    "Look at the screen. You should see three windows total."
    "Roll back to the previous line: 'Now we have two persistent windows.'"
    
    "If you rolled back, the 'Transient' window should have vanished,"
    "while the 'Fireball' and 'Ghost' windows stayed perfectly still."

    # Cleanup persistent windows
    python:
        remove_companion_state_by_logic("fireball_main")
        remove_companion_state_by_logic("ghost_window")

    "Persistence test complete."
    return
label after_rollback:
    # This automatically runs whenever the user rolls back.
    # It tells the Companion to clear any stuck windows.
    $ send_event(None, clear=True)
    return
label test_companion_logic:
    # Test 1: Immediate cleanup
    $ update_companion_state("This should vanish on next click", cleanup=CLEANUP_IMMEDIATE)
    "Click to test cleanup." 

    # Test 2: Persistent manual state
    $ eid = update_companion_state("This should stay", cleanup=CLEANUP_MANUAL)
    "Still here."
    $ remove_companion_state(eid)
    "Gone now."
    return