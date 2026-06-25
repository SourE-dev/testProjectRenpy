default companion_active_states = []

init -1 python:
    import json, uuid, logging, socket, time
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("Companion")
    logger.info("--- Initializing Companion Event System (Logging Enabled) ---")

    # Constants
    EFFECT_DEFAULT = "default"
    sync_deferred = False 
    
    # --- EXTENSIBILITY REGISTRY ---
    # Any key listed here will be purged from persistent state immediately after sending
    EPHEMERAL_OPTIONS = ["animation", "shake", "glitch", "sound_cue", "force_focus"] 
    if not hasattr(renpy.store, "_companion_sync_id"):
        renpy.store._companion_sync_id = 0

    def get_next_sync_id():
        renpy.store._companion_sync_id += 1
        return renpy.store._companion_sync_id
    
    def dump_state(label):
        """Helper to print a complete snapshot of the current state."""
        active_states = getattr(renpy.store, "companion_active_states", [])
        logger.info(f"[{label}] State Dump (Count: {len(active_states)})")
        
        for i, s in enumerate(active_states):
            # We use json.dumps for clean, readable serialization of the entire dict
            # indent=None keeps it on one line per entry for log readability
            state_str = json.dumps(s, sort_keys=True)
            logger.info(f"  [{i}] Full State: {state_str}")
    # --- Core Communication ---
    def send_event(clear=False):
        """Sends the state with a persistent sync_id to ensure order of operations."""
        global sync_deferred, companion_active_states
        
        sync_id = get_next_sync_id()
        payload_str = ""
        
        if clear:
            logger.info(f"Attempting to send: clear_all (SyncID: {sync_id})")
            new_payload = {"event_type": "clear_all", "sync_id": sync_id}
            payload_str = json.dumps(new_payload)
        else:
            logger.info(f"Attempting to send: update (Items: {len(companion_active_states)}, SyncID: {sync_id})")
            new_payload = {
                "event_type": "update", 
                "data": list(companion_active_states), 
                "sync_id": sync_id
            }
            
            # 1. Serialize the payload WITH the ephemeral events included
            payload_str = json.dumps(new_payload)
            
            # 2. EXTENSIBLE CLEANUP: Scrub ephemeral data from persistent state
            for state in companion_active_states:
                if "options" in state:
                    for ephemeral_key in EPHEMERAL_OPTIONS:
                        if ephemeral_key in state["options"]:
                            # Remove it so it never fires on the next sync
                            state["options"].pop(ephemeral_key)
                            logger.debug(f"Purged ephemeral key '{ephemeral_key}' from {state['logical_id']}")
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3) 
            s.connect(('127.0.0.1', 12345))
            s.sendall(payload_str.encode('utf-8'))
            s.close()
            logger.info(f"Successfully sent event: {new_payload.get('event_type')}")
        except Exception as e:
            logger.error(f"Companion connection failed: {e}")
        
        sync_deferred = False

    def run_deferred_sync():
        global sync_deferred
        if sync_deferred:
            dump_state("DEFERRED_SYNC_TRIGGERED")
            send_event()

    config.overlay_functions.append(run_deferred_sync)

    def show_effect(msg=None, effect=EFFECT_DEFAULT, logical_id=None, z_index=0, 
                    parent_id=None, element_kind=None, geometry=None, **kwargs):
        global companion_active_states, sync_deferred
        
        final_eid = logical_id if logical_id else str(uuid.uuid4())
        existing_state = next((s for s in companion_active_states if s['logical_id'] == final_eid), None)
        
        # 1. Clean decoupling & state normalization
        if existing_state:
            new_state = {
                "logical_id": existing_state["logical_id"],
                "z_index": existing_state.get("z_index", 0),
                "effect": existing_state.get("effect", EFFECT_DEFAULT),
                "msg": existing_state.get("msg")
            }
            if "parent_id" in existing_state: new_state["parent_id"] = existing_state["parent_id"]
            if "element_kind" in existing_state: new_state["element_kind"] = existing_state["element_kind"]
            
            new_state["geometry"] = dict(existing_state.get("geometry", {}))
            new_state["options"] = dict(existing_state.get("options", {}))
            
            # Notice we no longer need to manually pop 'animation' here, 
            # send_event already scrubbed it on the last tick!
            
            if "target" in new_state["geometry"]:
                t_x, t_y = new_state["geometry"].pop("target")
                new_state["geometry"]["x"] = t_x
                new_state["geometry"]["y"] = t_y
        else:
            new_state = {
                "geometry": {},
                "options": {}
            }
        
        # 2. Apply fresh arguments for this tick
        new_state.update({
            "logical_id": final_eid,
            "z_index": z_index if z_index != 0 or "z_index" not in new_state else new_state["z_index"],
            "effect": effect,
        })
        if msg is not None: new_state["msg"] = msg
        if parent_id: new_state["parent_id"] = parent_id
        if element_kind: new_state["element_kind"] = element_kind

        if geometry:
            new_state["geometry"].update(geometry)
            
        # Merge options/styling properties AND any new ephemeral events passed in via kwargs
        new_state["options"].update(kwargs)
        
        # 3. Swap state collection in-place
        companion_active_states[:] = [s for s in companion_active_states if s['logical_id'] != final_eid]
        companion_active_states.append(new_state)
        
        dump_state("AFTER_SHOW_EFFECT")
        sync_deferred = True 
        return final_eid
    def hide_effect(logical_id):
        global companion_active_states, sync_deferred
        logger.info(f"hide_effect called: ID={logical_id}")
        companion_active_states[:] = [s for s in companion_active_states if s['logical_id'] != logical_id]
        
        dump_state("AFTER_HIDE_EFFECT")
        sync_deferred = True

    def clear_all_effects():
        global companion_active_states, sync_deferred
        logger.info("clear_all_effects called")
        companion_active_states[:] = []
        
        dump_state("AFTER_CLEAR_ALL")
        sync_deferred = True
        send_event(clear=True)

    # --- Infrastructure ---
    def sync_after_rollback():
        logger.warning("Rollback detected! Forcing full state resync.")
        global sync_deferred
        sync_deferred = True
        dump_state("AFTER_ROLLBACK")

    config.after_default_callbacks.append(sync_after_rollback)

    