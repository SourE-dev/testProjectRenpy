label start:
    "Testing Containers and Shell/Content Architecture."

    # 1. Spawn a Container (The Shell)
    $ show_effect(
        msg="Container Alpha", 
        logical_id="test_win", 
        geometry={"x": 100, "y": 100, "w": 300, "h": 200},
        bg_color="#333333"
    )
    
    "Adding child to the container."

    # 2. Add a child (Sprite/Element)
    $ show_effect(
        logical_id="child_1", 
        parent_id="test_win", 
        element_kind="sprite", 
        asset_path="images/sprites/test_icon.png"
    )
    
    "Window created at 100,100. Moving window via Ren'Py command..."
    
    # 3. Test Stateless Geometry (Commanding position)
    $ show_effect(
        logical_id="test_win",
        geometry={"x": 500, "y": 300, "w": 400, "h": 300},
        msg="Container Alpha (Moved)"
    )
    
    "Window moved to 500,300. Now let's trigger a rollback."
    
    # 4. State Update
    $ show_effect(
        msg="Container Alpha (Updated Text)",
        logical_id="test_win",
        geometry={"x": 500, "y": 300, "w": 400, "h": 300}
    )
    
    "Cleanup test: The next line will clear the specific window."
    
    # Correct API Usage for removing a single element
    $ hide_effect("test_win") 
    
    "Cleanup test: The next line will clear everything."
    
    # Correct API Usage for clearing everything
    $ clear_all_effects()
    "Cool"
    return
   
label after_rollback:
    # This label is a safety hook if your project uses rollback handlers
    $ clear_all_effects()
    return