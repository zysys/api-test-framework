# Extension Example
# This file demonstrates how to create user extensions using the @extension decorator
# All user extensions must use the @extension decorator for explicit naming

from src.extensions.base import Extension, extension
from typing import Dict, Any

@extension('test-extension')
class TestExtension(Extension):
    """
    Example extension using the @extension decorator.
    
    This extension will be registered as 'test-extension'.
    """
    
    def process(self, block_name: str, block_value: Any, context: Dict[str, Any]) -> Any:
        """Process a block with test extension logic."""
        if block_name == 'headers':
            # Add a test header
            if isinstance(block_value, dict):
                block_value['X-Test-Extension'] = 'loaded'
            else:
                block_value = {'X-Test-Extension': 'loaded'}
        
        return block_value
    
    def validate(self, block_name: str, block_value: Any) -> bool:
        """Validate test extension configuration."""
        return True

@extension('my-custom-extension')
class MyCustomExtension(Extension):
    """
    Example using kebab-case naming.
    
    This extension will be registered as 'my-custom-extension'.
    """
    
    def process(self, block_name: str, block_value: Any, context: Dict[str, Any]) -> Any:
        """Process a block with custom extension logic."""
        if block_name == 'headers':
            if isinstance(block_value, dict):
                block_value['X-Custom-Extension'] = 'enabled'
            else:
                block_value = {'X-Custom-Extension': 'enabled'}
        
        return block_value
    
    def validate(self, block_name: str, block_value: Any) -> bool:
        """Validate custom extension configuration."""
        return True

@extension('snake_case_extension')
class SnakeCaseExtension(Extension):
    """
    Example using snake_case naming.
    
    This extension will be registered as 'snake_case_extension'.
    """
    
    def process(self, block_name: str, block_value: Any, context: Dict[str, Any]) -> Any:
        """Process a block with snake case extension logic."""
        if block_name == 'headers':
            if isinstance(block_value, dict):
                block_value['X-Snake-Case'] = 'enabled'
            else:
                block_value = {'X-Snake-Case': 'enabled'}
        
        return block_value
    
    def validate(self, block_name: str, block_value: Any) -> bool:
        """Validate snake case extension configuration."""
        return True 