"""
Robust Relationship Helpers
Provides safe ways to create SQLAlchemy relationships across services.
"""

from typing import Optional, Dict, Any, Union
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from .registry import get_model, has_model

def safe_relationship(
    target_model_name: str,
    back_populates: Optional[str] = None,
    foreign_keys: Optional[str] = None,
    primaryjoin: Optional[str] = None,
    secondary: Optional[str] = None,
    secondaryjoin: Optional[str] = None,
    **kwargs
) -> relationship:
    """
    Create a safe relationship that checks if the target model exists in the registry.
    
    Args:
        target_model_name: Name of the target model (must be registered)
        back_populates: Name of the back-reference attribute
        foreign_keys: Foreign key specification
        primaryjoin: Primary join condition
        secondary: Secondary table for many-to-many
        secondaryjoin: Secondary join condition
        **kwargs: Additional relationship arguments
    
    Returns:
        SQLAlchemy relationship object
    """
    # Check if the target model exists in the registry
    if not has_model(target_model_name):
        # If model doesn't exist, create a string-based relationship
        # This allows the relationship to be resolved later when the model is available
        logger.warning(f"Target model '{target_model_name}' not found in registry, using string reference")
        return relationship(
            target_model_name,
            back_populates=back_populates,
            foreign_keys=foreign_keys,
            primaryjoin=primaryjoin,
            secondary=secondary,
            secondaryjoin=secondaryjoin,
            **kwargs
        )
    
    # Get the actual model class from the registry
    target_model = get_model(target_model_name)
    if target_model is None:
        # Fallback to string reference if model retrieval fails
        logger.warning(f"Failed to retrieve model '{target_model_name}' from registry, using string reference")
        return relationship(
            target_model_name,
            back_populates=back_populates,
            foreign_keys=foreign_keys,
            primaryjoin=primaryjoin,
            secondary=secondary,
            secondaryjoin=secondaryjoin,
            **kwargs
        )
    
    # Create relationship with the actual model class
    return relationship(
        target_model,
        back_populates=back_populates,
        foreign_keys=foreign_keys,
        primaryjoin=primaryjoin,
        secondary=secondary,
        secondaryjoin=secondaryjoin,
        **kwargs
    )

def conditional_relationship(
    target_model_name: str,
    condition: bool = True,
    **kwargs
) -> Optional[relationship]:
    """
    Create a relationship only if a condition is met.
    
    Args:
        target_model_name: Name of the target model
        condition: Whether to create the relationship
        **kwargs: Relationship arguments
    
    Returns:
        SQLAlchemy relationship object or None
    """
    if condition:
        return safe_relationship(target_model_name, **kwargs)
    return None

def lazy_relationship(
    target_model_name: str,
    **kwargs
) -> relationship:
    """
    Create a lazy-loaded relationship that resolves at runtime.
    
    Args:
        target_model_name: Name of the target model
        **kwargs: Relationship arguments
    
    Returns:
        SQLAlchemy relationship object
    """
    # Always use string reference for lazy relationships
    return relationship(
        target_model_name,
        lazy="dynamic",  # Use dynamic loading
        **kwargs
    )

# Import logger at the top level
import logging
logger = logging.getLogger(__name__) 