"""
Zysys API Test Framework

A powerful, parallel HTTP endpoint testing framework with automatic core detection,
rich CLI interface, and flexible configuration management.

This package provides:
- EndpointTester: Core testing engine for parallel HTTP validation
- TestResult: Data structure for test results
- ZysysTestCLI: Command-line interface with rich terminal output
- Comprehensive validation: Status codes, content types, CORS, response body

Example usage:
    from src import EndpointTester
    
    tester = EndpointTester("test/configs")
    success = await tester.run_tests()
"""

__version__ = "2.0.2"
__author__ = "ZAB Ai, LLC"
__license__ = "Zysys API Test Framework License"

from .core import EndpointTester, TestResult
from .cli import ZysysTestCLI, show_help, main

__all__ = [
    'EndpointTester',
    'TestResult', 
    'ZysysTestCLI',
    'show_help',
    'main'
] 