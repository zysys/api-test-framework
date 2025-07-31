"""
Extensions module for Zysys API Test Framework.

This module provides the extension system that allows users to customize
how test configurations are processed and validated.
"""

from .base import Extension, CoreExtension, core_extension, extension, CORE_EXTENSIONS, USER_EXTENSIONS
from .loader import ExtensionLoader
from .multiple import MultipleExtension
from .encoded_values import EncodedValuesExtension

# Auto-load all core extensions
# The @core_extension decorator automatically registers them in CORE_EXTENSIONS
# when the modules are imported above

# Create a clean interface for accessing all extensions
def get_core_extensions() -> dict:
    """Get all registered core extensions"""
    return CORE_EXTENSIONS.copy()

def get_extension(name: str):
    """Get a specific core extension by name"""
    return CORE_EXTENSIONS.get(name)

def list_core_extensions() -> list:
    """List all available core extension names"""
    return list(CORE_EXTENSIONS.keys())

__all__ = [
    'Extension',
    'CoreExtension', 
    'core_extension',
    'extension',
    'ExtensionLoader',
    'MultipleExtension',
    'EncodedValuesExtension',
    'get_core_extensions',
    'get_extension', 
    'list_core_extensions',
    'CORE_EXTENSIONS',
    'USER_EXTENSIONS'
] 