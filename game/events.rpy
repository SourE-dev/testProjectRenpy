default companion_active_states = []
default companion_registry = {} 

init -1 python:
    import json, uuid, logging, socket, time
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("Companion")
    logger.info("Initializing Companion Event System (Deferred/Batching)...")

    # Constants
    EFFECT_DEFAULT = "default"
    sync_deferred = False 

    # --- Core Communication ---
    def send_event(clear=False):
        """Sends either the full state or a clear command to the Companion."""
        global last_sent_time, sync_deferred
        
        if clear:
            new_payload = {"event_type": "clear_all"}
        else:
            active_states = getattr(renpy.store, "companion_active_states", [])
            new_payload = {"event_type": "update", "data": list(active_states)}
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.2)
            s.connect(('127.0.0.1', 12345))
            s.sendall(json.dumps(new_payload).encode('utf-8'))
            s.close()
            logger.info(f"Sync sent to Companion: {new_payload.get('event_type')}")
        except Exception as e:
            logger.warning(f"Companion connection failed: {e}")
        
        sync_deferred = False

    def run_deferred_sync():
        global sync_deferred
        if sync_deferred:
            send_event()

    # Hook into Ren'Py's end-of-frame to bundle all changes into one packet
    config.overlay_functions.append(run_deferred_sync)

    # --- Writer-Facing API ---
    def show_effect(msg, effect=EFFECT_DEFAULT, logical_id=None, z_index=0, **kwargs):
        global companion_active_states, sync_deferred
        
        final_eid = logical_id if logical_id else str(uuid.uuid4())
        new_state = {"logical_id": final_eid, "z_index": z_index, "msg": msg, "effect": effect, "options": kwargs}
        
        # Replace existing state
        companion_active_states = [s for s in companion_active_states if s['logical_id'] != final_eid]
        companion_active_states.append(new_state)
        renpy.store.companion_active_states = companion_active_states
        
        sync_deferred = True 
        return final_eid

    def hide_effect(logical_id):
        global companion_active_states, sync_deferred
        companion_active_states[:] = [s for s in companion_active_states if s['logical_id'] != logical_id]
        sync_deferred = True

    def clear_all_effects():
        global companion_active_states, sync_deferred
        companion_active_states[:] = []
        sync_deferred = True
        # Immediate clear packet
        send_event(clear=True)

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
    def sync_after_rollback():
        global sync_deferred
        sync_deferred = True

    # Register it to the valid configuration variable
    config.after_default_callbacks.append(sync_after_rollback)
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