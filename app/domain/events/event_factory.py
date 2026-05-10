import os
import importlib
from typing import Dict, Any, Type

from app.domain.events.base_event import BaseEvent


class EventFactory:
    """Factory for creating events from data"""
    
    def __init__(self):
        self._builders: Dict[str, Type] = {}
        self._register_default_builders()
    
    def _register_default_builders(self):
        """Dynamically load and register event builders from the builders folder"""
        builders_path = os.path.dirname(__file__) + "/builders"
        
        # Skip base_builder.py and __init__.py
        excluded_files = {"__init__.py", "base_builder.py"}
        
        for filename in os.listdir(builders_path):
            if filename.endswith(".py") and filename not in excluded_files:
                module_name = filename[:-3]  # Remove .py extension
                full_module_name = f"app.domain.events.builders.{module_name}"
                
                try:
                    module = importlib.import_module(full_module_name)
                    
                    # Find EventBuilder classes in the module
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            hasattr(attr, 'event_type') and 
                            attr_name.endswith('Builder') and
                            attr_name != 'EventBuilder'):
                            
                            builder_instance = attr()
                            self._builders[builder_instance.event_type] = builder_instance
                            print(f"✅ Loaded event builder: {attr_name} -> {builder_instance.event_type}")
                            
                except Exception as e:
                    print(f"❌ Failed to load builder from {filename}: {e}")
    
    def register_builder(self, builder):
        """Register a new event builder"""
        self._builders[builder.event_type] = builder
    
    def create_event(self, event_type: str, data: Dict[str, Any]) -> BaseEvent:
        """Create an event from the given type and data"""
        builder = self._builders.get(event_type)
        
        if not builder:
            raise ValueError(f"Unknown event type: {event_type}")
        
        return builder.build(data)
    
    def get_supported_events(self) -> list[str]:
        """Get list of supported event types"""
        return list(self._builders.keys())


# Global event factory instance
event_factory = EventFactory()
