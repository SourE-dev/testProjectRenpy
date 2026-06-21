label start:
    "System Test Initiated: Advanced Options."

    # 1. Test Dynamic Scaling and Positioning
    "Spawning a large, centered fireball..."
    python:
        eid1 = update_companion_state(
            "Big Fireball", 
            effect=EFFECT_FIREBALL, 
            cleanup=CLEANUP_MANUAL, 
            scale_w=256, 
            scale_h=256
        )

    # 2. Test Click-Through functionality
    "Spawning a click-through persistent window in the top-left..."
    python:
        eid2 = update_companion_state(
            "I am ghost-like and unclickable", 
            effect=EFFECT_DEFAULT, 
            cleanup=CLEANUP_MANUAL, 
            click_through=True, 
            pos=(100, 100)
        )

    "You can now click through the second window to interact with the game UI behind it."

    # 3. Test Manual Cleanup of dynamic objects
    "Clearing all states now..."
    $ remove_companion_state(eid1)
    $ remove_companion_state(eid2)

    "Testing complete."
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