"""
Multiple extension for the Zysys API Test Framework.

This extension allows specifying multiple acceptable values using the | separator.
"""

from typing import Dict, Any
from .base import CoreExtension, core_extension

@core_extension('multiple')
class MultipleExtension(CoreExtension):
    """
    Built-in multiple values extension - allows OR logic with | separator.
    
    This extension processes pipe-separated values and converts them into
    a structured format that the validation system can handle.
    
    Usage:
        status<multiple>: 200 | 404 | 500
        content-type<multiple>: application/json | text/plain
    """
    
    def process(self, block_name: str, block_value: Any, context: Dict[str, Any]) -> Any:
        """
        Process multiple values separated by |.
        
        Args:
            block_name: The name of the block being processed
            block_value: The value to process (should be a string with | separators)
            context: Test context dictionary
        
        Returns:
            Dictionary with type and values, or original value if no processing needed
        """
        if isinstance(block_value, str) and '|' in block_value:
            values = [v.strip() for v in block_value.split('|')]
            
            # Convert values to appropriate types based on block name
            if block_name == 'status':
                # Convert status codes to integers
                converted_values = []
                for v in values:
                    try:
                        converted_values.append(int(v))
                    except ValueError:
                        converted_values.append(v)  # Keep as string if conversion fails
                return {"type": "multiple", "values": converted_values}
            else:
                # Keep other values as strings
                return {"type": "multiple", "values": values}
        return block_value
    
    def validate(self, block_name: str, block_value: Any) -> bool:
        """
        Validate multiple extension configuration.
        
        Args:
            block_name: The name of the block being validated
            block_value: The value to validate
        
        Returns:
            True if valid, False otherwise
        """
        if isinstance(block_value, str) and '|' in block_value:
            values = [v.strip() for v in block_value.split('|')]
            return len(values) > 1 and all(v for v in values)
        return True 