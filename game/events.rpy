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
        global sync_deferred
        
        # Access the persistent ID that survives rollbacks
        sync_id = get_next_sync_id()
        
        if clear:
            logger.info(f"Attempting to send: clear_all (SyncID: {sync_id})")
            new_payload = {"event_type": "clear_all", "sync_id": sync_id}
        else:
            active_states = getattr(renpy.store, "companion_active_states", [])
            logger.info(f"Attempting to send: update (Items: {len(active_states)}, SyncID: {sync_id})")
            new_payload = {
                "event_type": "update", 
                "data": list(active_states), 
                "sync_id": sync_id
            }
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3) 
            s.connect(('127.0.0.1', 12345))
            s.sendall(json.dumps(new_payload).encode('utf-8'))
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

    # --- Effect Management ---
    # --- Effect Management ---
    def show_effect(msg=None, effect=EFFECT_DEFAULT, logical_id=None, z_index=0, 
                    parent_id=None, element_kind=None, geometry=None, animation=None, **kwargs):
        global companion_active_states, sync_deferred
        
        # 1. Ensure logical_id is provided or generated
        final_eid = logical_id if logical_id else str(uuid.uuid4())
        
        # 2. Find existing state
        existing_state = next((s for s in companion_active_states if s['logical_id'] == final_eid), None)
        
        # 3. Collision Enforcement
        if existing_state and parent_id and existing_state.get("parent_id") and existing_state.get("parent_id") != parent_id:
            logger.warning(f"ID Collision! {final_eid} is moving from {existing_state.get('parent_id')} to {parent_id}")
        
        # 4. Merge Logic
        # Start with existing state if available, otherwise empty dict
        new_state = existing_state.copy() if existing_state else {}
        
        # Base updates
        new_state.update({
            "logical_id": final_eid,
            "z_index": z_index,
            "effect": effect,
            "msg": msg if msg is not None else new_state.get("msg")
        })
        
        # Preserve or update hierarchy/kind
        if parent_id: new_state["parent_id"] = parent_id
        if element_kind: new_state["element_kind"] = element_kind
        
        # Merge Geometry
        if geometry: new_state["geometry"] = geometry
        
        # Handle Options/Animation merge
        base_options = new_state.get("options", {}).copy()
        base_options.update(kwargs)
        if animation:
            base_options["animation"] = animation
        new_state["options"] = base_options
        
        # 5. Perform the update: Remove old, add updated
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

    