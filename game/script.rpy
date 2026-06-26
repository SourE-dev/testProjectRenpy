# =============================================================================
#           DESKTOP COMPANION FRAMEWORK PARAMS CHEAT SHEET / API REFERENCE
# =============================================================================
#
#  show_effect() Core Parameters:
#  -----------------------------------------------------------------------------
#  logical_id      [str]  Unique engine identifier for this specific node.
#  parent_id       [str]  (Optional) Binds a child element to a container window.
#  element_kind    [str]  "text" or "sprite". Omit for main OS container shells.
#  z_index         [int]  Stacking hierarchy (Higher values render on top).
#  msg             [str]  Text message payload (Required for element_kind="text").
#
#  geometry={} Parameters:
#  -----------------------------------------------------------------------------
#  x, y            [int]  Absolute or relative top-left position layout offset.
#  w, h            [int]  Absolute pixel width and height boundaries.
#  target          [list] Absolute destination [X, Y] array used by MoveStrategy.
#  rel_x, rel_y    [float] Proportional desktop coordinates (0.0 to 1.0).
#  rel_w, rel_h    [float] Proportional screen dimensions (0.0 to 1.0).
#
#  options={} Parameters:
#  -----------------------------------------------------------------------------
#  bg_color        [str]  Hex colors ("#3a0000") or "transparent".
#  border          [str]  CSS layout rules ("3px dashed #ff0000").
#  align           [str]  Typography rendering overrides: "center" or "right".
#  anchor_policy   [str]  Child layout flow tracking: "BottomCenter", "BottomStretch", "Proportional".
#  bottom_margin   [int]  Pixel padding used for bottom anchor constraints.
#  pct_x, pct_y    [float] Bounding box center pivot anchors used by Proportional policy.
#  asset_path      [str]  Relative disk path to image assets ("images/sprites/...").
#  frame_interval  [int]  Sprite animation playback delay track (in ms).
#
#  animation={} / loop_animation={} / shake={} Sub-Intents:
#  -----------------------------------------------------------------------------
#  type            [str]  "move", "scale", "bob", "shake", "opacity_glitch", "stop".
#  duration        [int]  Total runtime duration of an interpolation lap (in ms).
#  easing          [str]  Qt easing curves ("Linear", "OutQuad", "InOutCubic").
#  uninterruptible [bool] Protects active movement from mid-transit snapshot drops.
#  amplitude       [int]  Peak distance modifier used by floating Bob loops.
#  intensity       [int]  Pixel layout jitter displacement radius used by Shake.
#
# =============================================================================
label start:

    # =========================================================================
    # PHASE 1: Solid Base Shell Instantiation + Ambient Loop Tracking
    # =========================================================================

    # 1a. Spawn the core window container shell normally using absolute pixels
    $ show_effect(
        logical_id="ghost_box", 
        geometry={"x": 400, "y": 300, "w": 300, "h": 150}
    )

    # 1b. Inject the Text child component with local boundary mappings
    $ show_effect(
        msg="I am floating...",
        element_kind="text",
        logical_id="ghost_text",
        parent_id="ghost_box",
        geometry={"x": 10, "y": 10, "w": 280, "h": 130},
        z_index=1
    )

    # 1c. Layer a persistent, infinite ambient float loop right onto the shell
    $ show_effect(
        logical_id="ghost_box",
        loop_animation={"type": "bob", "amplitude": 20, "duration": 2500}
    )

    "The window opens as a solid gray box and begins bobbing up and down gently on the screen."

    "As I progress through these dialogue choices, the window continues its ambient floating loop seamlessly without resetting on click or rolling back."


    # =========================================================================
    # PHASE 2: Concurrent Multi-Track Layering (Move + Jitter Shake)
    # =========================================================================

    # 2. Stack an Uninterruptible Absolute Move + One-Shot Shake right on top of the loop track!
    $ show_effect(
        logical_id="ghost_box",
        geometry={"target": [800, 300]},
        animation={"type": "move", "duration": 2000, "easing": "OutQuad", "uninterruptible": True},
        shake={"intensity": 10, "duration": 500}
    )

    "Look at that! It violently shuddered, glided across the desktop, all while maintaining its continuous up-and-down ambient floating cycle."
    
    "Even if you click through the text immediately, the 'uninterruptible' move instruction forces itself to finish moving to X=800 cleanly."


    # =========================================================================
    # PHASE 3: Core Transparency & Real-time Aesthetic Stylization
    # =========================================================================

    # 3a. Explicitly stop the persistent ambient loop and strip the background texture
    $ show_effect(
        logical_id="ghost_box",
        bg_color="transparent",
        loop_animation={"type": "stop"}
    )

    "The ambient hover loop terminates, the solid background vanishes, and only the white text floating directly on your desktop remains."

    # 3b. Bring back a custom tinted theme dynamically to verify hot-swapping
    # All properties are now passed directly as flat flat keyword arguments!
    $ show_effect(
        logical_id="ghost_box",
        bg_color="#3a0000",
        border="3px dashed #ff0000"
    )
    
    $ show_effect(
        msg="Bloody Baseline Activated.",
        element_kind="text",
        logical_id="ghost_text",
        parent_id="ghost_box",
        geometry={"x": 10, "y": 10, "w": 280, "h": 130} 
    )

    "The window instantly snaps into a deep red background with a dashed red border, updating its visual state instantly mid-dialogue."


    # =========================================================================
    # PHASE 4: Proportional Screen Resizing & Responsive Anchor Layouts
    # =========================================================================

    # 4a. Update the child text to use responsive bottom positioning policy via kwargs
    $ show_effect(
        msg="Locked to Bottom Boundary.",
        element_kind="text",
        logical_id="ghost_text",
        parent_id="ghost_box",
        geometry={"x": 10, "y": 10, "w": 280, "h": 50},
        anchor_policy="BottomStretch", 
        bottom_margin=20
    )

    # 4b. Execute a ScaleStrategy animation on the container shell
    $ show_effect(
        logical_id="ghost_box",
        geometry={"w": 500, "h": 350},
        animation={"type": "scale", "duration": 1200}
    )

    "Watch the responsive reflow! As the window container expands smoothly over 1.2 seconds, the text widget tracks the shifting layout bounds and rides the bottom edge."


    # =========================================================================
    # PHASE 5: Sprite Sheet Animation Processing & Resolution Independence
    # =========================================================================

    # 5a. Instantly teleport the container window to a relative percentage spot on your monitor
    $ show_effect(
        logical_id="ghost_box",
        geometry={"rel_x": 0.05, "rel_y": 0.05, "w": 200, "h": 200},
        bg_color="transparent",
        border="none"
    )
    $ hide_effect(logical_id="ghost_text")

    # 5b. Inject a loop-animated sprite character sheet using flat kwargs parameters
    $ show_effect(
        element_kind="sprite",
        logical_id="fireball_sprite",
        parent_id="ghost_box",
        geometry={"x": 0, "y": 0},
        asset_path="images/sprites/red_fireball.png",
        frame_interval=150,
        anchor_policy="Proportional",
        pct_x=0.5,
        pct_y=0.5
    )

    "Now the window has stripped its borders, resolved its location relative to your screen size cache, and initialized a multi-frame fireball sprite sheet tracking your internal timer ticks."

    # 5c. Glide the fireball window using relative coordinates to test resolution independence
    $ show_effect(
        logical_id="ghost_box",
        geometry={"rel_x": 0.75, "rel_y": 0.75},
        animation={"type": "move", "duration": 3000, "easing": "InOutCubic"}
    )

    "The sprite smoothly flies diagonally down to the bottom right quadrant of your active display screen, completely independent of the baseline monitor hardware profile."

    # Final cleanup execution command
    $ clear_all_effects()
    "Comprehensive system validation complete. All layout loops, anchor trees, and strategy registries are operating perfectly."

    return