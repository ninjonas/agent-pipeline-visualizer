"""
Edge case tests for the agent-pipeline-visualizer API endpoints.

This module tests error handling and edge cases for the API endpoints
defined in app.py, using a temporary directory to avoid affecting real data.

Usage:
    python -m unittest tests/test_edge_cases.py
"""

import os
import sys
import json
import shutil
import tempfile
import unittest
from unittest import mock

# Add the backend directory to system path to import app
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, backend_dir)

# Now import the app module
import app as app_module
from app import app


class EdgeCaseTestCase(unittest.TestCase):
    """Test case for edge cases and error handling in the API endpoints."""

    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()

        # Store original values
        self.app_module = app_module
        self.original_agent_dir = app_module.AGENT_DIR
        self.original_steps_dir = app_module.STEPS_DIR
        self.original_config_file = app_module.CONFIG_FILE

        # Update variables in app module
        app_module.AGENT_DIR = os.path.join(self.test_dir, "agent")
        app_module.STEPS_DIR = os.path.join(app_module.AGENT_DIR, "steps")
        app_module.CONFIG_FILE = os.path.join(app_module.AGENT_DIR, "config.json")

        # Create necessary directories
        app_module.ensure_directories()

        # Configure Flask app for testing
        app.config["TESTING"] = True
        self.client = app.test_client()

    def tearDown(self):
        """Clean up after each test."""
        # Restore original paths
        self.app_module.AGENT_DIR = self.original_agent_dir
        self.app_module.STEPS_DIR = self.original_steps_dir
        self.app_module.CONFIG_FILE = self.original_config_file

        # Remove temporary directory
        shutil.rmtree(self.test_dir)

    def test_get_nonexistent_step(self):
        """Test GET /api/steps/<step_id> with a non-existent step ID."""
        response = self.client.get("/api/steps/nonexistent_step")
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data["error"], "Step not found")

    def test_post_step_missing_status(self):
        """Test POST /api/steps/<step_id> with missing status."""
        config = self.app_module.load_config()
        step_id = config["steps"][0]["id"]

        # Missing status in request
        response = self.client.post(
            f"/api/steps/{step_id}", json={}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)

    def test_approve_step_with_wrong_status(self):
        """Test POST /api/steps/<step_id>/approve for a step not waiting for input."""
        # First, ensure there's a step
        config = self.app_module.load_config()
        step_id = config["steps"][0]["id"]

        # Create a status.json file with the step in a status other than waiting_input
        status_data = {step_id: {"status": "running"}}
        status_file = os.path.join(self.app_module.AGENT_DIR, "status.json")
        with open(status_file, "w") as f:
            json.dump(status_data, f, indent=2)

        response = self.client.post(f"/api/steps/{step_id}/approve")
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)

    def test_get_nonexistent_file(self):
        """Test GET /api/files with a non-existent file path."""
        response = self.client.get("/api/files?path=/nonexistent/path.txt")
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data["error"], "File not found")

    def test_post_file_missing_path(self):
        """Test POST /api/files with missing path."""
        file_data = {
            "content": "Test content"
            # Missing 'path' field
        }

        response = self.client.post(
            "/api/files", json=file_data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["error"], "No file path provided")


if __name__ == "__main__":
    unittest.main()
