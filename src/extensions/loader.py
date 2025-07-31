"""
Extension loader for the Zysys API Test Framework.

This module handles loading and managing extensions with precedence handling.
"""

import importlib.util
from pathlib import Path
from typing import Dict, Optional, Any
from .base import Extension, USER_EXTENSIONS
from . import CORE_EXTENSIONS

class ExtensionLoader:
    """
    Loads and manages extensions with precedence handling.
    
    This class handles:
    - Loading core extensions (built-in)
    - Auto-loading user extensions from test/extensions/
    - Resolving extensions with precedence rules
    - Processing blocks with extensions
    """
    
    def __init__(self, extensions_dir: str = "test/extensions"):
        """
        Initialize the extension loader.
        
        Args:
            extensions_dir: Directory containing user extensions
        """
        self.extensions_dir = extensions_dir
        self.core_extensions = CORE_EXTENSIONS  # Built-in core extensions
        self.user_extensions: Dict[str, Extension] = {}
        self.precedence = "non-core"  # default
    
    def load_user_extensions(self) -> None:
        """
        Load user extensions from extensions/ directory.
        
        Extensions must be registered using the @extension decorator.
        """
        if not Path(self.extensions_dir).exists():
            return
        
        # Import all Python files to register decorated extensions
        for py_file in Path(self.extensions_dir).glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            try:
                # Import the module to register any @extension decorated classes
                spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Update user extensions after module import
                self.user_extensions.update(USER_EXTENSIONS)
                
                # Check for any undecorated Extension classes and warn
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, Extension) and 
                        attr != Extension):
                        
                        # Check if this extension was registered via @extension decorator
                        if not any(type(ext) == attr for ext in self.user_extensions.values()):
                            print(f"⚠️  Extension class '{attr_name}' is not decorated with @extension. "
                                  f"Please add @extension('name') decorator.")
                        
            except Exception as e:
                print(f"❌ Failed to load extension {py_file.name}: {e}")
    
    def resolve_extension(self, extension_name: str) -> Optional[Extension]:
        """
        Resolve extension with precedence handling.
        
        Args:
            extension_name: Name of the extension to resolve
        
        Returns:
            Extension instance or None if not found
        """
        if self.precedence == "core":
            # Core extensions take priority
            return (self.core_extensions.get(extension_name) or 
                    self.user_extensions.get(extension_name))
        else:
            # Non-core extensions take priority (default)
            return (self.user_extensions.get(extension_name) or 
                    self.core_extensions.get(extension_name))
    
    def list_available_extensions(self) -> dict:
        """
        List all available extensions (core and user).
        
        Returns:
            Dictionary with 'core' and 'user' extension lists
        """
        return {
            'core': list(self.core_extensions.keys()),
            'user': list(self.user_extensions.keys()),
            'precedence': self.precedence
        }
    
    def process_block_with_extensions(self, block_name: str, block_value: Any, context: Dict[str, Any]) -> Any:
        """
        Process a block with any applicable extensions.
        
        Args:
            block_name: Name of the block (may include extension syntax)
            block_value: Value of the block
            context: Test context dictionary
        
        Returns:
            Processed value
        """
        # Check if block has extension syntax: block<extension>
        if isinstance(block_name, str) and '<' in block_name and block_name.endswith('>'):
            # Extract base name and extension
            base_name, extension_name = block_name.rsplit('<', 1)
            extension_name = extension_name.rstrip('>')
            
            # Find and apply extension
            extension = self.resolve_extension(extension_name)
            if extension:
                try:
                    return extension.process(base_name, block_value, context)
                except Exception as e:
                    print(f"❌ Extension {extension_name} failed: {e}")
                    return block_value
            else:
                print(f"⚠️  Extension {extension_name} not found")
                return block_value
        
        return block_value 