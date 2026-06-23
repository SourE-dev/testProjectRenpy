default companion_active_states = []
default companion_registry = {} 


init -1 python:
    import json, uuid, logging, socket, time
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("Companion")
    logger.info("--- Initializing Companion Event System (Logging Enabled) ---")

    # Constants
    EFFECT_DEFAULT = "default"
    sync_deferred = False 
    class SyncManager:
        def __init__(self):
            self.id = 0
            
    # Persistent container for the ID
    if not hasattr(renpy.store, "_companion_sync_manager"):
        renpy.store._companion_sync_manager = SyncManager()
    def dump_state(label):
        """Helper to print a clean snapshot of the current state."""
        active_states = getattr(renpy.store, "companion_active_states", [])
        logger.info(f"[{label}] State Dump (Count: {len(active_states)})")
        for i, s in enumerate(active_states):
            logger.info(f"  [{i}] ID: {s.get('logical_id')} | Parent: {s.get('parent_id')} | Msg: {s.get('msg')}")

    # --- Core Communication ---
    def send_event(clear=False):
        """Sends the state with a persistent sync_id to ensure order of operations."""
        global sync_deferred
        
        # Access the persistent ID that survives rollbacks
        mgr = renpy.store._companion_sync_manager
        mgr.id += 1 
        
        if clear:
            logger.info(f"Attempting to send: clear_all (SyncID: {mgr.id})")
            new_payload = {"event_type": "clear_all", "sync_id": mgr.id}
        else:
            active_states = getattr(renpy.store, "companion_active_states", [])
            logger.info(f"Attempting to send: update (Items: {len(active_states)}, SyncID: {mgr.id})")
            new_payload = {
                "event_type": "update", 
                "data": list(active_states), 
                "sync_id": mgr.id
            }
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5) 
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
    def show_effect(msg=None, effect=EFFECT_DEFAULT, logical_id=None, z_index=0, 
                    parent_id=None, element_kind=None, geometry=None, **kwargs):
        global companion_active_states, sync_deferred
        
        final_eid = logical_id if logical_id else str(uuid.uuid4())
        logger.info(f"show_effect called: ID={final_eid}, msg={msg}, parent={parent_id}")
        
        new_state = {
            "logical_id": final_eid, 
            "z_index": z_index, 
            "msg": msg, 
            "effect": effect,
            "geometry": geometry, 
            "options": kwargs
        }
        if parent_id: new_state["parent_id"] = parent_id
        if element_kind: new_state["element_kind"] = element_kind
        
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

    # --- Registration & Engine Infrastructure ---
    def _add_to_registry(name, data):
        companion_registry[name] = data

    def register_animated(name, image_path, frame_w=32, frame_h=32, cols=1, total_frames=1, movement_type="linear"):
        _add_to_registry(name, {
            "class": "animated", "image_path": image_path, "frame_w": frame_w, 
            "frame_h": frame_h, "cols": cols, "total_frames": total_frames, "movement_type": movement_type
        })

    def register_static(name, image_path):
        _add_to_registry(name, {"class": "basic", "image_path": image_path})
    # 1. Add this function to handle the post-rollback sync
    # --- Registration & Engine Infrastructure ---
    def auto_register_effects():
        if getattr(renpy.store, "_companion_registered", False):
            return
        for name, data in companion_registry.items():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.2)
                s.connect(('127.0.0.1', 12345))
                s.sendall(json.dumps({"event_type": "register_effect", "name": name, "data": data}).encode('utf-8'))
                s.close()
            except: pass
        renpy.store._companion_registered = True

    config.start_callbacks.append(auto_register_effects)