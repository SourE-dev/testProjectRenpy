default companion_active_states = []
default companion_registry = {} 

init -1 python:
    import json, uuid, logging, socket, time
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("Companion")
    logger.info("Initializing Companion Event System (Debounced/Manual)...")

    # Constants
    EFFECT_DEFAULT = "default"
    MOVE_LINEAR = "linear"
    MOVE_COSINE = "cosine"
    DEBOUNCE_INTERVAL = 0.05  # 50ms throttle to prevent socket flooding
    
    last_sent_time = 0

    def send_event(event_type=None, name=None, data=None, clear=False):
        global last_sent_time
        
        # 1. Debounce Logic: Skip rapid-fire spam, but allow 'clear' commands
        current_time = time.time()
        if not clear and (current_time - last_sent_time) < DEBOUNCE_INTERVAL:
            return
        last_sent_time = current_time

        active_states = getattr(renpy.store, "companion_active_states", [])
        
        if clear:
            new_payload = {"event_type": "clear_all"}
        elif event_type == "register_effect":
            new_payload = {"event_type": "register_effect", "name": name, "data": data}
        else:
            new_payload = {"event_type": "update", "data": list(active_states)}
            
        # Optional: Prevent redundant network traffic
        if hasattr(send_event, "last_payload") and send_event.last_payload == new_payload and not clear:
            return
        send_event.last_payload = new_payload
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.1) # Tightened timeout to prevent game stutter
            s.connect(('127.0.0.1', 12345))
            s.sendall(json.dumps(new_payload).encode('utf-8'))
            s.close()
            logger.info(f"Event sent via TCP: {new_payload['event_type']}")
        except Exception as e:
            logger.warning(f"Companion not connected: {e}")

    # Writer-Facing API
    def show_effect(msg, effect=EFFECT_DEFAULT, logical_id=None, **kwargs):
        """Displays an effect on screen. Must be hidden manually."""
        final_eid = logical_id if logical_id else str(uuid.uuid4())
        
        new_state = {
            "logical_id": final_eid, 
            "msg": msg, 
            "effect": effect, 
            "options": kwargs
        }
        
        # Replace existing if logical_id is reused
        existing = next((s for s in companion_active_states if s['logical_id'] == final_eid), None)
        if existing: companion_active_states.remove(existing)
            
        companion_active_states.append(new_state)
        logger.info(f"Effect shown: {final_eid}")
        send_event() 
        return final_eid

    def hide_effect(logical_id):
        """Removes an effect by its logical_id."""
        global companion_active_states
        
        initial_len = len(companion_active_states)
        companion_active_states[:] = [s for s in companion_active_states if s['logical_id'] != logical_id]
        
        if len(companion_active_states) < initial_len:
            logger.info(f"Effect hidden: {logical_id}")
            send_event()
        else:
            logger.warning(f"Attempted to hide non-existent effect: {logical_id}")

    def clear_all_effects():
        """Force wipes all effects from the companion screen."""
        global companion_active_states
        companion_active_states[:] = []
        logger.info("All effects cleared manually.")
        send_event(clear=True)

    # Rollback/Load Sync: Ensure companion matches the game timeline
    def sync_companion_after_rollback():
        send_event()

    config.after_default_callbacks.append(lambda: send_event())
    # config.after_rollback_callbacks.append(sync_companion_after_rollback)