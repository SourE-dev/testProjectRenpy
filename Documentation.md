# Companion Effect System API

The Companion System allows you to trigger UI effects, animations, and projectiles from Ren'Py scripts on a separate, overlay-friendly window.

## 1. Setup & Initialization
Effects must be registered in an `init python` block before they can be used in the script.

### Registering Effects
* **`define_animated_effect(name, image_path, frame_w, frame_h, **kwargs)`**
    * Registers a repeating animated sprite.
    * `name`: Unique string ID (used in `show_effect`).
    * `frame_w/h`: Pixel dimensions of a single frame on the sheet.
    * `cols`: Number of columns in your sprite sheet.
    * `total_frames`: Total number of frames to cycle through.
* **`define_static_effect(name, image_path, **kwargs)`**
    * Registers a static (non-animated) image.

---

## 2. Writer API (`show_effect`)
Use this in your Ren'Py labels to trigger UI elements.

$ show_effect(
    msg="Optional text", 
    effect="name_of_registered_effect", 
    logical_id="unique_id", 
    **options
)

### Parameters
| Parameter | Type | Description |
| :--- | :--- | :--- |
| `msg` | String | The text label (if using a static/basic effect). |
| `effect` | String | The name used when registering the effect. |
| `logical_id` | String | A unique ID used for tracking, updating, or hiding this instance. |
| `scale_w/h` | Int | Target resolution for the effect on screen (e.g., 128x128). |
| `click_through` | Bool | If `True`, the window ignores mouse clicks. |
| `auto_hide` | Bool | If `True`, the window closes automatically when movement finishes. |

### Movement Parameters
If using `movement_type` ("linear" or "cosine"), provide a `movement_params` dictionary:

* **Linear:** `movement_params={"start_pos": (x, y), "end_pos": (x, y), "speed": int}`
* **Cosine (Curved):** `movement_params={"start_pos": (x, y), "end_pos": (x, y), "amplitude": 50, "frequency": 0.05, "speed": 15}`

---

## 3. Controlling Effects
* **`hide_effect(logical_id)`**: Removes a specific effect instance by its `logical_id`.
* **`clear_all_effects()`**: Immediately wipes every active effect from the companion screen.

---

## 4. Best Practices
1.  **Unique IDs:** Always provide a `logical_id` to ensure you can reference the effect later.
2.  **Rollback Safety:** The system automatically syncs with Ren'Py's rollback. You do not need to manually handle effects after a player scrolls back.
3.  **Debouncing:** The system is throttled to ~20 updates per second. While this is invisible to the user, ensure your `show_effect` calls are logical and not placed inside standard 60FPS loops.
4.  **Performance:** If using `AnimatedEffect`, always define `scale_w` and `scale_h` to ensure the C++ backend handles image scaling efficiently.

---

## Example Usage
label start:
    # 1. Register
    $ define_animated_effect("fast_fireball", "images/sprites/red_fireball.png", frame_w=32, frame_h=32, cols=2, total_frames=2, movement_type="linear")

    # 2. Trigger
    $ show_effect(
        "Launching Projectile!",
        effect="fast_fireball",
        logical_id="fireball_1",
        movement_params={"start_pos": (0, 300), "end_pos": (1200, 300), "speed": 40},
        scale_w=128, scale_h=128
    )
    
    # 3. Clean up
    $ hide_effect("fireball_1")
    return