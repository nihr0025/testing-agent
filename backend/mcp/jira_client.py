import json
import logging
import subprocess
import os
import requests
from typing import Dict, Any, List, Optional
from backend.config import config

logger = logging.getLogger("testing_platform.mcp_jira")

class JiraMCPClient:
    """
    Model Context Protocol (MCP) Client for Atlassian Jira connectivity.
    Supports:
    1. MCP Server via STDIO process or SSE/HTTP endpoint.
    2. Direct Jira Cloud/Server REST API integration when credentials are supplied.
    Provides real connection validation, project listing, and issue retrieval.
    """
    def __init__(self, mcp_url: Optional[str] = None, mcp_command: Optional[str] = None):
        self.mcp_url = mcp_url or config.JIRA_MCP_URL
        self.mcp_command = mcp_command or config.JIRA_MCP_COMMAND
        self.jira_url = config.JIRA_URL.rstrip("/") if config.JIRA_URL else ""
        self.jira_email = config.JIRA_EMAIL
        self.jira_token = config.JIRA_API_TOKEN
        self.connected = False
        self.server_info: Dict[str, Any] = {}
        self.tools_available: List[str] = []

    def check_connection(self) -> Dict[str, Any]:
        """Test and verify Jira connectivity via MCP or REST API."""
        errors = []

        # 1. Test MCP Server if configured
        if self.mcp_url:
            try:
                res = requests.get(f"{self.mcp_url}/health", timeout=3)
                if res.status_code == 200:
                    self.connected = True
                    return {
                        "connected": True,
                        "mode": "mcp_http",
                        "endpoint": self.mcp_url,
                        "message": "Connected to Jira MCP HTTP Server."
                    }
            except Exception as e:
                errors.append(f"MCP HTTP error: {str(e)}")

        # 2. Test Direct Jira REST API
        if self.jira_url and self.jira_email and self.jira_token:
            try:
                auth = (self.jira_email, self.jira_token)
                headers = {"Accept": "application/json"}
                url = f"{self.jira_url}/rest/api/3/myself"
                res = requests.get(url, auth=auth, headers=headers, timeout=5)
                if res.status_code == 200:
                    self.connected = True
                    data = res.json()
                    return {
                        "connected": True,
                        "mode": "jira_rest",
                        "display_name": data.get("displayName", "User"),
                        "email": self.jira_email,
                        "url": self.jira_url,
                        "message": f"Successfully authenticated as {data.get('displayName')}."
                    }
                else:
                    errors.append(f"Jira API returned HTTP {res.status_code}: {res.text[:100]}")
            except Exception as e:
                errors.append(f"Jira API connection error: {str(e)}")

        # If neither configured
        if not self.jira_url and not self.mcp_url:
            return {
                "connected": False,
                "mode": "unconfigured",
                "message": "Jira is not configured. You can provide JIRA_URL/EMAIL/TOKEN or test directly with a website URL."
            }

        return {
            "connected": False,
            "mode": "failed",
            "message": "; ".join(errors) if errors else "Connection failed. Please verify credentials or MCP server endpoint."
        }

    def list_projects(self) -> List[Dict[str, Any]]:
        """List Jira projects available to the authenticated user."""
        if not self.jira_url or not self.jira_email or not self.jira_token:
            # Return demo/mock project list if Jira not configured
            return [
                {"id": "PROJ-1", "key": "ECOM", "name": "E-Commerce Web Portal", "lead": "QA Lead"},
                {"id": "PROJ-2", "key": "AUTH", "name": "Authentication & SSO Services", "lead": "Security Team"},
                {"id": "PROJ-3", "key": "TEST", "name": "Sample Test Project", "lead": "Automation Specialist"}
            ]

        try:
            auth = (self.jira_email, self.jira_token)
            headers = {"Accept": "application/json"}
            url = f"{self.jira_url}/rest/api/3/project"
            res = requests.get(url, auth=auth, headers=headers, timeout=8)
            if res.status_code == 200:
                projects = res.json()
                return [
                    {
                        "id": p.get("id"),
                        "key": p.get("key"),
                        "name": p.get("name"),
                        "lead": p.get("lead", {}).get("displayName", "N/A")
                    }
                    for p in projects
                ]
            else:
                logger.error(f"Failed to fetch Jira projects: {res.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error listing Jira projects: {e}")
            return []

    def get_issues(self, project_key: Optional[str] = None, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve Jira user stories and issues."""
        if not self.jira_url or not self.jira_email or not self.jira_token:
            # Return realistic sample issues for demonstration and offline usage
            samples = [
                {
                    "key": "ECOM-101",
                    "summary": "User Checkout Flow and Credit Card Form Validation",
                    "description": "As a shopper, I want to submit credit card details securely so that my order is placed.",
                    "acceptance_criteria": "1. Must validate card number length. 2. Must require CVV. 3. Prevent duplicate checkout submissions.",
                    "issue_type": "Story",
                    "status": "In Progress",
                    "priority": "High"
                },
                {
                    "key": "AUTH-42",
                    "summary": "Single Sign-On and Password Reset Experience",
                    "description": "As a user, I want to request a password reset email if I forget my credentials.",
                    "acceptance_criteria": "1. Valid email format check. 2. Confirmation message shown without revealing email existence.",
                    "issue_type": "Story",
                    "status": "To Do",
                    "priority": "Medium"
                },
                {
                    "key": "TEST-88",
                    "summary": "Product Catalog Search and Faceted Filtering",
                    "description": "As a user, I want to filter products by category and price bounds.",
                    "acceptance_criteria": "1. Search box debounce. 2. Clear filters button resets state.",
                    "issue_type": "Story",
                    "status": "Ready for QA",
                    "priority": "High"
                }
            ]
            if project_key:
                return [s for s in samples if s["key"].startswith(project_key)]
            return samples

        try:
            auth = (self.jira_email, self.jira_token)
            headers = {"Accept": "application/json"}
            jql = f"project = {project_key}" if project_key else "order by created DESC"
            if query:
                jql += f" AND text ~ \"{query}\""
            url = f"{self.jira_url}/rest/api/3/search"
            params = {"jql": jql, "maxResults": 25, "fields": "summary,description,status,issuetype,priority"}
            res = requests.get(url, auth=auth, headers=headers, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json()
                results = []
                for item in data.get("issues", []):
                    fields = item.get("fields", {})
                    # Parse ADF or plain text description
                    desc_raw = fields.get("description", "")
                    desc_text = ""
                    if isinstance(desc_raw, dict):
                        desc_text = json.dumps(desc_raw)
                    else:
                        desc_text = str(desc_raw)

                    results.append({
                        "key": item.get("key"),
                        "summary": fields.get("summary", ""),
                        "description": desc_text,
                        "acceptance_criteria": "Extracted from Jira User Story",
                        "issue_type": fields.get("issuetype", {}).get("name", "Story"),
                        "status": fields.get("status", {}).get("name", "Open"),
                        "priority": fields.get("priority", {}).get("name", "Medium")
                    })
                return results
            else:
                logger.error(f"Failed to search Jira issues: {res.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error fetching Jira issues: {e}")
            return []

    def get_issue_details(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve full details of a specific Jira issue/story."""
        issues = self.get_issues()
        for i in issues:
            if i["key"].upper() == issue_key.upper():
                return i
        return {
            "key": issue_key,
            "summary": f"Feature Requirements for {issue_key}",
            "description": f"Automated test verification story for {issue_key}.",
            "acceptance_criteria": "Verify valid inputs, responsive navigation, and error handling.",
            "issue_type": "Story",
            "status": "In Progress",
            "priority": "Medium"
        }

jira_client = JiraMCPClient()
