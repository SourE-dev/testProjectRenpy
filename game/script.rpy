label start:
    "System Test Initiated."

    "Test 1: Multi-Instance Handling (Immediate Cleanup)"
    "Spawning two fireball instances..."
    # Fireballs use CLEANUP_IMMEDIATE, so they clear on the next interaction
    $ eid1 = update_companion_state("Fireball 1!", effect=EFFECT_FIREBALL, cleanup=CLEANUP_IMMEDIATE)
    $ eid2 = update_companion_state("Fireball 2!", effect=EFFECT_FIREBALL, cleanup=CLEANUP_IMMEDIATE)
    
    # Because they are CLEANUP_IMMEDIATE, the next line click will trigger 
    # process_cleanup_after_interaction and wipe them.
    "Two windows should have appeared. They will vanish when you click to continue."

    "Test 2: Persistent State & Manual Clear"
    # Using CLEANUP_MANUAL means they stay until you explicitly remove them
    $ eid = update_companion_state("I am persistent.", effect=EFFECT_DEFAULT, cleanup=CLEANUP_MANUAL)
    "A window is visible. Clearing manually now..."
    $ remove_companion_state(eid)
    "Window should be gone."

    "Test 3: Rollback & Automatic Cleanup Simulation"
    "Spawning a persistent window that will survive interaction..."
    $ eid = update_companion_state("Rollback/Cleanup Test", effect=EFFECT_SYSTEM, cleanup=CLEANUP_MANUAL)
    
    "If you rollback now (Mouse Wheel Up), the window should disappear."
    "Because the state is tracked by Ren'Py, the companion will undo the spawn."
    
    "Finally, clearing all states..."
    $ clear_companion_states()
    "All windows should be gone."
    
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