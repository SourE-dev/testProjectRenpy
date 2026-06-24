label start:
    "Testing Component Architecture: Animation Strategies."

    # 1. Spawn a Styled Container
    $ show_effect(
        msg="Moving Window", 
        logical_id="test_win", 
        geometry={"x": 100, "y": 100, "w": 300, "h": 200},
        bg_color="#0f599e"
    )
    
    "Ready to move."

    # 2. Test Move Animation (Strategy: MoveStrategy)
    $ show_effect(
        logical_id="test_win",
        geometry={"target": [400, 300]}, # Target for move animation
        animation={"type": "move", "duration": 1000, "easing": "OutBounce"}
    )
    
    "Window moved with bounce effect."

    # 3. Add Sprite and Test Scaling (Strategy: ScaleStrategy)
    $ show_effect(
        logical_id="child_1", 
        parent_id="test_win", 
        element_kind="sprite", 
        asset_path="images/sprites/test_icon.png",
        geometry={"x": 50, "y": 50, "size": [100, 100]},
        z_index=3
    )
    "pause"
    $ show_effect(
        logical_id="child_1",
        geometry={"size": [200, 200]}, # Grow it!
        animation={"type": "scale", "duration": 500}
    )

    "Sprite scaled up."

    # 5. Cleanup
    $ clear_all_effects()
    "Test complete."
    return