init -1 python:
    # --- Engine Infrastructure ---
    companion_registry = {}

    def _add_to_registry(name, data):
        companion_registry[name] = data

    # --- Artist/Writer-Facing Registration Functions ---
    def register_animated(name, image_path, frame_w=32, frame_h=32, cols=1, total_frames=1, movement_type="linear"):
        _add_to_registry(name, {
            "class": "animated", "image_path": image_path, "frame_w": frame_w, 
            "frame_h": frame_h, "cols": cols, "total_frames": total_frames, "movement_type": movement_type
        })

    def register_static(name, image_path):
        _add_to_registry(name, {"class": "basic", "image_path": image_path})

    # --- Auto-Sync Logic ---
    def auto_register_effects():
        if getattr(renpy.store, "_companion_registered", False):
            return
        for name, data in companion_registry.items():
            send_event(event_type="register_effect", name=name, data=data)
        renpy.store._companion_registered = True

    config.start_callbacks.append(auto_register_effects)