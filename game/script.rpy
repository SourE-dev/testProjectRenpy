label start:

    # =========================================================================
    # PHASE 1: Default Solid Gray Base + Ambient Loop Testing
    # =========================================================================

    # 1a. Spawn the window container shell normally
    $ show_effect(
        logical_id="ghost_box", 
        geometry={"x": 400, "y": 300, "w": 300, "h": 150}
    )

    # 1b. Inject the Text child component explicitly inside the window container
    $ show_effect(
        msg="I am floating...",
        element_kind="text",
        logical_id="ghost_text",
        parent_id="ghost_box",
        z_index=1
    )

    # 2. Inject a persistent ambient float loop directly to the window shell
    $ show_effect(
        logical_id="ghost_box",
        loop_animation={"type": "bob", "amplitude": 20, "duration": 2500}
    )

    "The window opens as a solid gray box and begins bobbing up and down gently on the screen."

    "As I progress through these dialogue choices, the window continues its ambient floating loop seamlessly without resetting on click."


    # =========================================================================
    # PHASE 2: Concurrent Animation Layering (Uninterruptible Move + Shake)
    # =========================================================================

    # 3. Stack an Uninterruptible Absolute Move + One-Shot Shake right on top of the loop!
    $ show_effect(
        logical_id="ghost_box",
        geometry={"target": [800, 300]},
        animation={"type": "move", "duration": 2000, "easing": "OutQuad", "uninterruptible": True},
        shake={"intensity": 10, "duration": 500}
    )

    "Look at that! It violently shuddered, glided across the screen, all while maintaining its continuous up-and-down ambient floating cycle."
    
    "Even if you click through the text immediately, the 'uninterruptible' move instruction forces itself to finish moving to X=800 cleanly."


    # =========================================================================
    # PHASE 3: Core Transparency & Real-time Stylization Testing
    # =========================================================================

    # 4. Explicitly stop the persistent ambient loop and strip the background texture
    $ show_effect(
        logical_id="ghost_box",
        bg_color="transparent",
        loop_animation={"type": "stop"}
    )

    "The ambient hover loop terminates, the solid background vanishes, and only the white text floating directly on your desktop remains."

    # 5. Bring back a custom tinted theme dynamically to verify hot-swapping
    # We update the container aesthetics, and then push a text content update to the child node
    $ show_effect(
        logical_id="ghost_box",
        bg_color="#3a0000",
        border="3px dashed #ff0000"
    )
    $ show_effect(
        msg="Bloody Baseline Activated.",
        element_kind="text",
        logical_id="ghost_text",
        parent_id="ghost_box"
    )

    "The window instantly snaps into a deep red background with a dashed red border, updating its visual state instantly mid-dialogue."

    "Awesome."
    
    $ clear_all_effects()
    return