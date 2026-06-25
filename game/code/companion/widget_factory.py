from utils import log_debug
from components import SpriteWidget, TextWidget

class WidgetFactory:
    @staticmethod
    def create_widget(element_data, parent_widget):
        kind = element_data.get('element_kind')
        options = element_data.get('options', {})
        
        log_debug(f"WidgetFactory: Instantiating element structural type: '{kind}'")
        
        if kind == "sprite":
            widget = SpriteWidget(options=options, parent=parent_widget)
            # Example Restriction: Sprites can bounce and shift, but can't change shape
            widget.setProperty("RESTRICT_ANIMATIONS", False)
            return widget
            
        elif kind == "text":
            widget = TextWidget(element_data.get('msg', ''), options, parent=parent_widget)
            # Horror rule: Block text blocks from executing standard scaling distortion tracks
            widget.setProperty("RESTRICT_EFFECTS", False) 
            return widget
            
        return None