from utils import log_debug
from components import SpriteWidget, TextWidget

# The Extension Registry: Map string keys directly to class definitions
COMPONENT_REGISTRY = {
    "sprite": SpriteWidget,
    "text": TextWidget,
    # Adding a new component type later is now just one line:
    # "video": VideoWidget,
}

class WidgetFactory:
    @staticmethod
    def create_widget(element_data, parent_widget):
        kind = element_data.get('element_kind')
        options = element_data.get('options', {})
        
        log_debug(f"WidgetFactory: Instantiating structural element type: '{kind}'")
        
        widget_class = COMPONENT_REGISTRY.get(kind)
        if not widget_class:
            log_debug(f"WidgetFactory: Unknown element type '{kind}'. Ignoring.")
            return None

        # Standard signature construction
        if kind == "text":
            # Text requires an initial string buffer matching your signature
            widget = widget_class(element_data.get('msg', ''), options, parent=parent_widget)
        else:
            widget = widget_class(options=options, parent=parent_widget)

        # --- DYNAMIC CONFIGURATION DELEGATION ---
        # Instead of long hardcoded conditional statements, handle policies via payload variables
        if kind == "text":
            widget.setProperty("ANCHOR_POLICY", options.get("anchor_policy", "BottomCenter"))
            widget.setProperty("BOTTOM_MARGIN", options.get("bottom_margin", 15))
            widget.setProperty("RESTRICT_EFFECTS", False)
        elif kind == "sprite":
            widget.setProperty("ANCHOR_POLICY", options.get("anchor_policy", "Proportional"))
            widget.setProperty("PCT_X", options.get("pct_x", 0.5))
            widget.setProperty("PCT_Y", options.get("pct_y", 0.5))
            widget.setProperty("RESTRICT_ANIMATIONS", False)

        return widget