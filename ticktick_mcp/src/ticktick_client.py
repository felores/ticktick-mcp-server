"""
TickTick API client with OAuth2 authentication.

Credentials are loaded from:
- Client ID/Secret: Environment variables (set in MCP client config)
- Access/Refresh tokens: Persistent storage (~/.config/ticktick-mcp/)
"""

import os
import base64
import re
import requests
import logging
from typing import Dict, List, Optional

from .credentials import load_credentials, save_credentials, get_access_token, get_refresh_token

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Raised when authentication is required."""
    pass


class TickTickClient:
    """Client for the TickTick API using OAuth2 authentication."""

    def __init__(self):
        # Client credentials from environment (passed via MCP client config)
        self.client_id = os.getenv("TICKTICK_CLIENT_ID")
        self.client_secret = os.getenv("TICKTICK_CLIENT_SECRET")

        # Tokens from persistent storage
        self.access_token = get_access_token()
        self.refresh_token = get_refresh_token()

        # API URLs (can be overridden for Dida365)
        self.base_url = os.getenv("TICKTICK_BASE_URL", "https://api.ticktick.com/open/v1")
        self.token_url = os.getenv("TICKTICK_TOKEN_URL", "https://ticktick.com/oauth/token")

        # Check authentication status
        if not self.access_token:
            if not self.client_id or not self.client_secret:
                raise AuthenticationError(
                    "TickTick credentials not configured. "
                    "Please add TICKTICK_CLIENT_ID and TICKTICK_CLIENT_SECRET to your MCP client config."
                )
            raise AuthenticationError(
                "Not authenticated with TickTick. "
                "Please run 'uvx ticktick-mcp-server auth' to connect your account."
            )

        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "User-Agent": "ticktick-mcp-server/0.2.2"
        }

    def _refresh_access_token(self) -> bool:
        """
        Refresh the access token using the refresh token.

        Returns:
            True if successful, False otherwise
        """
        if not self.refresh_token:
            logger.warning("No refresh token available. Cannot refresh access token.")
            return False

        if not self.client_id or not self.client_secret:
            logger.warning("Client credentials missing. Cannot refresh access token.")
            return False

        token_data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }

        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_b64 = base64.b64encode(auth_str.encode('ascii')).decode('ascii')

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            response = requests.post(self.token_url, data=token_data, headers=headers, verify=True)
            response.raise_for_status()

            tokens = response.json()

            # Update tokens
            self.access_token = tokens.get('access_token')
            if 'refresh_token' in tokens:
                self.refresh_token = tokens.get('refresh_token')

            # Update headers
            self.headers["Authorization"] = f"Bearer {self.access_token}"

            # Save to persistent storage
            save_credentials({
                'access_token': self.access_token,
                'refresh_token': self.refresh_token
            })

            logger.info("Access token refreshed successfully.")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Error refreshing access token: {e}")
            return False

    def _validate_id(self, id_value: str, id_name: str) -> None:
        """
        Validate that an ID contains only safe characters to prevent path traversal.

        Args:
            id_value: The ID value to validate
            id_name: The name of the ID field (for error messages)

        Raises:
            ValueError: If the ID is empty or contains unsafe characters
        """
        if not id_value:
            raise ValueError(f"{id_name} cannot be empty")
        if not re.match(r'^[a-zA-Z0-9_-]+$', id_value):
            raise ValueError(f"Invalid {id_name} format")

    def _make_request(self, method: str, endpoint: str, data=None) -> Dict:
        """
        Makes a request to the TickTick API.

        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request data (for POST)

        Returns:
            API response as a dictionary
        """
        url = f"{self.base_url}{endpoint}"

        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, verify=True)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data, verify=True)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers, verify=True)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Handle token expiration
            if response.status_code == 401:
                logger.info("Access token expired. Attempting to refresh...")
                if self._refresh_access_token():
                    # Retry request
                    if method == "GET":
                        response = requests.get(url, headers=self.headers, verify=True)
                    elif method == "POST":
                        response = requests.post(url, headers=self.headers, json=data, verify=True)
                    elif method == "DELETE":
                        response = requests.delete(url, headers=self.headers, verify=True)

            response.raise_for_status()

            if response.status_code == 204 or response.text == "":
                return {}

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return {"error": str(e)}

    # Project methods
    def get_projects(self) -> List[Dict]:
        """Gets all projects for the user."""
        return self._make_request("GET", "/project")

    def get_project(self, project_id: str) -> Dict:
        """Gets a specific project by ID."""
        self._validate_id(project_id, "project_id")
        return self._make_request("GET", f"/project/{project_id}")

    def get_project_with_data(self, project_id: str) -> Dict:
        """Gets project with tasks and columns."""
        self._validate_id(project_id, "project_id")
        return self._make_request("GET", f"/project/{project_id}/data")

    def create_project(self, name: str, color: str = "#F18181", view_mode: str = "list", kind: str = "TASK") -> Dict:
        """Creates a new project."""
        data = {
            "name": name,
            "color": color,
            "viewMode": view_mode,
            "kind": kind
        }
        return self._make_request("POST", "/project", data)

    def update_project(self, project_id: str, name: str = None, color: str = None,
                       view_mode: str = None, kind: str = None) -> Dict:
        """Updates an existing project."""
        self._validate_id(project_id, "project_id")
        data = {}
        if name:
            data["name"] = name
        if color:
            data["color"] = color
        if view_mode:
            data["viewMode"] = view_mode
        if kind:
            data["kind"] = kind
        return self._make_request("POST", f"/project/{project_id}", data)

    def delete_project(self, project_id: str) -> Dict:
        """Deletes a project."""
        self._validate_id(project_id, "project_id")
        return self._make_request("DELETE", f"/project/{project_id}")

    # Task methods
    def get_task(self, project_id: str, task_id: str) -> Dict:
        """Gets a specific task by project ID and task ID."""
        self._validate_id(project_id, "project_id")
        self._validate_id(task_id, "task_id")
        return self._make_request("GET", f"/project/{project_id}/task/{task_id}")

    def create_task(self, title: str, project_id: str, content: str = None,
                    start_date: str = None, due_date: str = None,
                    priority: int = 0, is_all_day: bool = False) -> Dict:
        """Creates a new task."""
        self._validate_id(project_id, "project_id")
        data = {
            "title": title,
            "projectId": project_id
        }
        if content:
            data["content"] = content
        if start_date:
            data["startDate"] = start_date
        if due_date:
            data["dueDate"] = due_date
        if priority is not None:
            data["priority"] = priority
        if is_all_day is not None:
            data["isAllDay"] = is_all_day
        return self._make_request("POST", "/task", data)

    def update_task(self, task_id: str, project_id: str, title: str = None,
                    content: str = None, priority: int = None,
                    start_date: str = None, due_date: str = None) -> Dict:
        """Updates an existing task."""
        self._validate_id(task_id, "task_id")
        self._validate_id(project_id, "project_id")
        data = {
            "id": task_id,
            "projectId": project_id
        }
        if title:
            data["title"] = title
        if content:
            data["content"] = content
        if priority is not None:
            data["priority"] = priority
        if start_date:
            data["startDate"] = start_date
        if due_date:
            data["dueDate"] = due_date
        return self._make_request("POST", f"/task/{task_id}", data)

    def complete_task(self, project_id: str, task_id: str) -> Dict:
        """Marks a task as complete."""
        self._validate_id(project_id, "project_id")
        self._validate_id(task_id, "task_id")
        return self._make_request("POST", f"/project/{project_id}/task/{task_id}/complete")

    def delete_task(self, project_id: str, task_id: str) -> Dict:
        """Deletes a task."""
        self._validate_id(project_id, "project_id")
        self._validate_id(task_id, "task_id")
        return self._make_request("DELETE", f"/project/{project_id}/task/{task_id}")

    def create_subtask(self, subtask_title: str, parent_task_id: str, project_id: str,
                       content: str = None, priority: int = 0) -> Dict:
        """Creates a subtask for a parent task within the same project."""
        self._validate_id(project_id, "project_id")
        self._validate_id(parent_task_id, "parent_task_id")
        data = {
            "title": subtask_title,
            "projectId": project_id,
            "parentId": parent_task_id
        }
        if content:
            data["content"] = content
        if priority is not None:
            data["priority"] = priority
        return self._make_request("POST", "/task", data)
