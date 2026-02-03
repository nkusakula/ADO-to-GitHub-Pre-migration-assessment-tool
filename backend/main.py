"""FastAPI backend for ADO Migration Readiness Analyzer."""

import asyncio
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ado_readiness.config import ADOConfig, save_config, get_config, config_exists, delete_config
from ado_readiness.ado_client import ADOClient, ADOAuthError
from ado_readiness.scanner import OrganizationScanner
from rich.console import Console

# Store for active connections and scan state
class AppState:
    def __init__(self):
        self.scan_results: dict[str, Any] | None = None
        self.scan_in_progress: bool = False
        self.scan_progress: dict[str, Any] = {}
        self.migration_in_progress: bool = False
        self.migration_progress: dict[str, Any] = {}
        self.websocket_connections: list[WebSocket] = []

state = AppState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    state.websocket_connections.clear()

app = FastAPI(
    title="ADO Migration Readiness Analyzer",
    description="Analyze Azure DevOps organizations and migrate to GitHub",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Models ====================

class ConfigRequest(BaseModel):
    organization_url: str
    pat: str
    github_token: str | None = None
    github_org: str | None = None


class ConfigResponse(BaseModel):
    configured: bool
    organization_url: str | None = None
    github_org: str | None = None


class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    projects: list[dict[str, Any]] | None = None


class ScanRequest(BaseModel):
    project: str | None = None


class MigrateRequest(BaseModel):
    repos: list[str]
    target_org: str
    visibility: str = "private"


class MigrationStatus(BaseModel):
    repo: str
    status: str  # pending, in_progress, completed, failed
    progress: int
    message: str


# ==================== WebSocket ====================

@app.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    """WebSocket for real-time progress updates."""
    await websocket.accept()
    state.websocket_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        state.websocket_connections.remove(websocket)


async def broadcast_progress(data: dict[str, Any]):
    """Broadcast progress to all connected clients."""
    for connection in state.websocket_connections:
        try:
            await connection.send_json(data)
        except Exception:
            pass


# ==================== Config Endpoints ====================

@app.get("/api/config", response_model=ConfigResponse)
async def get_configuration():
    """Get current configuration status."""
    if not config_exists():
        return ConfigResponse(configured=False)
    
    try:
        config = get_config()
        return ConfigResponse(
            configured=True,
            organization_url=config.organization_url,
        )
    except Exception:
        return ConfigResponse(configured=False)


@app.post("/api/config")
async def save_configuration(request: ConfigRequest):
    """Save configuration."""
    try:
        config = ADOConfig(
            organization_url=request.organization_url,
            pat=request.pat,
        )
        save_config(config)
        
        # Store GitHub config separately if provided
        if request.github_token:
            github_config_file = get_config_dir() / "github_config.yaml"
            import yaml
            with open(github_config_file, "w") as f:
                yaml.safe_dump({
                    "token": request.github_token,
                    "org": request.github_org,
                }, f)
        
        return {"success": True, "message": "Configuration saved"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/config")
async def delete_configuration():
    """Delete configuration."""
    delete_config()
    return {"success": True, "message": "Configuration deleted"}


# ==================== Connection Test ====================

@app.get("/api/test-connection", response_model=ConnectionTestResponse)
async def test_connection():
    """Test connection to Azure DevOps."""
    if not config_exists():
        return ConnectionTestResponse(
            success=False,
            message="Not configured. Please configure first.",
        )
    
    try:
        config = get_config()
        client = ADOClient(config.organization_url, config.pat)
        projects = client.get_projects()
        client.close()
        
        return ConnectionTestResponse(
            success=True,
            message=f"Connected successfully! Found {len(projects)} projects.",
            projects=[{"name": p.get("name"), "description": p.get("description")} for p in projects],
        )
    except ADOAuthError as e:
        return ConnectionTestResponse(success=False, message=str(e))
    except Exception as e:
        return ConnectionTestResponse(success=False, message=f"Connection failed: {e}")


# ==================== Scan Endpoints ====================

@app.post("/api/scan")
async def start_scan(request: ScanRequest):
    """Start organization scan."""
    if state.scan_in_progress:
        raise HTTPException(status_code=409, detail="Scan already in progress")
    
    if not config_exists():
        raise HTTPException(status_code=400, detail="Not configured")
    
    # Start scan in background
    asyncio.create_task(run_scan(request.project))
    
    return {"success": True, "message": "Scan started"}


async def run_scan(project_filter: str | None = None):
    """Run scan in background."""
    state.scan_in_progress = True
    state.scan_progress = {"status": "starting", "progress": 0}
    
    try:
        config = get_config()
        client = ADOClient(config.organization_url, config.pat)
        
        # Get projects
        if project_filter:
            projects = [{"name": project_filter}]
        else:
            projects = client.get_projects()
        
        total = len(projects)
        results = {
            "organization_url": config.organization_url,
            "projects": [],
            "summary": {},
        }
        
        for i, proj in enumerate(projects):
            project_name = proj["name"]
            state.scan_progress = {
                "status": "scanning",
                "progress": int((i / total) * 100),
                "current_project": project_name,
                "projects_scanned": i,
                "total_projects": total,
            }
            await broadcast_progress({"type": "scan", **state.scan_progress})
            
            # Scan project (simplified for async)
            project_data = await scan_project_async(client, project_name)
            results["projects"].append(project_data)
        
        # Calculate summary
        from ado_readiness.scanner import OrganizationScanner
        console = Console(force_terminal=True, no_color=True)
        scanner = OrganizationScanner(client, console)
        results["summary"] = scanner._calculate_summary(results["projects"])
        
        state.scan_results = results
        state.scan_progress = {"status": "completed", "progress": 100}
        await broadcast_progress({"type": "scan", **state.scan_progress})
        
        client.close()
        
    except Exception as e:
        state.scan_progress = {"status": "failed", "error": str(e)}
        await broadcast_progress({"type": "scan", **state.scan_progress})
    finally:
        state.scan_in_progress = False


async def scan_project_async(client: ADOClient, project_name: str) -> dict[str, Any]:
    """Scan a single project."""
    repos = client.get_repositories(project_name)
    tfvc_used = client.check_tfvc(project_name)
    pipelines = client.get_pipelines(project_name)
    build_defs = client.get_build_definitions(project_name)
    release_defs = client.get_release_definitions(project_name)
    work_item_counts = client.get_work_item_counts_by_type(project_name)
    work_item_types = client.get_work_item_types(project_name)
    teams = client.get_teams(project_name)
    service_connections = client.get_service_connections(project_name)
    variable_groups = client.get_variable_groups(project_name)
    test_plans = client.get_test_plans(project_name)
    
    return {
        "name": project_name,
        "repositories": {
            "count": len(repos),
            "tfvc_used": tfvc_used,
            "items": [{"name": r.get("name"), "id": r.get("id"), "size": r.get("size", 0), "url": r.get("webUrl")} for r in repos],
        },
        "pipelines": {
            "yaml_count": len(pipelines),
            "build_definitions": len(build_defs),
            "release_definitions": len(release_defs),
            "classic_count": len([d for d in build_defs if d.get("type") == "build"]),
        },
        "work_items": {
            "total": sum(work_item_counts.values()),
            "by_type": work_item_counts,
            "custom_types": [t["name"] for t in work_item_types if t.get("isCustomType", False)],
            "custom_fields": 0,  # Simplified - would need separate API call
        },
        "teams": {"count": len(teams)},
        "dependencies": {
            "service_connections": len(service_connections),
            "variable_groups": len(variable_groups),
        },
        "test_plans": {"count": len(test_plans)},
    }


@app.get("/api/scan/status")
async def get_scan_status():
    """Get current scan status."""
    return {
        "in_progress": state.scan_in_progress,
        **state.scan_progress,
    }


@app.get("/api/scan/results")
async def get_scan_results():
    """Get scan results."""
    if state.scan_results is None:
        raise HTTPException(status_code=404, detail="No scan results available")
    return state.scan_results


# ==================== Migration Endpoints ====================

@app.get("/api/repos")
async def list_repos():
    """List all repos from scan results."""
    if state.scan_results is None:
        raise HTTPException(status_code=404, detail="No scan results. Run scan first.")
    
    repos = []
    for project in state.scan_results["projects"]:
        for repo in project["repositories"]["items"]:
            repos.append({
                "project": project["name"],
                "name": repo["name"],
                "id": repo["id"],
                "size": repo.get("size", 0),
                "url": repo.get("url"),
            })
    return {"repos": repos}


@app.post("/api/migrate")
async def start_migration(request: MigrateRequest):
    """Start repository migration."""
    if state.migration_in_progress:
        raise HTTPException(status_code=409, detail="Migration already in progress")
    
    # Start migration in background
    asyncio.create_task(run_migration(request))
    
    return {"success": True, "message": f"Starting migration of {len(request.repos)} repos"}


async def run_migration(request: MigrateRequest):
    """Run migration in background using GEI."""
    state.migration_in_progress = True
    state.migration_progress = {
        "status": "starting",
        "repos": {repo: {"status": "pending", "progress": 0} for repo in request.repos},
    }
    
    try:
        config = get_config()
        
        for repo_name in request.repos:
            state.migration_progress["repos"][repo_name] = {
                "status": "in_progress",
                "progress": 0,
                "message": "Starting migration...",
            }
            await broadcast_progress({"type": "migration", **state.migration_progress})
            
            # Find repo details
            repo_info = None
            for project in state.scan_results["projects"]:
                for repo in project["repositories"]["items"]:
                    if repo["name"] == repo_name:
                        repo_info = {"project": project["name"], **repo}
                        break
            
            if not repo_info:
                state.migration_progress["repos"][repo_name] = {
                    "status": "failed",
                    "progress": 0,
                    "message": "Repo not found",
                }
                continue
            
            # Execute migration using subprocess (gh gei)
            success, message = await execute_gei_migration(
                ado_org=config.organization_url.split("/")[-1],
                ado_project=repo_info["project"],
                ado_repo=repo_name,
                github_org=request.target_org,
                github_repo=repo_name,
                visibility=request.visibility,
            )
            
            if success:
                state.migration_progress["repos"][repo_name] = {
                    "status": "completed",
                    "progress": 100,
                    "message": "Migration completed!",
                }
            else:
                state.migration_progress["repos"][repo_name] = {
                    "status": "failed",
                    "progress": 0,
                    "message": message[:100] if message else "Migration failed",
                }
            
            await broadcast_progress({"type": "migration", **state.migration_progress})
        
        state.migration_progress["status"] = "completed"
        await broadcast_progress({"type": "migration", **state.migration_progress})
        
    except Exception as e:
        state.migration_progress["status"] = "failed"
        state.migration_progress["error"] = str(e)
        await broadcast_progress({"type": "migration", **state.migration_progress})
    finally:
        state.migration_in_progress = False


async def execute_gei_migration(
    ado_org: str,
    ado_project: str,
    ado_repo: str,
    github_org: str,
    github_repo: str,
    visibility: str = "private",
) -> tuple[bool, str]:
    """Execute GEI migration command using gh ado2gh."""
    import os
    import subprocess
    import sys
    import yaml
    
    # Get ADO PAT from config
    config = get_config()
    
    # Get GitHub PAT from github config
    github_pat = None
    github_config_file = get_config_dir() / "github_config.yaml"
    if github_config_file.exists():
        with open(github_config_file) as f:
            gh_config = yaml.safe_load(f)
            github_pat = gh_config.get("token")
    
    if not github_pat:
        return False, "GitHub PAT not configured. Go to Configure page and add your GitHub token."
    
    # Set environment variables for GEI
    env = os.environ.copy()
    env["GH_PAT"] = github_pat
    
    # Build the ado2gh command (correct syntax)
    cmd = [
        "gh", "ado2gh", "migrate-repo",
        "--ado-org", ado_org,
        "--ado-team-project", ado_project,
        "--ado-repo", ado_repo,
        "--github-org", github_org,
        "--github-repo", github_repo,
        "--ado-pat", config.pat,
    ]
    
    # Add visibility if not private (default is private)
    if visibility and visibility != "private":
        cmd.extend(["--target-repo-visibility", visibility])
    
    print(f"Running: {' '.join(cmd[:6])}... (PAT hidden)")
    
    try:
        # Use subprocess.run in a thread for Windows compatibility
        import asyncio
        loop = asyncio.get_event_loop()
        
        def run_command():
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                shell=(sys.platform == "win32"),  # Use shell on Windows
            )
            return result
        
        result = await loop.run_in_executor(None, run_command)
        
        print(f"Migration stdout: {result.stdout[:500] if result.stdout else 'None'}")
        print(f"Migration stderr: {result.stderr[:500] if result.stderr else 'None'}")
        print(f"Return code: {result.returncode}")
        
        if result.returncode == 0:
            return True, "Success"
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            return False, error_msg[:200]
    except Exception as e:
        print(f"Migration exception: {e}")
        return False, str(e)



@app.get("/api/migrate/status")
async def get_migration_status():
    """Get migration status."""
    return {
        "in_progress": state.migration_in_progress,
        **state.migration_progress,
    }


# ==================== Helper ====================

def get_config_dir():
    from pathlib import Path
    config_dir = Path.home() / ".ado-readiness"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


# ==================== Health Check ====================

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.2.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
