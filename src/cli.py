"""
Zysys API Test Framework - CLI Interface

Provides the command-line interface for the testing framework.
"""

import asyncio
import logging
import psutil
import shutil
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

from .core import EndpointTester, TestResult

# Initialize rich console
console = Console()

# Constants
DEFAULT_CONFIG_FILE = "config.yaml"
DEFAULT_CONFIGS_DIR = "test/configs"
EXAMPLE_CONFIG_FILE = "config.example.yaml"
EXAMPLE_CONFIGS_DIR = "examples"

class ZysysTestCLI:
    """
    Main CLI application for the Zysys API Test Framework.
    
    Provides a command-line interface for initializing the framework,
    creating tests, running tests, and displaying results with rich
    terminal output.
    
    Attributes:
        config_file: Path to the global configuration file
        configs_dir: Directory containing test configuration files
    """
    
    def __init__(self) -> None:
        """Initialize the CLI application with default configuration paths."""
        self.config_file = DEFAULT_CONFIG_FILE
        self.configs_dir = DEFAULT_CONFIGS_DIR
        
    def setup_logging(self, level: str = "INFO") -> None:
        """
        Setup logging configuration.
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR).
                  Defaults to "INFO".
        """
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def get_cpu_count(self) -> int:
        """
        Get the number of CPU cores for automatic parallelization.
        
        Returns:
            Number of physical CPU cores, or 1 if detection fails.
        """
        return max(psutil.cpu_count(logical=False) or 1, 1)
    
    def ensure_config_exists(self) -> None:
        """
        Ensure configuration files exist, create from examples if needed.
        
        Creates the test directory structure and copies example configuration
        files if they don't exist. Exits with error if required files are missing.
        
        Raises:
            SystemExit: If config.yaml is not found and no example is available.
        """
        if not Path(self.config_file).exists():
            if Path(EXAMPLE_CONFIG_FILE).exists():
                shutil.copy(EXAMPLE_CONFIG_FILE, self.config_file)
                console.print(f"✅ Created {self.config_file} from example", style="green")
            else:
                console.print(f"❌ {self.config_file} not found and no example available", style="red")
                sys.exit(1)
        
        # Ensure test directory structure exists
        Path("test").mkdir(exist_ok=True)
        Path("test/extensions").mkdir(exist_ok=True)
        Path(self.configs_dir).mkdir(exist_ok=True)
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load the global configuration.
        
        Automatically detects CPU cores and sets concurrency if not specified.
        
        Returns:
            Dictionary containing global configuration settings.
            
        Raises:
            SystemExit: If configuration file cannot be loaded.
        """
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Auto-detect CPU cores if concurrent is set to 0
            if config.get('concurrent', 0) == 0:
                config['concurrent'] = self.get_cpu_count()
                console.print(f"🖥️  Auto-detected {config['concurrent']} CPU cores", style="blue")
            
            return config
        except Exception as e:
            console.print(f"❌ Error loading config: {e}", style="red")
            sys.exit(1)
    
    def list_tests(self) -> None:
        """
        List all available test files and their test cases.
        
        Displays a rich table showing test files, test names, URLs, and HTTP methods.
        Handles multiple YAML documents per file and provides error handling.
        """
        configs_path = Path(self.configs_dir)
        if not configs_path.exists():
            console.print(f"❌ No test configurations found in {self.configs_dir}", style="red")
            return
        
        table = Table(title="Available Tests")
        table.add_column("File", style="cyan")
        table.add_column("Test Name", style="green")
        table.add_column("URL", style="yellow")
        table.add_column("Method", style="magenta")
        
        for yaml_file in configs_path.glob("*.yaml"):
            try:
                with open(yaml_file, 'r') as f:
                    documents = list(yaml.safe_load_all(f))
                    for i, doc in enumerate(documents):
                        if isinstance(doc, dict):
                            name = str(doc.get('name', f"{yaml_file.name}#{i+1}"))
                            url = str(doc.get('relative-url', doc.get('url', 'N/A')))
                            method = str(doc.get('type', 'GET'))
                            table.add_row(yaml_file.name, name, url, method)
            except Exception as e:
                console.print(f"⚠️  Error reading {yaml_file}: {e}", style="yellow")
        
        console.print(table)
    
    def create_test(self, name: str, url: str, method: str = "GET") -> None:
        """
        Create a new test configuration.
        
        Generates a YAML test file with default expectations that can be
        customized by the user.
        
        Args:
            name: Name of the test (used for filename and test identification)
            url: Relative URL path to test
            method: HTTP method (GET, POST, etc.). Defaults to "GET".
        """
        test_config = {
            'name': name,
            'relative-url': url,
            'type': method.upper(),
            'expected': {
                'status': 200,
                'content-type': 'application/json',
                'response': {
                    'type': 'contains',
                    'value': 'success'
                }
            }
        }
        
        # Create configs directory if it doesn't exist
        Path(self.configs_dir).mkdir(exist_ok=True)
        
        # Write test to file
        test_file = Path(self.configs_dir) / f"{name.lower().replace(' ', '_')}.yaml"
        with open(test_file, 'w') as f:
            yaml.dump(test_config, f, default_flow_style=False, sort_keys=False)
        
        console.print(f"✅ Created test: {test_file}", style="green")
        console.print(f"📝 Edit {test_file} to customize expectations", style="blue")
    
    async def run_specific_test(self, test_name: str) -> bool:
        """
        Run a specific test by name.
        
        Searches through all loaded tests to find one matching the given name
        and executes it.
        
        Args:
            test_name: Name of the test to run
            
        Returns:
            True if the test passed, False otherwise.
        """
        config = self.load_config()
        tester = EndpointTester(self.configs_dir)
        
        # Find the specific test
        target_test = None
        for test in tester.tests:
            if test.get('name') == test_name:
                target_test = test
                break
        
        if not target_test:
            console.print(f"❌ Test '{test_name}' not found", style="red")
            return False
        
        console.print(f"🧪 Running test: {test_name}", style="blue")
        
        async with tester.create_session() as session:
            result = await tester.run_test(session, target_test)
            self.display_result(result)
            return result.passed
    
    async def run_test_file(self, file_path: str) -> bool:
        """
        Run all tests in a specific file.
        
        Loads tests from the specified file and executes them with progress
        indication.
        
        Args:
            file_path: Path to the test file to run
            
        Returns:
            True if all tests passed, False if any failed.
        """
        if not Path(file_path).exists():
            console.print(f"❌ Test file '{file_path}' not found", style="red")
            return False
        
        config = self.load_config()
        tester = EndpointTester(self.configs_dir)
        
        # Filter tests to only those from the specified file
        file_tests = [test for test in tester.tests if test.get('_source_file', '').startswith(Path(file_path).name)]
        
        if not file_tests:
            console.print(f"❌ No tests found in '{file_path}'", style="red")
            return False
        
        console.print(f"🧪 Running {len(file_tests)} tests from {file_path}", style="blue")
        
        async with tester.create_session() as session:
            results = []
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Running tests...", total=len(file_tests))
                
                for test in file_tests:
                    result = await tester.run_test(session, test)
                    results.append(result)
                    progress.advance(task)
            
            # Display results
            self.display_results(results)
            return all(r.passed for r in results)
    
    async def run_all_tests(self) -> bool:
        """
        Run all available tests.
        
        Executes all loaded tests using the core testing engine and displays
        configuration information.
        
        Returns:
            True if all tests passed, False if any failed.
        """
        config = self.load_config()
        tester = EndpointTester(self.configs_dir)
        
        console.print(f"🧪 Running {len(tester.tests)} tests", style="blue")
        console.print(f"🌐 Base URL: {config['baseUrl']}", style="blue")
        console.print(f"⚡ Concurrent: {config['concurrent']}", style="blue")
        console.print()
        
        success = await tester.run_tests()
        return success
    
    def display_result(self, result: TestResult) -> None:
        """
        Display a single test result.
        
        Shows the test outcome with appropriate styling and error details
        if the test failed.
        
        Args:
            result: TestResult object containing the test outcome
        """
        if result.passed:
            console.print(f"✅ {result.name} ({result.duration:.2f}s)", style="green")
        else:
            console.print(f"❌ {result.name} ({result.duration:.2f}s)", style="red")
            console.print(f"   URL: {result.url}", style="yellow")
            if result.error:
                console.print(f"   Error: {result.error}", style="red")
    
    def display_results(self, results: List[TestResult]) -> None:
        """
        Display multiple test results in a table format.
        
        Creates a rich table showing test names, status, duration, and URLs
        with color-coded status indicators.
        
        Args:
            results: List of TestResult objects to display
        """
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        
        table = Table(title="Test Results")
        table.add_column("Test", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Duration", style="yellow")
        table.add_column("URL", style="blue")
        
        for result in results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            status_style = "green" if result.passed else "red"
            table.add_row(
                result.name,
                Text(status, style=status_style),
                f"{result.duration:.2f}s",
                result.url
            )
        
        console.print(table)
        console.print(f"📊 Results: {passed} passed, {failed} failed", style="blue")
    
    def show_extensions(self) -> None:
        """
        Display available extensions.
        
        Shows all core and user extensions with their current precedence.
        """
        try:
            # Create an ExtensionLoader directly to avoid config file dependency
            # This works in both modular and standalone modes
            try:
                from extensions import ExtensionLoader
            except ImportError:
                # In standalone mode, ExtensionLoader is in the same file
                import runner
                ExtensionLoader = runner.ExtensionLoader
            
            loader = ExtensionLoader()
            
            # Load user extensions
            loader.load_user_extensions()
            
            # Get available extensions
            available = loader.list_available_extensions()
            
            console.print("🔧 Available Extensions", style="bold blue")
            console.print()
            
            # Core extensions
            if available['core']:
                console.print("📦 Core Extensions:", style="bold green")
                for ext in available['core']:
                    console.print(f"  • {ext}", style="green")
                console.print()
            
            # User extensions
            if available['user']:
                console.print("👤 User Extensions:", style="bold yellow")
                for ext in available['user']:
                    console.print(f"  • {ext}", style="yellow")
                console.print()
            
            # Precedence
            console.print(f"⚖️  Extension Precedence: {available['precedence']}", style="blue")
            console.print()
            
            if not available['core'] and not available['user']:
                console.print("ℹ️  No extensions found", style="yellow")
                
        except Exception as e:
            console.print(f"❌ Extension system not available: {e}", style="red")

def show_help() -> None:
    """
    Show help information.
    
    Displays the framework name, usage instructions, available commands,
    and example usage patterns.
    """
    console.print("Zysys API Test Framework", style="bold blue")
    console.print()
    console.print("Usage: python3 runner.py <command> [args...]", style="green")
    console.print()
    console.print("Commands:", style="bold")
    console.print("  init                    Initialize the test framework")
    console.print("  list                    List all available tests")
    console.print("  create <name> <url>     Create a new test")
    console.print("  run <test_name>         Run a specific test")
    console.print("  run-file <file_path>    Run all tests in a file")
    console.print("  run-all                 Run all available tests")
    console.print("  extensions              Show available extensions")
    console.print("  info                    Show framework information")
    console.print("  version                 Show framework version")
    console.print("  help                    Show this help message")
    console.print()
    console.print("Examples:", style="bold")
    console.print("  python3 runner.py init")
    console.print("  python3 runner.py create 'Health Check' /health")
    console.print("  python3 runner.py run-all")
    console.print("  python3 runner.py run 'Health Check - Basic GET'")

def main() -> None:
    """
    Main CLI function.
    
    Parses command line arguments and delegates to appropriate CLI methods.
    Handles argument validation and provides help when needed.
    """
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1]
    
    cli = ZysysTestCLI()
    cli.setup_logging()
    cli.ensure_config_exists()
    
    if command == "init":
        # Create config from example if it doesn't exist
        if not Path(cli.config_file).exists() and Path(EXAMPLE_CONFIG_FILE).exists():
            shutil.copy(EXAMPLE_CONFIG_FILE, cli.config_file)
            console.print(f"✅ Created {cli.config_file} from example", style="green")
        
        # Create test directory structure
        Path("test").mkdir(exist_ok=True)
        Path("test/extensions").mkdir(exist_ok=True)
        Path(cli.configs_dir).mkdir(exist_ok=True)
        
        # Copy example tests if they don't exist
        if Path(EXAMPLE_CONFIGS_DIR).exists():
            for example_file in Path(EXAMPLE_CONFIGS_DIR).glob("*.yaml"):
                target_file = Path(cli.configs_dir) / example_file.name
                if not target_file.exists():
                    shutil.copy(example_file, target_file)
                    console.print(f"✅ Created example test: {target_file}", style="green")
        
        console.print("🎉 Test framework initialized!", style="green")
        console.print("📁 Created test/ directory structure", style="blue")
        console.print("📝 Edit config.yaml to set your base URL and preferences", style="blue")
    
    elif command == "list":
        cli.list_tests()
    
    elif command == "create":
        if len(sys.argv) < 4:
            console.print("❌ Usage: create <name> <url> [method]", style="red")
            return
        name = sys.argv[2]
        url = sys.argv[3]
        method = sys.argv[4] if len(sys.argv) > 4 else "GET"
        cli.create_test(name, url, method)
    
    elif command == "run":
        if len(sys.argv) < 3:
            console.print("❌ Usage: run <test_name>", style="red")
            return
        test_name = sys.argv[2]
        success = asyncio.run(cli.run_specific_test(test_name))
        sys.exit(0 if success else 1)
    
    elif command == "run-file":
        if len(sys.argv) < 3:
            console.print("❌ Usage: run-file <file_path>", style="red")
            return
        file_path = sys.argv[2]
        success = asyncio.run(cli.run_test_file(file_path))
        sys.exit(0 if success else 1)
    
    elif command == "run-all":
        success = asyncio.run(cli.run_all_tests())
        sys.exit(0 if success else 1)
    
    elif command == "extensions":
        cli.show_extensions()
    
    elif command == "info":
        try:
            config = cli.load_config()
            
            info_table = Table(title="Framework Information")
            info_table.add_column("Property", style="cyan")
            info_table.add_column("Value", style="green")
            
            info_table.add_row("Base URL", config.get('baseUrl', 'Not set'))
            info_table.add_row("Concurrent Requests", str(config.get('concurrent', 'Auto')))
            info_table.add_row("Timeout", f"{config.get('timeout', 30)}s")
            info_table.add_row("Retries", str(config.get('retries', 3)))
            info_table.add_row("CPU Cores", str(cli.get_cpu_count()))
            info_table.add_row("Config File", cli.config_file)
            info_table.add_row("Tests Directory", cli.configs_dir)
            
            console.print(info_table)
            
        except Exception as e:
            console.print(f"❌ Error loading configuration: {e}", style="red")
    
    elif command == "version":
        console.print("🚀 Zysys API Test Framework 2.0.0", style="bold blue")
        console.print("📝 Using Semantic Versioning (major.minor.patch)", style="blue")
        console.print("📋 Check header for detailed version info", style="blue")
    
    elif command == "help":
        show_help()
    
    else:
        console.print(f"❌ Unknown command: {command}", style="red")
        show_help()
        sys.exit(1) 