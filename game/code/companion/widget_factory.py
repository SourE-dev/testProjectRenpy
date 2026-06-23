from utils import log_debug
from components import SpriteWidget, TextWidget
# widget_factory.py
class WidgetFactory:
    @staticmethod
    def create_widget(element_data, parent_widget):
        kind = element_data.get('element_kind')
        options = element_data.get('options', {})
        
        log_debug(f"WidgetFactory: Creating {kind} with options {options}")
        
        if kind == "sprite":
            return SpriteWidget(options=options, parent=parent_widget) # This now matches the signature above
        elif kind == "text":
            return TextWidget(element_data.get('msg', ''), options)
        return None