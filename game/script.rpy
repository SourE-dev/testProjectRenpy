label start:
    "Testing Component Architecture: Styling and Elements."

    # 1. Spawn a Styled Container
    # The 'bg_color' triggers the MessageWindow styling logic
    $ show_effect(
        msg="Styled Container", 
        logical_id="test_win", 
        geometry={"x": 100, "y": 100, "w": 300, "h": 200},
        bg_color="#0f599e",
        border="2px solid #e61f1f"
    )
    
    "Adding sprite to transparent container."

    # 3. Add the Sprite to the transparent container
    $ show_effect(
        logical_id="child_1", 
        parent_id="test_win", 
        element_kind="sprite", 
        asset_path="images/sprites/test_icon.png",
        geometry={"x": 50, "y": 50, "w": 100, "h": 100},
        z_index=3
    )
    
    "Window created and sprite loaded. Moving styled window..."
    $ show_effect(
        logical_id="child_2", 
        parent_id="test_win", 
        element_kind="sprite", 
        asset_path="images/sprites/red_fireball.png",
        geometry={"x": 60, "y": 60, "w": 100, "h": 100},
        z_index=2
    )
    "This is cool"
    # 4. Test Geometry Update
    $ show_effect(
        logical_id="test_win",
        geometry={"x": 200, "y": 200, "w": 400, "h": 300},
        msg="Container Moved & Resized"
    )
    
    "Testing child stuff"
    $ show_effect(
        logical_id="child_2", 
        parent_id="test_win", 
        element_kind="sprite", 
        asset_path="images/sprites/red_fireball.png",
        geometry={"x": 60, "y": 60, "w": 100, "h": 100},
        z_index=4
    )
    "hopefully the fireball is below now"
    
    # 5. Cleanup
    $ clear_all_effects()
    "Test complete."
    return
