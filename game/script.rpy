label start:
    "Starting Layering Test with transparency and size constraints..."

    # 1. Spawn a 'background' message at Z=0
    # Added min_width to prevent shrinking on rollback
    $ show_effect("I am at the BOTTOM (Z=0)", logical_id="layer_bottom", z_index=0, bg_color="#0000FF", opacity=0.4, min_width=300)
    
    # 2. Spawn a 'foreground' message at Z=10
    $ show_effect("I am at the TOP (Z=10)", logical_id="layer_top", z_index=10, bg_color="#FF0000", opacity=0.6, min_width=300)
    
    "Both windows should be visible now. The transparency and size are now locked."

    # 3. Dynamic Re-layering Test
    "Now let's swap them. Moving TOP to Z=-1 and BOTTOM to Z=5."
    
    # The min_width ensures these windows don't shrink when text is replaced
    $ show_effect("I am now buried (Z=-1)", logical_id="layer_top", z_index=-1, bg_color="#FF0000", opacity=0.6, min_width=300)
    $ show_effect("I am now visible (Z=5)", logical_id="layer_bottom", z_index=5, bg_color="#0000FF", opacity=0.4, min_width=300)

    "The layering updated, and the window sizes remain consistent."

    $ clear_all_effects()
    "Cleanup complete."
    return

label after_rollback:
    # Explicitly clear state on rollback to trigger fresh sync
    $ clear_all_effects()
    return