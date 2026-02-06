"""
Centralized Model Registry
Provides a way for services to reference models from other services without circular imports.
"""

from typing import Dict, Type, Any, Optional
from sqlalchemy.orm import DeclarativeBase
import logging

logger = logging.getLogger(__name__)

class ModelRegistry:
    """Centralized registry for SQLAlchemy models across services."""
    
    def __init__(self):
        self._models: Dict[str, Type[DeclarativeBase]] = {}
        self._aliases: Dict[str, str] = {}
    
    def register(self, name: str, model_class: Type[DeclarativeBase], alias: Optional[str] = None):
        """Register a model with the registry."""
        self._models[name] = model_class
        if alias:
            self._aliases[alias] = name
        logger.debug(f"Registered model: {name} -> {model_class.__name__}")
    
    def get(self, name: str) -> Optional[Type[DeclarativeBase]]:
        """Get a model by name or alias."""
        # Check direct name first
        if name in self._models:
            return self._models[name]
        
        # Check aliases
        if name in self._aliases:
            return self._models[self._aliases[name]]
        
        logger.warning(f"Model not found in registry: {name}")
        return None
    
    def get_all(self) -> Dict[str, Type[DeclarativeBase]]:
        """Get all registered models."""
        return self._models.copy()
    
    def has(self, name: str) -> bool:
        """Check if a model is registered."""
        return name in self._models or name in self._aliases
    
    def clear(self):
        """Clear all registered models."""
        self._models.clear()
        self._aliases.clear()

# Global model registry instance
model_registry = ModelRegistry()

def register_model(name: str, model_class: Type[DeclarativeBase], alias: Optional[str] = None):
    """Convenience function to register a model."""
    model_registry.register(name, model_class, alias)

def get_model(name: str) -> Optional[Type[DeclarativeBase]]:
    """Convenience function to get a model."""
    return model_registry.get(name)

def has_model(name: str) -> bool:
    """Convenience function to check if a model exists."""
    return model_registry.has(name) 