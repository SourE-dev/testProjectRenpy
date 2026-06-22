default companion_active_states = []
default companion_registry = {} 

init -1 python:
    import json, time, threading, uuid, queue, shutil, logging, sys

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("Companion")
    logger.info("Initializing Companion Event System...")

    # Constants
    CLEANUP_IMMEDIATE = "immediate"
    CLEANUP_MANUAL = "manual"
    EFFECT_FIREBALL = "fireball"
    EFFECT_SYSTEM = "system"
    EFFECT_DEFAULT = "default"
    MOVE_LINEAR = "linear"
    MOVE_COSINE = "cosine"

    # Use the module itself to hold the queue, so it isn't part of Ren'Py's save data
    module = sys.modules[__name__]
    if not hasattr(module, "_event_queue"):
        module._event_queue = queue.Queue()
        
    last_processed_statement = None

    def send_event(states=None, clear=False):
        new_payload = {"type": "clear_all"} if clear else {"type": "update", "data": list(companion_active_states)}
        
        # Check against last_payload stored on the function itself (this is safe from pickling)
        if hasattr(send_event, "last_payload") and send_event.last_payload == new_payload:
            return
        
        send_event.last_payload = new_payload
        logger.info(f"Queuing event: {new_payload['type']}")
        module._event_queue.put(new_payload)

    def writer_loop():
        events_file = os.path.join(config.gamedir, "code", "companion", "game_events.json")
        temp_file = events_file + ".tmp"
        logger.info("Writer thread started.")
        
        while True:
            cmd = module._event_queue.get()
            while not module._event_queue.empty():
                try: cmd = module._event_queue.get_nowait()
                except: break
            
            try:
                with open(temp_file, "w") as f:
                    json.dump(cmd, f)
                    f.flush()
                    os.fsync(f.fileno())
                shutil.move(temp_file, events_file)
            except Exception as e:
                logger.error(f"Writer error: {e}")
            module._event_queue.task_done()

    # Helper functions
    def update_companion_state(msg, effect=EFFECT_DEFAULT, cleanup=CLEANUP_IMMEDIATE, logical_id=None, **kwargs):
        renpy.retain_after_load() 
        
        if logical_id:
            new_registry = companion_registry.copy()
            if logical_id not in new_registry:
                new_registry[logical_id] = str(uuid.uuid4())
            companion_registry.update(new_registry)
            final_eid = companion_registry[logical_id]
        else:
            final_eid = str(uuid.uuid4())
        
        new_state = {"id": final_eid, "msg": msg, "effect": effect, "cleanup": cleanup, "options": kwargs}
        
        existing = next((s for s in companion_active_states if s['id'] == final_eid), None)
        if existing and existing == new_state:
            return final_eid
            
        if existing: companion_active_states.remove(existing)
        companion_active_states.append(new_state)
        logger.info(f"State updated: {logical_id or final_eid}")
        send_event() 
        return final_eid

    def remove_companion_state(eid):
        companion_active_states[:] = [s for s in companion_active_states if s['id'] != eid]
        logger.info(f"State removed: {eid}")
        send_event()
    def remove_companion_state_by_logic(logical_id):
        global companion_registry
        if logical_id in companion_registry:
            eid = companion_registry.pop(logical_id)
            remove_companion_state(eid)
            logger.info(f"Logic state removed: {logical_id}")

    def cleanup_immediate(name=None):
        global last_processed_statement
        immediate_states = [s for s in companion_active_states if s.get("cleanup") == CLEANUP_IMMEDIATE]
        if immediate_states:
            current_statement = renpy.get_filename_line()
            if last_processed_statement and last_processed_statement != current_statement:
                companion_active_states[:] = [s for s in companion_active_states if s.get("cleanup") != CLEANUP_IMMEDIATE]
                logger.info("Transient states cleared via immediate cleanup.")
                send_event()
            last_processed_statement = current_statement

    config.after_default_callbacks.append(lambda: send_event())
    config.interact_callbacks.append(cleanup_immediate)

label splashscreen:
    python:
        # Check if the thread is already running without storing the object in the store
        if not any(thread.name == "writer_thread" for thread in threading.enumerate()):
            logger.info("Spawning writer thread.")
            # Start the thread directly without assigning it to a variable
            threading.Thread(target=writer_loop, name="writer_thread", daemon=True).start()
    return