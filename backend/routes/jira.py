from fastapi import APIRouter, Query
from typing import Optional
from backend.mcp.jira_client import jira_client

router = APIRouter(prefix="/api/jira", tags=["Jira MCP Integration"])

@router.get("/status")
def get_jira_status():
    """Check Jira / MCP connection state."""
    return jira_client.check_connection()

@router.get("/projects")
def list_jira_projects():
    """Retrieve available Jira projects."""
    return jira_client.list_projects()

@router.get("/issues")
def list_jira_issues(project: Optional[str] = Query(None), q: Optional[str] = Query(None)):
    """Retrieve Jira user stories and issues."""
    return jira_client.get_issues(project_key=project, query=q)

@router.get("/issues/{issue_key}")
def get_jira_issue(issue_key: str):
    """Retrieve specific Jira issue details."""
    issue = jira_client.get_issue_details(issue_key)
    return issue
