# Examples

This directory contains examples and demonstrations for the Zysys API Test Framework.

## Directory Structure

```
examples/
├── README.md                    # This file
├── example.yaml                 # Comprehensive test scenarios
├── extension_example.yaml       # Extension system examples
├── configs/                     # Extension-specific examples
│   ├── multiple_extension_demo.yaml      # Multiple extension usage
│   ├── encoded_values_demo.yaml          # Encoded values extension
│   └── extension_demo.yaml               # Custom extension usage
└── extensions/                  # Custom extension examples
    └── extension_example.py              # How to create extensions
```

## Getting Started

### Basic Examples

- **`example.yaml`** - Comprehensive test scenarios covering all validation types
- **`extension_example.yaml`** - Examples of using the built-in extension system

### Extension Examples

- **`configs/multiple_extension_demo.yaml`** - Using the `<multiple>` extension for flexible validation
- **`configs/encoded_values_demo.yaml`** - Using the `<encoded_values>` extension for secure data handling
- **`configs/extension_demo.yaml`** - Using custom extensions with @extension decorator

### Custom Extension Development

- **`extensions/extension_example.py`** - Complete example using the `@extension` decorator

## Usage

To run these examples:

```bash
# Run comprehensive examples
python3 -m src.cli run-file examples/example.yaml

# Run extension examples
python3 -m src.cli run-file examples/extension_example.yaml

# Run specific extension demos
python3 -m src.cli run-file examples/configs/multiple_extension_demo.yaml
```

## Creating Your Own Extensions

See `extensions/extension_example.py` for a complete guide on creating custom extensions.

### Creating Extensions

All user extensions must use the `@extension` decorator to specify the exact name:

```python
from src.extensions.base import Extension, extension

@extension('my-custom-extension')
class MyCustomExtension(Extension):
    def process(self, block_name, block_value, context):
        # Your extension logic here
        return block_value

    def validate(self, block_name, block_value):
        return True
```

**Benefits:**

- ✅ Explicit naming: You choose the exact name
- ✅ Kebab-case support: `'test-extension'`
- ✅ Snake_case support: `'snake_case_extension'`
- ✅ No dependency on class name
- ✅ Clear and consistent API
