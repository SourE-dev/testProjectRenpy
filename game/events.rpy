default companion_active_states = []

default companion_registry = {} 

init python:
    import json, time, threading, uuid, queue, shutil
    if 'companion_active_states' not in globals():
        companion_active_states = []
    if 'companion_registry' not in globals():
        companion_registry = {}
    # Constants
    CLEANUP_IMMEDIATE = "immediate"
    CLEANUP_MANUAL = "manual"
    EFFECT_FIREBALL = "fireball"
    EFFECT_SYSTEM = "system"
    EFFECT_DEFAULT = "default"

    event_queue = queue.Queue()
    last_processed_statement = None

    # The Command-based sync function
    def send_event(states=None, clear=False):
        # ONLY send if the state has actually changed
        new_payload = {"type": "clear_all"} if clear else {"type": "update", "data": list(companion_active_states)}
        
        # Prevent redundant writes if nothing changed
        if hasattr(send_event, "last_payload") and send_event.last_payload == new_payload:
            return
        
        send_event.last_payload = new_payload
        event_queue.put(new_payload)

    def writer_loop():
        events_file = os.path.join(config.gamedir, "code", "companion", "game_events.json")
        temp_file = events_file + ".tmp"
        while True:
            cmd = event_queue.get()
            # Clear queue of stale updates
            while not event_queue.empty():
                try: cmd = event_queue.get_nowait()
                except: break
            
            try:
                with open(temp_file, "w") as f:
                    json.dump(cmd, f)
                    f.flush()
                    os.fsync(f.fileno())
                shutil.move(temp_file, events_file)
            except Exception as e:
                print(f"DEBUG: Writer error: {e}")
            event_queue.task_done()

    # Helper functions
    def update_companion_state(msg, effect=EFFECT_DEFAULT, cleanup=CLEANUP_IMMEDIATE, logical_id=None, **kwargs):
        global companion_registry
        
        # Force Ren'Py to mark this dictionary as 'dirty' so it snapshots it
        renpy.retain_after_load() 
        
        if logical_id:
            # We copy the dict to ensure Ren'Py sees a new object reference, 
            # which forces a rollback snapshot
            new_registry = companion_registry.copy()
            if logical_id not in new_registry:
                new_registry[logical_id] = str(uuid.uuid4())
            
            # Update the registry
            companion_registry = new_registry
            final_eid = companion_registry[logical_id]
        else:
            final_eid = str(uuid.uuid4())
        
        new_state = {
            "id": final_eid, 
            "msg": msg, 
            "effect": effect, 
            "cleanup": cleanup,
            "options": kwargs
        }
        
        # 2. Check if identical state already exists (Prevents sync-flicker)
        existing = next((s for s in companion_active_states if s['id'] == final_eid), None)
        if existing:
            if existing == new_state:
                return final_eid # Nothing changed, do nothing
            companion_active_states.remove(existing)
        
        companion_active_states.append(new_state)
        send_event() 
        return final_eid

    def remove_companion_state_by_logic(logical_id):
        if logical_id in companion_registry:
            eid = companion_registry.pop(logical_id)
            remove_companion_state(eid)
    def remove_companion_state(eid):
        companion_active_states[:] = [s for s in companion_active_states if s['id'] != eid]
        send_event()

    def clear_companion_states():
        import traceback
        print("DEBUG: clear_companion_states called from:")
        traceback.print_stack() # This will show you exactly what line triggered the clear
        companion_active_states.clear()
        send_event(clear=True)

    # Change the function definition to accept the argument
    def cleanup_immediate(name=None):
        global companion_active_states, last_processed_statement
        
        # 1. Identify transient states
        immediate_states = [s for s in companion_active_states if s.get("cleanup") == CLEANUP_IMMEDIATE]
        
        if immediate_states:
            # 2. Get the current statement context
            # In Ren'Py, we can use renpy.get_return_stack() or just a counter
            current_statement = renpy.get_filename_line()
            
            # 3. Only delete if we are in a NEW statement line
            # This allows the transient window to persist through the python 
            # block that created it and the immediate 'say' statement following it.
            if last_processed_statement and last_processed_statement != current_statement:
                companion_active_states[:] = [s for s in companion_active_states if s.get("cleanup") != CLEANUP_IMMEDIATE]
                send_event()
            
            # 4. Update the tracker
            last_processed_statement = current_statement
    def force_sync_on_rollback():
        # This function runs automatically after a successful rollback
        # We trigger a full update of the companion to the current state
        send_event()
    config.after_default_callbacks.append(force_sync_on_rollback)
    config.interact_callbacks.append(cleanup_immediate)
 



label splashscreen:
    python:
        # (Your existing thread logic)
        if not any(t.name == "writer_thread" for t in threading.enumerate()):
            t = threading.Thread(target=writer_loop, name="writer_thread", daemon=True)
            t.start()
    return