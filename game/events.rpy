init python:
    import json, time, threading, uuid, queue, shutil
    is_in_interaction = False
    # Constants
    CLEANUP_IMMEDIATE = "immediate"
    CLEANUP_MANUAL = "manual"
    CLEANUP_TIMER = "timer"
    EFFECT_FIREBALL = "fireball"
    EFFECT_SYSTEM = "system"
    EFFECT_DEFAULT = "default"

    # Observable Class to auto-sync on change
    class ObservableList(list):
        def append(self, item):
            super().append(item)
            sync_companion()
        def __setitem__(self, index, value):
            super().__setitem__(index, value)
            sync_companion()
        def clear(self):
            super().clear()
            sync_companion()
        def remove_by_id(self, eid):
            global companion_active_states
            companion_active_states[:] = [s for s in self if s['id'] != eid]
            sync_companion()

    event_queue = queue.Queue()

    def writer_loop():
        events_file = os.path.join(renpy.config.basedir, "game_events.json")
        temp_file = events_file + ".tmp"
        
        while True:
            latest_state = event_queue.get() 
            # Clear queue of old snapshots
            while not event_queue.empty():
                try: latest_state = event_queue.get_nowait()
                except: break

            print(f"DEBUG: Ren'Py attempting to write: {latest_state}") # ADD THIS
            
            try:
                with open(temp_file, "w") as f:
                    json.dump(latest_state, f)
                    f.flush()
                    os.fsync(f.fileno())
                shutil.move(temp_file, events_file)
                print("DEBUG: File write successful.") # ADD THIS
            except Exception as e:
                print(f"DEBUG: Writer error: {e}")
            
            event_queue.task_done()

    def sync_companion():
        event_queue.put(list(companion_active_states))

    def update_companion_state(msg, effect=EFFECT_DEFAULT, cleanup=CLEANUP_MANUAL):
        new_state = {"id": str(uuid.uuid4()), "msg": msg, "effect": effect, "cleanup": cleanup}
        companion_active_states.append(new_state)
        return new_state["id"]

    def remove_companion_state(eid):
        companion_active_states.remove_by_id(eid)

    def clear_companion_states():
        companion_active_states.clear()

    # Callbacks
    renpy.after_rollback = sync_companion

    def process_cleanup_after_interaction():
        global companion_active_states
        
        # Only cleanup if we are NOT currently spawning new fireballs
        # (This relies on the fact that Ren'Py processes statements in order)
        new_list = [s for s in companion_active_states if s.get("cleanup") != CLEANUP_IMMEDIATE]
        # Performance note. If need more performance precompute len(companion_active_states) as global variable and only assign if changed.
        if len(new_list) != len(companion_active_states):
            print(f"DEBUG: Cleanup triggered, removing {len(companion_active_states) - len(new_list)} items.")
            companion_active_states[:] = new_list
            
    config.interact_callbacks.append(process_cleanup_after_interaction)

# IMPORTANT: Define the variable outside init python so Ren'Py tracks it for saves/rollback
default companion_active_states = ObservableList()
label splashscreen:
    python:
        if not any(t.name == "writer_thread" for t in threading.enumerate()):
            t = threading.Thread(target=writer_loop, name="writer_thread", daemon=True)
            t.start()
            print("DEBUG: Writer thread started.")
    return
