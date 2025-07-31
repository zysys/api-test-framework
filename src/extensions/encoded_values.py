"""
Encoded Values extension for the Zysys API Test Framework.

This extension base64 encodes the values in key-value pairs for POST requests.
Useful for APIs that expect encoded values in form data or JSON payloads.
"""

import base64
from typing import Dict, Any
from .base import CoreExtension, core_extension

@core_extension('encoded_values')
class EncodedValuesExtension(CoreExtension):
    """
    Built-in extension that base64 encodes values in key-value pairs.
    
    This extension processes body data and encodes the values while keeping
    the keys unchanged. Useful for APIs that expect encoded values.
    
    Usage:
        body<encoded_values>:
          username: "john_doe"
          password: "secret123"
          data: "sensitive information"
    
    Results in:
        body:
          username: "am9obl9kb2U="
          password: "c2VjcmV0MTIz"
          data: "c2Vuc2l0aXZlIGluZm9ybWF0aW9u"
    """
    
    def process(self, block_name: str, block_value: Any, context: Dict[str, Any]) -> Any:
        """
        Process key-value pairs and encode the values.
        
        Args:
            block_name: The name of the block being processed (e.g., 'body')
            block_value: The value to process (should be a dict with key-value pairs)
            context: Test context dictionary
        
        Returns:
            Dictionary with encoded values, or original value if no processing needed
        """
        if isinstance(block_value, dict):
            encoded_dict = {}
            for key, value in block_value.items():
                if isinstance(value, str):
                    # Encode string values
                    encoded_value = base64.b64encode(value.encode('utf-8')).decode('utf-8')
                    encoded_dict[key] = encoded_value
                elif isinstance(value, (int, float)):
                    # Encode numeric values as strings
                    value_str = str(value)
                    encoded_value = base64.b64encode(value_str.encode('utf-8')).decode('utf-8')
                    encoded_dict[key] = encoded_value
                else:
                    # Keep non-string/non-numeric values as-is
                    encoded_dict[key] = value
            return encoded_dict
        return block_value
    
    def validate(self, block_name: str, block_value: Any) -> bool:
        """
        Validate encoded values extension configuration.
        
        Args:
            block_name: The name of the block being validated
            block_value: The value to validate
        
        Returns:
            True if valid, False otherwise
        """
        if isinstance(block_value, dict):
            # Check that all values are encodable
            for key, value in block_value.items():
                if not isinstance(value, (str, int, float)):
                    # Only allow string, int, and float values for encoding
                    return False
            return True
        return False 