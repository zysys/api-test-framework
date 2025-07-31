# Extensions Specification

## Overview

The Zysys API Test Framework supports a powerful extension system that allows you to customize how test configurations are processed and validated. Extensions can modify any block in your test configurations using the `block<extension>` syntax.

## Extension Types

### Core Extensions

Built-in extensions that are bundled with the framework:

- **Multiple Extension**: Allows OR logic with `|` separator
- **Encoded Values Extension**: Base64 encodes values in key-value pairs
- **Dynamic Extension**: Generates dynamic values (planned)
- **Conditional Extension**: Conditional logic based on context (planned)

### User Extensions

Custom extensions created by users and placed in `test/extensions/` directory.

## Extension Naming

All user extensions must use the `@extension` decorator for explicit naming:

### @extension Decorator

Use the `@extension` decorator to register your extension:

```python
from src.extensions.base import Extension, extension

@extension('my-custom-extension')
class MyCustomExtension(Extension):
    def process(self, block_name, block_value, context):
        # Your extension logic
        return block_value
```

**Benefits:**

- ✅ Explicit naming: You choose the exact name
- ✅ Kebab-case support: `'test-extension'`
- ✅ Snake_case support: `'test_extension'`
- ✅ No dependency on class name
- ✅ Clear and consistent API

## Extension Interface

All extensions must implement the `Extension` abstract base class with two distinct methods:

### `process()` - Transformation Logic

```python
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
    # Transform the value - can return anything!
    return transformed_value
```

### `validate()` - Configuration Validation

```python
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
    # Check if the configuration is valid
    return is_valid
```

### Key Distinction

- **`process()`**: Can completely transform/replace values (transformative extensions)
- **`validate()`**: Determines if the configuration is valid (validation only)

### Example: How They Work Together

```python
class MyTransformativeExtension(Extension):
    def validate(self, block_name: str, block_value: Any) -> bool:
        # Check if we can process this configuration
        if block_name == 'body' and isinstance(block_value, dict):
            return True  # Valid configuration
        return False  # Invalid configuration

    def process(self, block_name: str, block_value: Any, context: Dict[str, Any]) -> Any:
        # Completely transform the value
        if block_name == 'body' and isinstance(block_value, dict):
            # Transform simple dict into complex structure
            return {
                "metadata": {"processed_by": "my_extension"},
                "data": block_value,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        return block_value
```

**Flow**:

1. **Validation**: `validate()` checks if the configuration is valid
2. **Transformation**: `process()` completely transforms the value
3. **Usage**: The transformed value is used in the test

## Extension Syntax

Extensions are applied using the `block<extension>` syntax:

```yaml
# Basic usage
name<myextension>: "Test Name"
relative-url<log>: /api/endpoint

# Field-level extensions
expected:
  status<multiple>: 200 | 404
  content-type<multiple>: application/json | text/plain

# Nested usage
headers<custom>:
  Authorization: "Bearer token"
  Content-Type: "application/json"
```

## Built-in Extensions

### Multiple Extension

The multiple extension allows you to specify multiple acceptable values using the `|` separator.

**Syntax**: `field<multiple>`

**Important**: The multiple extension is applied to individual fields, not entire blocks. Use `field<multiple>` syntax for the specific field you want to support multiple values.

**Usage Examples**:

```yaml
# Multiple status codes
expected:
  status<multiple>: 200 | 404 | 500

# Multiple content types
expected:
  content-type<multiple>: application/json | text/plain

# Multiple response values
expected:
  response:
    type: contains
    value<multiple>: "success" | "ok" | "valid"
```

**Processing**: The extension transforms the pipe-separated string into a structured dictionary:

```python
# Input: "200 | 404 | 500"
# Output: {"type": "multiple", "values": [200, 404, 500]}
```

**Validation**: The extension validates that the input contains multiple values separated by `|`:

```python
def validate(self, block_name: str, block_value: Any) -> bool:
    if isinstance(block_value, str) and '|' in block_value:
        values = [v.strip() for v in block_value.split('|')]
        return len(values) > 1 and all(v for v in values)
    return True
```

### Encoded Values Extension

The encoded values extension base64 encodes the values in key-value pairs while keeping the keys unchanged. This is useful for APIs that expect encoded values in form data or JSON payloads.

**Syntax**: `block<encoded_values>`

**Usage Examples**:

```yaml
# Encode body values for POST request
body<encoded_values>:
  username: "john_doe"
  password: "secret123"
  data: "sensitive information"
  user_id: 12345
  score: 95.5

# Results in:
body:
  username: "am9obl9kb2U="
  password: "c2VjcmV0MTIz"
  data: "c2Vuc2l0aXZlIGluZm9ybWF0aW9u"
  user_id: "MTIzNDU="
  score: "OTUuNQ=="
```

**Processing**: The extension transforms all values to base64 encoded strings while preserving the key names:

```python
# Input: {"username": "john_doe", "password": "secret123"}
# Output: {"username": "am9obl9kb2U=", "password": "c2VjcmV0MTIz"}
```

**Validation**: The extension validates that all values are encodable:

```python
def validate(self, block_name: str, block_value: Any) -> bool:
    if isinstance(block_value, dict):
        for key, value in block_value.items():
            if not isinstance(value, (str, int, float)):
                return False  # Only allow string, int, and float values
        return True
    return False
```

## Creating User Extensions

### Step 1: Create Extension File

Create a Python file in the `test/extensions/` directory:

```python
# test/extensions/my_extension.py
from runner import Extension
from typing import Dict, Any

class MyCustomExtension(Extension):
    """Custom extension that adds logging to test execution"""

    def process(self, block_name: str, block_value: Any, context: Dict[str, Any]) -> Any:
        """Process a block with custom logic"""
        if block_name == 'relative-url':
            print(f"🔍 Testing endpoint: {block_value}")
        elif block_name == 'type':
            print(f"📡 Using HTTP method: {block_value}")

        return block_value

    def validate(self, block_name: str, block_value: Any) -> bool:
        """Validate extension configuration"""
        return True
```

### Step 2: Use Extension in Test

```yaml
---
name: "Test with Custom Extension"
relative-url<mycustomextension>: /api/health
type<mycustomextension>: GET
expected:
  status<multiple>: 200 | 404
```

### Step 3: Auto-loading

Extensions are automatically loaded when the framework starts. You'll see confirmation messages:

```
✅ Loaded user extension: mycustomextension
```

## Extension Precedence

Extensions follow a precedence system controlled by the `extension-precedence` setting in `config.yaml`:

```yaml
# config.yaml
extension-precedence: "non-core" # non-core | core
```

### Precedence Rules

- **`non-core`** (default): User extensions take priority over core extensions
- **`core`**: Core extensions take priority over user extensions

This allows you to override built-in extensions with your own implementations.

## Extension Context

The `context` parameter provides access to the test configuration and other useful information:

```python
def process(self, block_name: str, block_value: Any, context: Dict[str, Any]) -> Any:
    test_config = context.get('test_config', {})

    # Access test properties
    test_name = test_config.get('name', 'Unknown')
    test_url = test_config.get('relative-url', '')

    # Your processing logic
    return block_value
```

## Common Extension Patterns

### 1. Header Modification

```python
class HeaderExtension(Extension):
    def process(self, block_name: str, block_value: Any, context: Dict[str, Any]) -> Any:
        if block_name == 'headers':
            if isinstance(block_value, dict):
                block_value['X-Custom-Header'] = 'value'
            else:
                block_value = {'X-Custom-Header': 'value'}
        return block_value
```

### 2. Dynamic Value Generation

```python
import uuid
from datetime import datetime

class DynamicExtension(Extension):
    def process(self, block_name: str, block_value: Any, context: Dict[str, Any]) -> Any:
        if isinstance(block_value, str):
            if block_value == '@uuid':
                return str(uuid.uuid4())
            elif block_value == '@timestamp':
                return datetime.now().isoformat()
        return block_value
```

### 3. Conditional Logic

```python
class ConditionalExtension(Extension):
    def process(self, block_name: str, block_value: Any, context: Dict[str, Any]) -> Any:
        test_config = context.get('test_config', {})

        if block_name == 'body':
            # Only add body for POST/PUT requests
            if test_config.get('type') in ['POST', 'PUT']:
                return block_value
            else:
                return None

        return block_value
```

## Error Handling

Extensions should handle errors gracefully:

```python
class SafeExtension(Extension):
    def process(self, block_name: str, block_value: Any, context: Dict[str, Any]) -> Any:
        try:
            # Your processing logic
            return processed_value
        except Exception as e:
            print(f"⚠️  Extension error: {e}")
            return block_value  # Return original value on error
```

## Best Practices

### 1. Keep Extensions Focused

Each extension should have a single responsibility:

```python
# Good: Single purpose
class LoggingExtension(Extension):
    def process(self, block_name: str, block_value: Any, context: Dict[str, Any]) -> Any:
        if block_name == 'relative-url':
            print(f"Testing: {block_value}")
        return block_value

# Avoid: Multiple responsibilities
class DoEverythingExtension(Extension):
    # Don't do this
    pass
```

### 2. Validate Input

Always validate your extension inputs:

```python
def validate(self, block_name: str, block_value: Any) -> bool:
    if block_name == 'headers':
        if isinstance(block_value, dict):
            return all(isinstance(k, str) and isinstance(v, str)
                      for k, v in block_value.items())
        return False
    return True
```

### 3. Use Descriptive Names

Choose clear, descriptive names for your extensions:

```python
# Good
class AuthenticationExtension(Extension):
    pass

class RateLimitExtension(Extension):
    pass

# Avoid
class Ext1(Extension):
    pass
```

### 4. Document Your Extensions

Include clear documentation:

```python
class MyExtension(Extension):
    """
    Custom extension that adds authentication headers.

    Usage:
        headers<myextension>:
          Authorization: "Bearer token"

    This extension automatically adds required authentication
    headers to all requests.
    """
```

## Debugging Extensions

### Enable Debug Logging

Set the log level to DEBUG in your test configuration:

```yaml
# config.yaml
log-level: "DEBUG"
```

### Check Extension Loading

Extensions are loaded when the framework starts. Look for these messages:

```
✅ Loaded user extension: myextension
❌ Failed to load extension bad_extension.py: ImportError
```

### Test Extensions

Create simple test cases to verify your extensions work correctly:

```yaml
---
name: "Extension Test"
relative-url<myextension>: /test
type: GET
expected:
  status: 200
```

## Extension Examples

### Complete Example: Authentication Extension

```python
# test/extensions/auth_extension.py
from runner import Extension
from typing import Dict, Any

class AuthExtension(Extension):
    """Adds authentication headers to requests"""

    def process(self, block_name: str, block_value: Any, context: Dict[str, Any]) -> Any:
        if block_name == 'headers':
            if isinstance(block_value, dict):
                block_value['Authorization'] = 'Bearer your-token-here'
                block_value['X-API-Key'] = 'your-api-key'
            else:
                block_value = {
                    'Authorization': 'Bearer your-token-here',
                    'X-API-Key': 'your-api-key'
                }
        return block_value

    def validate(self, block_name: str, block_value: Any) -> bool:
        if block_name == 'headers':
            return isinstance(block_value, dict)
        return True
```

**Usage**:

```yaml
---
name: "Authenticated API Test"
relative-url: /api/protected
type: GET
headers<auth>: {}
expected:
  status: 200
```

This extension automatically adds authentication headers to any test that uses `headers<auth>`.

## Troubleshooting

### Extension Not Found

- Check that the extension file is in `test/extensions/`
- Verify the class name matches the extension name (case-insensitive)
- Ensure the class inherits from `Extension`

### Extension Not Processing

- Verify you're using the correct syntax: `block<extension>`
- Check that the extension is being loaded (look for confirmation messages)
- Test with a simple case first

### Import Errors

- Make sure your extension file has no syntax errors
- Check that all imports are available
- Verify the file is valid Python

## Future Extensions

Planned built-in extensions:

- **Dynamic Extension**: `@uuid`, `@timestamp`, `@email`
- **Conditional Extension**: Conditional logic based on test context
- **Template Extension**: Variable substitution in URLs and bodies
- **Schema Extension**: JSON schema validation
- **Rate Limit Extension**: Automatic rate limiting and retry logic

## Contributing Extensions

When creating extensions for sharing:

1. Include comprehensive documentation
2. Provide usage examples
3. Handle errors gracefully
4. Follow the naming conventions
5. Include validation logic
6. Test thoroughly

---

For more information, see the main README.md and USAGE.md files.
