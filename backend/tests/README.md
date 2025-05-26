# API Tests for Agent Pipeline Visualizer

This directory contains unit and integration tests for the API endpoints of the Agent Pipeline Visualizer backend.

## Test Structure

- `test_api.py` - Basic unit tests for all API endpoints
- `test_edge_cases.py` - Tests for error handling and edge cases
- `test_integration.py` - Integration tests for complete workflows

## Running the Tests

You can run the tests in several ways:

### Using the run_tests.sh script

```bash
./tests/run_tests.sh
```

This will run all the tests and show a summary of the results.

### Using Python's unittest module directly

```bash
# Run all tests
python -m unittest discover -s tests

# Run a specific test file
python -m unittest tests/test_api.py

# Run a specific test class
python -m unittest tests.test_api.APITestCase

# Run a specific test method
python -m unittest tests.test_api.APITestCase.test_get_config
```

## Test Environment

The tests use a temporary directory for all file operations to avoid interfering with the actual application data. Each test:

1. Creates a temporary directory
2. Redirects all file paths to use this directory
3. Runs the test
4. Cleans up by removing the temporary directory

## Mocking

Some tests use the `unittest.mock` module to mock dependencies. For example, in `test_run_step()` we mock the `AgentBase` class to avoid requiring the actual agent implementation.

## Prerequisites

Before running the tests, ensure all dependencies are installed:

```bash
pip install -r ../requirements.txt
```
