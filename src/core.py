"""
Zysys API Test Framework - Core Testing Engine

Provides the core testing functionality for parallel HTTP endpoint validation
with comprehensive response checking and error handling.
"""

import asyncio
import aiohttp
import yaml
import re
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

# Import extension system
try:
    from .extensions import ExtensionLoader
except ImportError:
    # Fallback for direct execution
    from extensions import ExtensionLoader

@dataclass
class TestResult:
    """
    Represents the result of a single endpoint test.
    
    Attributes:
        name: The name/identifier of the test
        url: The full URL that was tested
        passed: Whether the test passed validation
        expected: The expected response criteria
        actual: The actual response received
        error: Error message if the test failed due to an exception
        duration: Time taken to complete the test in seconds
    """
    name: str
    url: str
    passed: bool
    expected: Dict[str, Any]
    actual: Dict[str, Any]
    error: Optional[str] = None
    duration: float = 0.0

class EndpointTester:
    """
    Core testing engine for parallel HTTP endpoint validation.
    
    This class handles loading test configurations, executing HTTP requests,
    and validating responses against expected criteria. It supports parallel
    execution with configurable concurrency limits.
    
    Attributes:
        config_dir: Directory containing test configuration files
        global_config: Global configuration settings
        tests: List of loaded test definitions
    """
    
    def __init__(self, config_dir: str = "configs") -> None:
        """
        Initialize the endpoint tester.
        
        Args:
            config_dir: Path to directory containing test configuration files.
                       Defaults to "configs".
        
        Raises:
            FileNotFoundError: If config.yaml is not found in the current directory.
        """
        self.config_dir = Path(config_dir)
        self.global_config = self.load_global_config()
        
        # Initialize extension system
        self.extension_loader = ExtensionLoader()
        self.extension_loader.precedence = self.global_config.get('extension-precedence', 'non-core')
        self.extension_loader.load_user_extensions()
        
        self.tests = self.load_all_tests()
        
    def load_global_config(self) -> Dict[str, Any]:
        """
        Load the global configuration from config.yaml.
        
        Returns:
            Dictionary containing global configuration settings.
            
        Raises:
            FileNotFoundError: If config.yaml does not exist.
        """
        config_file = Path("config.yaml")
        if not config_file.exists():
            raise FileNotFoundError("config.yaml not found. Run 'python zysys_test.py init' to initialize.")
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def load_all_tests(self) -> List[Dict[str, Any]]:
        """
        Load all test configurations from YAML files in the config directory.
        
        Supports multiple YAML documents per file, separated by '---'.
        Each document should represent a single test definition.
        
        Returns:
            List of test configuration dictionaries.
        """
        tests = []
        configs_dir = self.config_dir
        
        if not configs_dir.exists():
            logging.warning(f"Test directory {configs_dir} does not exist")
            return tests
        
        for yaml_file in configs_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r') as f:
                    # Load multiple YAML documents from single file
                    documents = list(yaml.safe_load_all(f))
                    for i, doc in enumerate(documents):
                        if isinstance(doc, dict):  # Ensure it's a valid test document
                            doc['_source_file'] = f"{yaml_file.name}#{i+1}"
                            # Process extensions for this test
                            processed_doc = self.process_test_with_extensions(doc)
                            tests.append(processed_doc)
            except Exception as e:
                logging.error(f"Error loading test file {yaml_file}: {e}")
        
        return tests
    
    def process_test_with_extensions(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a test configuration with extensions.
        
        Recursively processes all blocks that have extension syntax.
        
        Args:
            test_config: Original test configuration dictionary
        
        Returns:
            Processed test configuration with extensions applied
        """
        processed = {}
        context = {'test_config': test_config}
        
        for key, value in test_config.items():
            if key.startswith('_'):  # Skip internal fields
                processed[key] = value
                continue
                
            if isinstance(value, dict):
                # Recursively process nested dictionaries
                processed[key] = self.process_test_with_extensions(value)
            elif isinstance(value, list):
                # Process list items
                processed[key] = [self.process_test_with_extensions(item) if isinstance(item, dict) else item for item in value]
            else:
                # Process leaf values with extensions
                processed_value = self.extension_loader.process_block_with_extensions(key, value, context)
                
                # Check if this was an extension and extract the base key name
                if isinstance(key, str) and '<' in key and key.endswith('>'):
                    base_name = key.rsplit('<', 1)[0]
                    processed[base_name] = processed_value
                else:
                    processed[key] = processed_value
        
        return processed
    
    async def run_tests(self) -> bool:
        """
        Execute all loaded tests in parallel with configurable concurrency.
        
        Creates a semaphore to limit concurrent requests based on the
        'concurrent' setting in global configuration. Processes results
        and logs outcomes.
        
        Returns:
            True if all tests passed, False if any failed.
        """
        logging.info(f"Running {len(self.tests)} endpoint tests...")
        logging.info(f"Base URL: {self.global_config['baseUrl']}")
        logging.info(f"Concurrent: {self.global_config.get('concurrent', 10)}")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.global_config.get('concurrent', 10))
        
        async with self.create_session() as session:
            tasks = [
                self.run_test_with_semaphore(session, test, semaphore) 
                for test in self.tests
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        passed = 0
        failed = 0
        
        for result in results:
            if isinstance(result, Exception):
                logging.error(f"Test failed with exception: {result}")
                failed += 1
            elif result.passed:
                logging.info(f"✅ {result.name} ({result.duration:.2f}s)")
                passed += 1
            else:
                logging.error(f"❌ {result.name} ({result.duration:.2f}s)")
                logging.error(f"   URL: {result.url}")
                if result.error:
                    logging.error(f"   Error: {result.error}")
                failed += 1
                
                if self.global_config.get('stop-on-fail', False):
                    logging.info("Stopping on first failure")
                    break
        
        logging.info(f"Results: {passed} passed, {failed} failed")
        return failed == 0
    
    def create_session(self) -> aiohttp.ClientSession:
        """
        Create an aiohttp session with configured timeout.
        
        Returns:
            Configured aiohttp ClientSession instance.
        """
        return aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.global_config.get('timeout', 30))
        )
    
    async def run_test_with_semaphore(
        self, 
        session: aiohttp.ClientSession, 
        test: Dict[str, Any], 
        semaphore: asyncio.Semaphore
    ) -> TestResult:
        """
        Run a single test with semaphore-based concurrency control.
        
        Args:
            session: aiohttp session for making requests
            test: Test configuration dictionary
            semaphore: Semaphore for limiting concurrent requests
            
        Returns:
            TestResult containing the test outcome.
        """
        async with semaphore:
            return await self.run_test(session, test)
    
    async def run_test(self, session: aiohttp.ClientSession, test: Dict[str, Any]) -> TestResult:
        """
        Execute a single endpoint test.
        
        Builds the full URL, makes the HTTP request with retry logic,
        and validates the response against expected criteria.
        
        Args:
            session: aiohttp session for making requests
            test: Test configuration dictionary containing endpoint details
            
        Returns:
            TestResult with the test outcome and validation results.
        """
        start_time = asyncio.get_event_loop().time()
        
        # Build URL
        if 'url' in test:
            url = test['url']  # Absolute URL
        else:
            url = urljoin(self.global_config['baseUrl'], test['relative-url'])
        
        method = test.get('type', 'GET').upper()
        test_name = test.get('name', test.get('_source_file', url))
        
        try:
            # Prepare request
            kwargs = {}
            if 'body' in test:
                kwargs['json'] = test['body']
            
            # Make request with retries
            for attempt in range(self.global_config.get('retries', 1)):
                try:
                    async with session.request(method, url, **kwargs) as response:
                        body = await response.text()
                        duration = asyncio.get_event_loop().time() - start_time
                        
                        result = TestResult(
                            name=test_name,
                            url=url,
                            passed=False,
                            expected=test.get('expected', {}),
                            actual={
                                'status': response.status,
                                'body': body,
                                'headers': dict(response.headers)
                            },
                            duration=duration
                        )
                        
                        # Validate response
                        result.passed = self.validate_response(test.get('expected', {}), result.actual)
                        logging.debug(f"Test validation result: {result.passed}")
                        return result
                        
                except asyncio.TimeoutError:
                    if attempt == self.global_config.get('retries', 1) - 1:
                        raise
                    await asyncio.sleep(1)
                    
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            logging.debug(f"Exception in test {test_name}: {e}")
            return TestResult(
                name=test_name,
                url=url,
                passed=False,
                expected=test.get('expected', {}),
                actual={},
                error=str(e),
                duration=duration
            )
    
    def validate_response(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> bool:
        """
        Validate an HTTP response against expected criteria.
        
        Checks status code, content type, CORS headers, and response body
        according to the validation rules specified in the expected criteria.
        
        Args:
            expected: Dictionary containing expected response criteria
            actual: Dictionary containing actual response data
            
        Returns:
            True if all validations pass, False otherwise.
        """
        # Status code validation
        if 'status' in expected:
            expected_status = expected['status']
            # Handle multiple extension
            if isinstance(expected_status, dict) and expected_status.get('type') == 'multiple':
                if actual['status'] not in expected_status['values']:
                    logging.debug(f"Status failed - expected one of {expected_status['values']}, got {actual['status']}")
                    return False
            else:
                if actual['status'] != expected_status:
                    logging.debug(f"Status failed - expected {expected_status}, got {actual['status']}")
                    return False
        
        # Content type validation
        if 'content-type' in expected:
            expected_content_type = expected['content-type']
            # Handle case-insensitive header lookup
            actual_content_type = ''
            for key, value in actual['headers'].items():
                if key.lower() == 'content-type':
                    actual_content_type = value
                    break
            
            # Handle multiple extension
            if isinstance(expected_content_type, dict) and expected_content_type.get('type') == 'multiple':
                content_type_matches = any(
                    actual_content_type.startswith(ct) for ct in expected_content_type['values']
                )
                if not content_type_matches:
                    logging.debug(f"Content-type failed - expected one of {expected_content_type['values']}, got {actual_content_type}")
                    return False
            else:
                logging.debug(f"Content-type check - expected '{expected_content_type}', got '{actual_content_type}'")
                if not actual_content_type.startswith(expected_content_type):
                    logging.debug(f"Content-type failed - expected {expected_content_type}, got {actual_content_type}")
                    return False
        
        # CORS validation
        if 'cors' in expected:
            cors_header = actual['headers'].get('access-control-allow-origin', '')
            if expected['cors'] == '*' and cors_header != '*':
                logging.debug(f"CORS failed - expected *, got {cors_header}")
                return False
            elif expected['cors'] != '*' and expected['cors'] not in cors_header:
                logging.debug(f"CORS failed - expected {expected['cors']}, got {cors_header}")
                return False
        
        # Response body validation
        if 'response' in expected:
            body = actual['body']
            if self.global_config.get('trim', True):
                body = body.strip()
            
            response_config = expected['response']
            response_type = response_config.get('type', 'exact')
            
            if response_type == 'exact':
                if body != response_config['value']:
                    logging.debug(f"Exact match failed - expected '{response_config['value']}', got '{body[:100]}...'")
                    return False
            elif response_type == 'regex':
                if not re.search(response_config['value'], body, re.MULTILINE):
                    logging.debug(f"Regex match failed - pattern '{response_config['value']}' not found in body")
                    return False
            elif response_type == 'contains':
                if response_config['value'] not in body:
                    logging.debug(f"Contains failed - expected '{response_config['value']}' not found in body")
                    return False
            elif response_type == 'empty':
                if body != '':
                    logging.debug(f"Empty check failed - expected empty body, got '{body[:100]}...'")
                    return False
        
        return True 