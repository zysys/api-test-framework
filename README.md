# Zysys API Test Framework

A powerful, parallel HTTP endpoint testing framework with automatic core detection, rich CLI interface, and flexible configuration management. Perfect for validating Docker containers, microservices, and API endpoints.

## 🚀 Features

- **Parallel Testing**: Automatic CPU core detection for optimal performance
- **Rich CLI**: Beautiful terminal interface with progress bars and colored output
- **Flexible Configuration**: YAML-based test definitions with multiple validation types
- **Multiple Usage Modes**: Library, CLI tool, or Git submodule
- **Comprehensive Validation**: Status codes, content types, CORS headers, and response body validation
- **Retry Logic**: Configurable retry attempts for failed requests
- **Multiple Output Formats**: Text, JSON, and JUnit XML support

## 📦 Installation

### As a Standalone Tool

```bash
git clone <repository-url>
cd zysys-api-test-framework
pip install -r requirements.txt
```

### As a Git Submodule

```bash
git submodule add <repository-url> tests/api-framework
cd tests/api-framework
pip install -r requirements.txt
```

### As a Library

```bash
pip install git+<repository-url>
```

## 🎯 Quick Start

### Option 1: Download Latest Standalone Runner

```bash
# Download the latest standalone runner from releases
curl -L https://github.com/zysys/api-test-framework/releases/latest/download/runner.py -o runner.py

```

### Option 2: Clone and Install

```bash
git clone <repository-url>
cd zysys-api-test-framework
pip install -r requirements.txt
```

2. **Initialize the framework:**

   ```bash
   python3 runner.py init
   ```

3. **Configure your base URL:**

   ```bash
   # Edit config.yaml
   baseUrl: "http://localhost:8080"
   ```

4. **Create your first test:**

   ```bash
   python3 runner.py create "Health Check" /health
   ```

5. **Run all tests:**
   ```bash
   python3 runner.py run-all
   ```

## 🏗️ Simple Project Structure

For quick integration into existing projects, you can use the simple `test/` directory structure:

### Directory Layout

```
my-project/
├── runner.py              # Download from framework
└── test/
    ├── extensions/        # Custom extensions
    └── configs/          # Test configurations
        ├── auth.yaml
        ├── users.yaml
        └── legacy.yaml
```

### Framework Structure

The framework itself is organized in a modular structure:

```
zysys-api-test-framework/
├── src/
│   ├── core.py           # Core testing engine
│   ├── cli.py            # CLI interface
│   └── extensions/       # Extension system
│       ├── __init__.py   # Extension module exports
│       ├── base.py       # Base classes and decorators
│       ├── loader.py     # Extension loader
│       └── multiple.py   # Multiple extension
├── runner.py             # Auto-generated standalone runner
├── examples/             # Example test configurations
└── test/                 # User test directory (created by init)
```

### Quick Setup

1. **Download the runner:**

   ```bash
   curl -O https://raw.githubusercontent.com/zysys/api-test-framework/main/runner.py
   ```

2. **Initialize the structure:**

   ```bash
   python3 runner.py init
   ```

3. **Start testing:**
   ```bash
   python3 runner.py create "Health Check" /health
   python3 runner.py run-all
   ```

### Benefits

- **Single Command Center**: Everything goes through `runner.py`
- **Simple Structure**: Just 3 directories (runner, extensions, configs)
- **Portable**: Easy to copy between projects
- **Self-Contained**: Everything in one place
- **Extensible**: Can add custom functionality via extensions

This pattern is perfect for scenarios like:

- Converting legacy endpoints to Docker
- Adding API testing to existing projects
- Quick validation of microservices
- CI/CD pipeline integration

## 🛠️ CLI Commands

### Core Commands

```bash
# Initialize framework with examples
python3 runner.py init

# List all available tests
python3 runner.py list

# Create a new test
python3 runner.py create "Test Name" /endpoint

# Run specific test by name
python3 runner.py run "Test Name"

# Run all tests in a file
python3 runner.py run-file test/configs/my_tests.yaml

# Run all tests
python3 runner.py run-all

# Show framework information
python3 runner.py info
```

### Advanced Options

```bash
# The simple CLI doesn't support advanced options yet
# For advanced configuration, edit config.yaml directly
# or use the original zysys_test.py (if Click issues are resolved)
```

## 📝 Configuration

### Global Config (`config.yaml`)

```yaml
# Base URL for all relative endpoints
baseUrl: "http://localhost:8080"

# Number of retry attempts for failed requests
retries: 3

# Whether to trim whitespace from responses
trim: true

# Stop execution on first failure
stop-on-fail: false

# Request timeout in seconds
timeout: 30

# Maximum concurrent requests (0 = auto-detect CPU cores)
concurrent: 0

# Logging level (DEBUG, INFO, WARNING, ERROR)
log-level: "INFO"

# Output format (text, json, junit)
output-format: "text"

# Save test results to file
save-results: true
results-file: "test-results.json"
```

### Test Configuration Structure

Each YAML file in `configs/` can contain multiple test definitions separated by `---`:

```yaml
---
name: "Health Check"
relative-url: /health
type: GET
expected:
  status: 200
  content-type: application/json
  response:
    type: contains
    value: "status"

---
name: "User Login"
relative-url: /api/auth/login
type: POST
body:
  username: "testuser"
  password: "testpass"
expected:
  status: 200
  content-type: application/json
  response:
    type: regex
    value: '"token":"[a-zA-Z0-9]+"'
```

## 🔍 Response Validation Types

- **`exact`**: Response must match exactly
- **`regex`**: Response must match regex pattern
- **`contains`**: Response must contain substring
- **`empty`**: Response must be empty

## 🏗️ Usage Patterns

### 1. Library Usage

```python
from test_runner import EndpointTester
import asyncio

async def run_tests():
    tester = EndpointTester("configs")
    success = await tester.run_tests()
    return success

# Run tests
asyncio.run(run_tests())
```

### 2. Git Submodule Pattern

```bash
# In your main project
git submodule add <framework-url> tests/api-framework

# Create a wrapper script
echo '#!/bin/bash
cd tests/api-framework
python zysys_test.py "$@"' > run-tests.sh
chmod +x run-tests.sh

# Use in CI/CD
./run-tests.sh run-all
```

### 3. Docker Integration

```dockerfile
# In your Dockerfile
COPY tests/api-framework /opt/test-framework
WORKDIR /opt/test-framework
RUN pip install -r requirements.txt

# In your CI pipeline
docker run --network host your-app &
sleep 10
docker run --network host test-framework python zysys_test.py run-all
```

## 📊 Example Test Cases

The framework includes comprehensive examples in the `examples/` directory:

- `examples/example.yaml` - Comprehensive test scenarios
- `examples/extension_example.yaml` - Extension system examples
- `examples/configs/` - Extension-specific demonstrations
- `examples/extensions/` - Custom extension examples

These examples demonstrate:

- Health check endpoints
- Authentication flows
- Data validation
- Error handling
- CORS validation
- File uploads
- Rate limiting
- Protected endpoints

## 🔧 Advanced Features

### Extension System

The framework includes a powerful extension system for customizing test behavior:

```python
from src.extensions.base import Extension, extension

@extension('my-custom-extension')
class MyCustomExtension(Extension):
    def process(self, block_name, block_value, context):
        # Your custom logic here
        return block_value
```

**Built-in Extensions:**

- `multiple` - Accept multiple valid values: `status<multiple>: 200 | 404`
- `encoded_values` - Automatically encode sensitive data

**Extension Naming:**

- Use `@extension('name')` decorator for explicit naming
- Supports kebab-case: `'test-extension'`
- Supports snake_case: `'test_extension'`
- Clear and consistent API

### Automatic Core Detection

The framework automatically detects your CPU cores and sets optimal concurrency:

```yaml
# config.yaml
concurrent: 0 # Auto-detect (recommended)
```

### Custom Headers

```yaml
---
name: "Authenticated Request"
relative-url: /api/protected
type: GET
headers:
  Authorization: "Bearer your-token"
expected:
  status: 200
```

### File Uploads

```yaml
---
name: "File Upload"
relative-url: /api/upload
type: POST
body:
  file: "@test-file.txt"
  description: "Test upload"
expected:
  status: 201
```

## 🚀 Performance Tips

1. **Use auto-detection**: Set `concurrent: 0` for optimal performance
2. **Batch related tests**: Group related endpoints in the same file
3. **Use appropriate timeouts**: Set realistic timeouts for your endpoints
4. **Enable retries**: Use retries for flaky endpoints

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 🚨 Breaking Changes in v1.0.0

This is the first official release of the Zysys API Test Framework. The extension system has been simplified:

- **Required**: All user extensions must use the `@extension('name')` decorator
- **Removed**: Legacy class-name-based extension registration
- **Simplified**: Cleaner, more consistent API

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔄 Continuous Integration

The framework includes GitHub Actions that automatically generate the latest standalone runner:

### Automatic Runner Generation

- **On every push to main**: The latest `runner.py` is automatically generated
- **Available as**: GitHub release asset 
- **Always up-to-date**: Contains the latest features and bug fixes

### GitHub Actions

- `.github/workflows/release-runner.yml` - Creates GitHub releases with `runner.py` as asset

## 🆘 Support

- Check the examples in the `examples/` directory
- Run `python3 runner.py --help` for configuration help
- Use `--log-level DEBUG` for detailed debugging information
