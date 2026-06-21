init python:
    import json, time, threading, uuid, queue, shutil
    
    # Constants
    CLEANUP_IMMEDIATE = "immediate"
    CLEANUP_MANUAL = "manual"
    EFFECT_FIREBALL = "fireball"
    EFFECT_SYSTEM = "system"
    EFFECT_DEFAULT = "default"

    event_queue = queue.Queue()

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
    def update_companion_state(msg, effect=EFFECT_DEFAULT, cleanup=CLEANUP_MANUAL, eid=None, **kwargs):
        # If no ID is provided, generate a new one
        final_eid = eid if eid else str(uuid.uuid4())
        
        new_state = {
            "id": final_eid, 
            "msg": msg, 
            "effect": effect, 
            "cleanup": cleanup,
            "options": kwargs
        }
        
        # Check if this ID already exists to update it instead of appending
        existing = next((s for s in companion_active_states if s['id'] == final_eid), None)
        if existing:
            companion_active_states.remove(existing)
        
        companion_active_states.append(new_state)
        send_event() 
        return final_eid

    def remove_companion_state(eid):
        companion_active_states[:] = [s for s in companion_active_states if s['id'] != eid]
        send_event()

    def clear_companion_states():
        import traceback
        print("DEBUG: clear_companion_states called from:")
        traceback.print_stack() # This will show you exactly what line triggered the clear
        companion_active_states.clear()
        send_event(clear=True)

    def cleanup_immediate():
        global companion_active_states
        if any(s.get("cleanup") == CLEANUP_IMMEDIATE for s in companion_active_states):
            companion_active_states[:] = [s for s in companion_active_states if s.get("cleanup") != CLEANUP_IMMEDIATE]
            send_event()
    def force_sync_on_rollback():
        # This function runs automatically after a successful rollback
        # We trigger a full update of the companion to the current state
        send_event()
    config.after_default_callbacks.append(force_sync_on_rollback)
 

default companion_active_states = []

label splashscreen:
    python:
        if not any(t.name == "writer_thread" for t in threading.enumerate()):
            t = threading.Thread(target=writer_loop, name="writer_thread", daemon=True)
            t.start()
    return