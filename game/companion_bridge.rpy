init python:
    # This sends a "register" event to the Companion
    def define_animated_effect(name, image_path, frame_w=32, frame_h=32, **kwargs):
        data = {
            "class": "animated",
            "image_path": image_path,
            "frame_w": frame_w,
            "frame_h": frame_h,
            **kwargs
        }
        # Send command to Companion
        send_event(event_type="register_effect", name=name, data=data)

    def define_static_effect(name, image_path, **kwargs):
        data = {
            "class": "basic",
            "image_path": image_path,
            **kwargs
        }
        send_event(event_type="register_effect", name=name, data=data)