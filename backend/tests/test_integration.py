"""
Integration tests for the agent-pipeline-visualizer API.

This module tests sequences of API calls that mimic real-world usage
of the agent pipeline, ensuring that the entire workflow functions correctly.

Usage:
    python -m unittest tests/test_integration.py
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


class IntegrationTestCase(unittest.TestCase):
    """Test case for integration tests of API endpoint sequences."""

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

    def test_complete_workflow(self):
        """Test a complete workflow through the API.

        This test simulates the flow of:
        1. Getting initial configuration
        2. Updating a step's status to running
        3. Updating the step to waiting_input
        4. Approving the step
        5. Updating the step to completed
        6. Checking the final status
        """
        # 1. Get initial configuration and step status
        response = self.client.get("/api/config")
        self.assertEqual(response.status_code, 200)
        config = json.loads(response.data)

        # Get the first step ID
        first_step_id = config["steps"][0]["id"]

        # 2. Update step status to running
        response = self.client.post(
            f"/api/steps/{first_step_id}",
            json={"status": "running"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        # Check that the status was updated
        response = self.client.get(f"/api/steps/{first_step_id}")
        self.assertEqual(response.status_code, 200)
        step_data = json.loads(response.data)
        self.assertEqual(step_data["status"], "running")

        # 3. Update step status to waiting_input
        response = self.client.post(
            f"/api/steps/{first_step_id}",
            json={"status": "waiting_input"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        # 4. Approve the step
        response = self.client.post(f"/api/steps/{first_step_id}/approve")
        self.assertEqual(response.status_code, 200)

        # Check that the .approved file was created
        approval_file = os.path.join(
            self.app_module.STEPS_DIR, first_step_id, "out", ".approved"
        )
        self.assertTrue(os.path.exists(approval_file))

        # 5. Update step status to completed
        response = self.client.post(
            f"/api/steps/{first_step_id}",
            json={"status": "completed"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        # 6. Check final status
        response = self.client.get(f"/api/steps/{first_step_id}")
        self.assertEqual(response.status_code, 200)
        step_data = json.loads(response.data)
        self.assertEqual(step_data["status"], "completed")

    def test_file_workflow(self):
        """Test a workflow focused on file operations.

        This test simulates:
        1. Creating a file using the API
        2. Reading the file content
        3. Creating a step output file
        4. Getting the files for a step
        """
        # 1. Create a file using the API
        test_content = "This is test content for the file."
        test_file_path = os.path.join(self.test_dir, "test_file.txt")

        response = self.client.post(
            "/api/files",
            json={"path": test_file_path, "content": test_content},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        # 2. Read the file content
        response = self.client.get(f"/api/files?path={test_file_path}")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["content"], test_content)

        # 3. Create a step output file
        config = self.app_module.load_config()
        step_id = config["steps"][0]["id"]

        step_out_dir = os.path.join(self.app_module.STEPS_DIR, step_id, "out")
        os.makedirs(step_out_dir, exist_ok=True)

        step_file_path = os.path.join(step_out_dir, "result.txt")
        step_content = "Step result content"

        response = self.client.post(
            "/api/files",
            json={"path": step_file_path, "content": step_content},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        # 4. Get files for the step
        response = self.client.get(f"/api/steps/{step_id}/files")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("files", data)
        self.assertEqual(len(data["files"]), 1)


if __name__ == "__main__":
    unittest.main()
