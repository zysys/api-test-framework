"""
Base extension classes and decorators for the Zysys API Test Framework.

This module provides the foundation for the extension system, including
the abstract base classes and decorators for creating extensions.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class Extension(ABC):
    """Base interface for all extensions"""
    
    @abstractmethod
    def process(self, block_name: str, block_value: Any, context: Dict[str, Any]) -> Any:
        """
        Transform or replace the block value with extension logic.
        
        This method can completely overwrite the original value with a new structure.
        Useful for transformative extensions that change the data format.
        
        Args:
            block_name: The name of the block being processed
            block_value: The original value of the block
            context: Dictionary containing test context (test_config, etc.)
        
        Returns:
            The transformed value (can be completely different from input)
        """
        pass
    
    @abstractmethod
    def validate(self, block_name: str, block_value: Any) -> bool:
        """
        Validate that the extension configuration is correct.
        
        This method determines if the extension can process the given configuration.
        Called before processing to ensure the input is valid.
        
        Args:
            block_name: The name of the block being validated
            block_value: The value to validate
        
        Returns:
            True if configuration is valid, False otherwise
        """
        pass

class CoreExtension(Extension):
    """Core extensions - loaded first, can be overridden"""
    pass

# Core extensions registry (auto-populated by decorators)
CORE_EXTENSIONS: Dict[str, CoreExtension] = {}

# User extensions registry (auto-populated by decorators)
USER_EXTENSIONS: Dict[str, Extension] = {}

def core_extension(name: str):
    """
    Decorator to mark core extensions.
    
    Args:
        name: The name of the extension (used for registration)
    
    Returns:
        Decorator function that registers the extension
    """
    def decorator(cls):
        if not issubclass(cls, Extension):
            raise TypeError(f"{cls.__name__} must inherit from Extension")
        
        # Register as core extension
        CORE_EXTENSIONS[name] = cls()
        return cls
    return decorator

def extension(name: str):
    """
    Decorator to register user extensions with explicit naming.
    
    All user extensions must use this decorator to specify their name.
    
    Args:
        name: The name of the extension (used for registration)
    
    Returns:
        Decorator function that registers the extension
    
    Example:
        @extension('my-custom-extension')
        class MyCustomExtension(Extension):
            pass
    """
    def decorator(cls):
        if not issubclass(cls, Extension):
            raise TypeError(f"{cls.__name__} must inherit from Extension")
        
        # Register as user extension
        USER_EXTENSIONS[name] = cls()
        return cls
    return decorator 