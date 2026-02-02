"""Organization scanner for migration assessment."""

from dataclasses import dataclass, field
from typing import Any, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel

from ado_readiness.ado_client import ADOClient
from ado_readiness.config import get_config_dir


@dataclass
class ProjectScanResult:
    """Scan results for a single project."""
    name: str
    repositories: list[dict[str, Any]] = field(default_factory=list)
    tfvc_used: bool = False
    pipelines: list[dict[str, Any]] = field(default_factory=list)
    build_definitions: list[dict[str, Any]] = field(default_factory=list)
    release_definitions: list[dict[str, Any]] = field(default_factory=list)
    work_item_counts: dict[str, int] = field(default_factory=dict)
    work_item_types: list[dict[str, Any]] = field(default_factory=list)
    custom_fields: list[dict[str, Any]] = field(default_factory=list)
    teams: list[dict[str, Any]] = field(default_factory=list)
    service_connections: list[dict[str, Any]] = field(default_factory=list)
    variable_groups: list[dict[str, Any]] = field(default_factory=list)
    test_plans: list[dict[str, Any]] = field(default_factory=list)


class OrganizationScanner:
    """Scanner for Azure DevOps organization assessment."""
    
    def __init__(self, client: ADOClient, console: Console, verbose: bool = False) -> None:
        self.client = client
        self.console = console
        self.verbose = verbose
    
    def scan(self, project_filter: Optional[str] = None) -> dict[str, Any]:
        """Scan the organization and return assessment results."""
        results: dict[str, Any] = {
            "organization_url": self.client.organization_url,
            "projects": [],
            "summary": {},
        }
        
        # Get projects to scan
        if project_filter:
            projects = [{"name": project_filter}]
        else:
            projects = self.client.get_projects()
        
        self.console.print(f"\n[cyan]Found {len(projects)} project(s) to scan[/cyan]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Scanning projects...", total=len(projects))
            
            for proj in projects:
                project_name = proj["name"]
                progress.update(task, description=f"Scanning {project_name}...")
                
                project_result = self._scan_project(project_name)
                results["projects"].append(self._result_to_dict(project_result))
                
                progress.advance(task)
        
        # Calculate summary
        results["summary"] = self._calculate_summary(results["projects"])
        
        # Cache results
        self._save_cache(results)
        
        return results
    
    def _scan_project(self, project_name: str) -> ProjectScanResult:
        """Scan a single project."""
        result = ProjectScanResult(name=project_name)
        
        if self.verbose:
            self.console.print(f"  [dim]Scanning {project_name}...[/dim]")
        
        # Repositories
        result.repositories = self.client.get_repositories(project_name)
        result.tfvc_used = self.client.check_tfvc(project_name)
        
        # Pipelines
        result.pipelines = self.client.get_pipelines(project_name)
        result.build_definitions = self.client.get_build_definitions(project_name)
        result.release_definitions = self.client.get_release_definitions(project_name)
        
        # Work Items
        result.work_item_types = self.client.get_work_item_types(project_name)
        result.work_item_counts = self.client.get_work_item_counts_by_type(project_name)
        result.custom_fields = self.client.get_custom_fields(project_name)
        
        # Teams and Boards
        result.teams = self.client.get_teams(project_name)
        
        # Dependencies
        result.service_connections = self.client.get_service_connections(project_name)
        result.variable_groups = self.client.get_variable_groups(project_name)
        
        # Test Plans
        result.test_plans = self.client.get_test_plans(project_name)
        
        return result
    
    def _result_to_dict(self, result: ProjectScanResult) -> dict[str, Any]:
        """Convert ProjectScanResult to dictionary."""
        return {
            "name": result.name,
            "repositories": {
                "count": len(result.repositories),
                "tfvc_used": result.tfvc_used,
                "items": [{"name": r.get("name"), "size": r.get("size", 0)} for r in result.repositories],
            },
            "pipelines": {
                "yaml_count": len(result.pipelines),
                "build_definitions": len(result.build_definitions),
                "release_definitions": len(result.release_definitions),
                "classic_count": len([d for d in result.build_definitions if d.get("type") == "build"]),
            },
            "work_items": {
                "total": sum(result.work_item_counts.values()),
                "by_type": result.work_item_counts,
                "custom_types": [t["name"] for t in result.work_item_types if t.get("isCustomType", False)],
                "custom_fields": len(result.custom_fields),
            },
            "teams": {
                "count": len(result.teams),
            },
            "dependencies": {
                "service_connections": len(result.service_connections),
                "variable_groups": len(result.variable_groups),
            },
            "test_plans": {
                "count": len(result.test_plans),
            },
        }
    
    def _calculate_summary(self, projects: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate overall summary and complexity scores."""
        summary = {
            "total_projects": len(projects),
            "total_repositories": sum(p["repositories"]["count"] for p in projects),
            "tfvc_projects": sum(1 for p in projects if p["repositories"]["tfvc_used"]),
            "total_pipelines": sum(p["pipelines"]["yaml_count"] + p["pipelines"]["release_definitions"] for p in projects),
            "classic_pipelines": sum(p["pipelines"]["release_definitions"] for p in projects),
            "total_work_items": sum(p["work_items"]["total"] for p in projects),
            "total_test_plans": sum(p["test_plans"]["count"] for p in projects),
            "total_service_connections": sum(p["dependencies"]["service_connections"] for p in projects),
            "complexity": {},
            "blockers": [],
        }
        
        # Calculate complexity scores
        summary["complexity"] = {
            "repositories": self._score_repos(summary),
            "pipelines": self._score_pipelines(summary),
            "work_items": self._score_work_items(summary, projects),
            "overall": 0,
        }
        
        # Calculate overall score
        scores = [
            summary["complexity"]["repositories"]["score"],
            summary["complexity"]["pipelines"]["score"],
            summary["complexity"]["work_items"]["score"],
        ]
        summary["complexity"]["overall"] = sum(scores) // len(scores)
        summary["complexity"]["rating"] = self._score_to_rating(summary["complexity"]["overall"])
        
        # Identify blockers
        if summary["tfvc_projects"] > 0:
            summary["blockers"].append(f"{summary['tfvc_projects']} project(s) use TFVC - requires special handling")
        
        if summary["classic_pipelines"] > 0:
            summary["blockers"].append(f"{summary['classic_pipelines']} Classic release pipeline(s) need manual conversion")
        
        custom_types = set()
        for p in projects:
            custom_types.update(p["work_items"]["custom_types"])
        if custom_types:
            summary["blockers"].append(f"{len(custom_types)} custom work item type(s) need mapping")
        
        return summary
    
    def _score_repos(self, summary: dict[str, Any]) -> dict[str, Any]:
        """Score repository migration complexity."""
        score = 20  # Base score (low complexity)
        
        if summary["tfvc_projects"] > 0:
            score += 40  # TFVC adds significant complexity
        
        if summary["total_repositories"] > 50:
            score += 20
        elif summary["total_repositories"] > 20:
            score += 10
        
        return {
            "score": min(score, 100),
            "rating": self._score_to_rating(score),
            "effort": self._estimate_effort(score, "repos"),
        }
    
    def _score_pipelines(self, summary: dict[str, Any]) -> dict[str, Any]:
        """Score pipeline migration complexity."""
        score = 30  # Base score
        
        # Classic pipelines are harder to migrate
        if summary["classic_pipelines"] > 0:
            classic_ratio = summary["classic_pipelines"] / max(summary["total_pipelines"], 1)
            score += int(classic_ratio * 50)
        
        if summary["total_pipelines"] > 100:
            score += 20
        elif summary["total_pipelines"] > 50:
            score += 10
        
        return {
            "score": min(score, 100),
            "rating": self._score_to_rating(score),
            "effort": self._estimate_effort(score, "pipelines"),
        }
    
    def _score_work_items(self, summary: dict[str, Any], projects: list[dict[str, Any]]) -> dict[str, Any]:
        """Score work items migration complexity."""
        score = 25  # Base score
        
        # Custom fields add complexity
        total_custom_fields = sum(p["work_items"]["custom_fields"] for p in projects)
        if total_custom_fields > 20:
            score += 30
        elif total_custom_fields > 10:
            score += 15
        
        # Large number of work items
        if summary["total_work_items"] > 10000:
            score += 25
        elif summary["total_work_items"] > 5000:
            score += 15
        elif summary["total_work_items"] > 1000:
            score += 5
        
        return {
            "score": min(score, 100),
            "rating": self._score_to_rating(score),
            "effort": self._estimate_effort(score, "work_items"),
        }
    
    def _score_to_rating(self, score: int) -> str:
        """Convert numeric score to rating."""
        if score < 35:
            return "Low"
        elif score < 65:
            return "Medium"
        else:
            return "High"
    
    def _estimate_effort(self, score: int, category: str) -> str:
        """Estimate effort based on score and category."""
        if score < 35:
            return "1-2 days"
        elif score < 65:
            return "1-2 weeks"
        else:
            return "2+ weeks"
    
    def _save_cache(self, results: dict[str, Any]) -> None:
        """Save results to cache for report generation."""
        import json
        cache_file = get_config_dir() / "last_scan.json"
        with open(cache_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
    
    def display_summary(self, results: dict[str, Any]) -> None:
        """Display scan summary to console."""
        summary = results["summary"]
        
        self.console.print()
        self.console.print(Panel.fit(
            f"[bold cyan]Scan Complete![/bold cyan]\n"
            f"Organization: [dim]{results['organization_url']}[/dim]",
            border_style="green",
        ))
        
        # Summary table
        table = Table(title="📊 Asset Summary", show_header=True, header_style="bold cyan")
        table.add_column("Asset Type", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("Complexity", justify="center")
        table.add_column("Est. Effort", justify="right")
        
        table.add_row(
            "Repositories",
            str(summary["total_repositories"]),
            self._color_rating(summary["complexity"]["repositories"]["rating"]),
            summary["complexity"]["repositories"]["effort"],
        )
        table.add_row(
            "Pipelines",
            str(summary["total_pipelines"]),
            self._color_rating(summary["complexity"]["pipelines"]["rating"]),
            summary["complexity"]["pipelines"]["effort"],
        )
        table.add_row(
            "Work Items",
            str(summary["total_work_items"]),
            self._color_rating(summary["complexity"]["work_items"]["rating"]),
            summary["complexity"]["work_items"]["effort"],
        )
        table.add_row(
            "Test Plans",
            str(summary["total_test_plans"]),
            "[yellow]N/A[/yellow]",
            "Manual",
        )
        
        self.console.print(table)
        
        # Overall score
        overall = summary["complexity"]["overall"]
        rating = summary["complexity"]["rating"]
        color = self._rating_color(rating)
        
        self.console.print()
        self.console.print(f"[bold]Overall Migration Complexity:[/bold] [{color}]{rating} ({overall}/100)[/{color}]")
        
        # Blockers
        if summary["blockers"]:
            self.console.print()
            self.console.print("[bold red]⚠️  Blockers Found:[/bold red]")
            for blocker in summary["blockers"]:
                self.console.print(f"  • {blocker}")
        
        self.console.print()
        self.console.print("[dim]Run 'ado-readiness report --format html -o report.html' for detailed report[/dim]")
    
    def _color_rating(self, rating: str) -> str:
        """Color-code a rating."""
        color = self._rating_color(rating)
        return f"[{color}]{rating}[/{color}]"
    
    def _rating_color(self, rating: str) -> str:
        """Get color for rating."""
        if rating == "Low":
            return "green"
        elif rating == "Medium":
            return "yellow"
        else:
            return "red"
