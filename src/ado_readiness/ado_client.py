"""Azure DevOps REST API client."""

import base64
from typing import Any, Optional

import httpx


class ADOAuthError(Exception):
    """Authentication error for Azure DevOps."""
    pass


class ADOClient:
    """Client for Azure DevOps REST API."""
    
    def __init__(self, organization_url: str, pat: str) -> None:
        """Initialize the ADO client.
        
        Args:
            organization_url: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
            pat: Personal Access Token
        """
        self.organization_url = organization_url.rstrip("/")
        self.pat = pat
        self._client: Optional[httpx.Client] = None
    
    @property
    def client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._client is None:
            # Encode PAT for Basic auth (ADO requires empty username with PAT)
            auth_string = base64.b64encode(f":{self.pat}".encode()).decode()
            self._client = httpx.Client(
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Basic {auth_string}",
                },
                timeout=30.0,
                follow_redirects=False,  # Don't follow auth redirects
            )
        return self._client
    
    def _api_url(self, path: str, project: Optional[str] = None, api_version: str = "7.1") -> str:
        """Build API URL."""
        if project:
            base = f"{self.organization_url}/{project}/_apis"
        else:
            base = f"{self.organization_url}/_apis"
        
        separator = "&" if "?" in path else "?"
        return f"{base}/{path}{separator}api-version={api_version}"
    
    def _get(self, path: str, project: Optional[str] = None, **kwargs: Any) -> dict[str, Any]:
        """Make GET request to ADO API."""
        url = self._api_url(path, project)
        response = self.client.get(url, **kwargs)
        
        # Check for auth redirect (302 to login page)
        if response.status_code in (301, 302, 303):
            raise ADOAuthError(
                "Authentication failed. Please verify your PAT is valid and has not expired.\n"
                "Create a new PAT at: https://dev.azure.com/{org}/_usersSettings/tokens"
            )
        
        response.raise_for_status()
        return response.json()
    
    def _get_all(self, path: str, project: Optional[str] = None, **kwargs: Any) -> list[dict[str, Any]]:
        """Get all items with pagination support."""
        items: list[dict[str, Any]] = []
        continuation_token = None
        
        while True:
            params = kwargs.get("params", {})
            if continuation_token:
                params["continuationToken"] = continuation_token
            kwargs["params"] = params
            
            response = self._get(path, project, **kwargs)
            
            if isinstance(response, dict):
                items.extend(response.get("value", []))
                continuation_token = response.get("continuationToken")
            else:
                items.extend(response)
                break
            
            if not continuation_token:
                break
        
        return items
    
    # ==================== Projects ====================
    
    def get_projects(self) -> list[dict[str, Any]]:
        """Get all projects in the organization."""
        return self._get_all("projects")
    
    def get_project(self, project_name: str) -> dict[str, Any]:
        """Get a specific project."""
        return self._get(f"projects/{project_name}")
    
    # ==================== Repositories ====================
    
    def get_repositories(self, project: Optional[str] = None) -> list[dict[str, Any]]:
        """Get all Git repositories."""
        if project:
            return self._get_all("git/repositories", project)
        
        repos = []
        for proj in self.get_projects():
            try:
                proj_repos = self._get_all("git/repositories", proj["name"])
                repos.extend(proj_repos)
            except Exception:
                pass
        return repos
    
    def get_repository(self, project: str, repo_id: str) -> dict[str, Any]:
        """Get a specific repository."""
        return self._get(f"git/repositories/{repo_id}", project)
    
    def get_branches(self, project: str, repo_id: str) -> list[dict[str, Any]]:
        """Get branches for a repository."""
        try:
            return self._get_all(f"git/repositories/{repo_id}/refs?filter=heads/", project)
        except Exception:
            return []
    
    def check_tfvc(self, project: str) -> bool:
        """Check if project uses TFVC."""
        try:
            result = self._get("tfvc/items", project, params={"scopePath": f"$/{project}"})
            return len(result.get("value", [])) > 0
        except Exception:
            return False
    
    # ==================== Pipelines ====================
    
    def get_pipelines(self, project: str) -> list[dict[str, Any]]:
        """Get all pipelines (YAML) in a project."""
        try:
            return self._get_all("pipelines", project)
        except Exception:
            return []
    
    def get_build_definitions(self, project: str) -> list[dict[str, Any]]:
        """Get all build definitions (Classic + YAML)."""
        try:
            return self._get_all("build/definitions", project)
        except Exception:
            return []
    
    def get_release_definitions(self, project: str) -> list[dict[str, Any]]:
        """Get all release definitions (Classic only)."""
        try:
            url = f"{self.organization_url}/{project}/_apis/release/definitions?api-version=7.1"
            response = self.client.get(url)
            if response.status_code == 404:
                return []
            response.raise_for_status()
            return response.json().get("value", [])
        except Exception:
            return []
    
    # ==================== Work Items ====================
    
    def get_work_item_types(self, project: str) -> list[dict[str, Any]]:
        """Get work item types for a project."""
        try:
            return self._get_all("wit/workitemtypes", project)
        except Exception:
            return []
    
    def count_work_items(self, project: str) -> int:
        """Get total count of work items in a project."""
        try:
            wiql = {"query": f"SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = '{project}'"}
            url = self._api_url("wit/wiql", project)
            response = self.client.post(url, json=wiql)
            if response.status_code == 200:
                return len(response.json().get("workItems", []))
            return 0
        except Exception:
            return 0
    
    def get_work_item_counts_by_type(self, project: str) -> dict[str, int]:
        """Get count of work items by type."""
        counts: dict[str, int] = {}
        types = self.get_work_item_types(project)
        
        for wit in types:
            type_name = wit["name"]
            try:
                wiql = {
                    "query": f"SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = '{project}' AND [System.WorkItemType] = '{type_name}'"
                }
                url = self._api_url("wit/wiql", project)
                response = self.client.post(url, json=wiql)
                if response.status_code == 200:
                    counts[type_name] = len(response.json().get("workItems", []))
            except Exception:
                counts[type_name] = 0
        
        return counts
    
    def get_custom_fields(self, project: str) -> list[dict[str, Any]]:
        """Get custom work item fields."""
        try:
            fields = self._get_all("wit/fields", project)
            return [f for f in fields if not f.get("name", "").startswith("System.")]
        except Exception:
            return []
    
    # ==================== Boards ====================
    
    def get_teams(self, project: str) -> list[dict[str, Any]]:
        """Get all teams in a project."""
        try:
            return self._get_all(f"projects/{project}/teams")
        except Exception:
            return []
    
    def get_boards(self, project: str, team: str) -> list[dict[str, Any]]:
        """Get boards for a team."""
        try:
            url = f"{self.organization_url}/{project}/{team}/_apis/work/boards?api-version=7.1"
            response = self.client.get(url)
            if response.status_code != 200:
                return []
            return response.json().get("value", [])
        except Exception:
            return []
    
    # ==================== Service Connections ====================
    
    def get_service_connections(self, project: str) -> list[dict[str, Any]]:
        """Get service connections/endpoints."""
        try:
            return self._get_all("serviceendpoint/endpoints", project)
        except Exception:
            return []
    
    # ==================== Variable Groups ====================
    
    def get_variable_groups(self, project: str) -> list[dict[str, Any]]:
        """Get variable groups."""
        try:
            return self._get_all("distributedtask/variablegroups", project)
        except Exception:
            return []
    
    # ==================== Test Plans ====================
    
    def get_test_plans(self, project: str) -> list[dict[str, Any]]:
        """Get test plans."""
        try:
            return self._get_all("testplan/plans", project)
        except Exception:
            return []
    
    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None
