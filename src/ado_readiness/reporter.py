"""Report generator for migration assessment."""

from datetime import datetime
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel


class ReportGenerator:
    """Generate migration readiness reports in various formats."""
    
    def __init__(self, console: Console) -> None:
        self.console = console
    
    def print_report(self, results: dict[str, Any]) -> None:
        """Print detailed report to console."""
        summary = results["summary"]
        
        # Header
        self.console.print()
        self.console.print(Panel.fit(
            "[bold cyan]ADO Migration Readiness Report[/bold cyan]\n"
            f"Organization: [dim]{results['organization_url']}[/dim]\n"
            f"Generated: [dim]{datetime.now().strftime('%Y-%m-%d %H:%M')}[/dim]",
            border_style="cyan",
        ))
        
        # Summary table
        self._print_summary_table(summary)
        
        # Project details
        self._print_project_details(results["projects"])
        
        # Complexity breakdown
        self._print_complexity_breakdown(summary)
        
        # Blockers and recommendations
        self._print_blockers(summary)
        self._print_recommendations(summary)
    
    def _print_summary_table(self, summary: dict[str, Any]) -> None:
        """Print summary table."""
        self.console.print()
        table = Table(title="📊 Summary", show_header=True, header_style="bold cyan")
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
            "Manual review",
        )
        
        self.console.print(table)
        
        # Overall
        overall = summary["complexity"]["overall"]
        rating = summary["complexity"]["rating"]
        color = self._rating_color(rating)
        self.console.print()
        self.console.print(f"[bold]Overall Migration Complexity:[/bold] [{color}]{rating} ({overall}/100)[/{color}]")
    
    def _print_project_details(self, projects: list[dict[str, Any]]) -> None:
        """Print details for each project."""
        self.console.print()
        table = Table(title="📁 Projects", show_header=True, header_style="bold cyan")
        table.add_column("Project", style="cyan")
        table.add_column("Repos", justify="right")
        table.add_column("Pipelines", justify="right")
        table.add_column("Work Items", justify="right")
        table.add_column("Notes", style="dim")
        
        for proj in projects:
            notes = []
            if proj["repositories"]["tfvc_used"]:
                notes.append("TFVC")
            if proj["pipelines"]["release_definitions"] > 0:
                notes.append(f"{proj['pipelines']['release_definitions']} Classic")
            if proj["work_items"]["custom_types"]:
                notes.append(f"{len(proj['work_items']['custom_types'])} custom types")
            
            table.add_row(
                proj["name"],
                str(proj["repositories"]["count"]),
                str(proj["pipelines"]["yaml_count"] + proj["pipelines"]["release_definitions"]),
                str(proj["work_items"]["total"]),
                ", ".join(notes) if notes else "-",
            )
        
        self.console.print(table)
    
    def _print_complexity_breakdown(self, summary: dict[str, Any]) -> None:
        """Print complexity breakdown."""
        self.console.print()
        self.console.print("[bold]📈 Complexity Breakdown:[/bold]")
        
        for category in ["repositories", "pipelines", "work_items"]:
            data = summary["complexity"][category]
            color = self._rating_color(data["rating"])
            bar = self._progress_bar(data["score"])
            self.console.print(f"  {category.replace('_', ' ').title():15} [{color}]{bar}[/{color}] {data['score']}/100")
    
    def _print_blockers(self, summary: dict[str, Any]) -> None:
        """Print blockers."""
        if not summary["blockers"]:
            self.console.print()
            self.console.print("[green]✅ No major blockers identified![/green]")
            return
        
        self.console.print()
        self.console.print("[bold red]⚠️  Migration Blockers:[/bold red]")
        for blocker in summary["blockers"]:
            self.console.print(f"  • {blocker}")
    
    def _print_recommendations(self, summary: dict[str, Any]) -> None:
        """Print recommendations."""
        self.console.print()
        self.console.print("[bold]💡 Recommendations:[/bold]")
        
        recommendations = [
            "1. Start with repositories - they have the lowest complexity",
            "2. Use GitHub Enterprise Importer (GEI) for repo migration",
            "3. Convert Classic pipelines to YAML before migrating",
            "4. Plan work item migration separately - consider GitHub Issues or Projects",
            "5. Review service connections and variable groups for secrets handling",
        ]
        
        if summary["tfvc_projects"] > 0:
            recommendations.insert(1, "⚠️  Plan TFVC to Git conversion as a separate phase")
        
        if summary["total_test_plans"] > 0:
            recommendations.append("6. Test Plans don't migrate - evaluate GitHub Actions for testing")
        
        for rec in recommendations:
            self.console.print(f"  {rec}")
    
    def generate_html(self, results: dict[str, Any], output_path: str) -> None:
        """Generate HTML report."""
        summary = results["summary"]
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ADO Migration Readiness Report</title>
    <style>
        :root {{
            --bg-color: #1a1a2e;
            --card-bg: #16213e;
            --text-color: #eee;
            --accent-color: #0f4c75;
            --success: #00d26a;
            --warning: #ffb830;
            --danger: #ff6b6b;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            padding: 2rem;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #3498db; margin-bottom: 0.5rem; }}
        h2 {{ color: #3498db; margin: 2rem 0 1rem; border-bottom: 2px solid var(--accent-color); padding-bottom: 0.5rem; }}
        .subtitle {{ color: #888; margin-bottom: 2rem; }}
        .card {{
            background: var(--card-bg);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }}
        .score-card {{
            text-align: center;
            padding: 2rem;
        }}
        .score {{ font-size: 4rem; font-weight: bold; }}
        .score.low {{ color: var(--success); }}
        .score.medium {{ color: var(--warning); }}
        .score.high {{ color: var(--danger); }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid #333; }}
        th {{ color: #3498db; font-weight: 600; }}
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 500;
        }}
        .badge.low {{ background: var(--success); color: #000; }}
        .badge.medium {{ background: var(--warning); color: #000; }}
        .badge.high {{ background: var(--danger); color: #fff; }}
        .progress-bar {{
            background: #333;
            border-radius: 4px;
            height: 8px;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }}
        .blocker {{ 
            background: rgba(255,107,107,0.1); 
            border-left: 4px solid var(--danger);
            padding: 1rem;
            margin: 0.5rem 0;
        }}
        .recommendation {{
            background: rgba(52,152,219,0.1);
            border-left: 4px solid #3498db;
            padding: 1rem;
            margin: 0.5rem 0;
        }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }}
        .stat {{ text-align: center; }}
        .stat-value {{ font-size: 2rem; font-weight: bold; color: #3498db; }}
        .stat-label {{ color: #888; font-size: 0.875rem; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 ADO Migration Readiness Report</h1>
        <p class="subtitle">
            Organization: {results['organization_url']}<br>
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </p>
        
        <div class="card score-card">
            <div class="score {summary['complexity']['rating'].lower()}">{summary['complexity']['overall']}/100</div>
            <div>Overall Complexity: <span class="badge {summary['complexity']['rating'].lower()}">{summary['complexity']['rating']}</span></div>
        </div>
        
        <h2>📊 Summary</h2>
        <div class="grid">
            <div class="card stat">
                <div class="stat-value">{summary['total_projects']}</div>
                <div class="stat-label">Projects</div>
            </div>
            <div class="card stat">
                <div class="stat-value">{summary['total_repositories']}</div>
                <div class="stat-label">Repositories</div>
            </div>
            <div class="card stat">
                <div class="stat-value">{summary['total_pipelines']}</div>
                <div class="stat-label">Pipelines</div>
            </div>
            <div class="card stat">
                <div class="stat-value">{summary['total_work_items']:,}</div>
                <div class="stat-label">Work Items</div>
            </div>
        </div>
        
        <h2>📈 Complexity Breakdown</h2>
        <div class="card">
            <table>
                <tr>
                    <th>Category</th>
                    <th>Count</th>
                    <th>Complexity</th>
                    <th>Score</th>
                    <th>Est. Effort</th>
                </tr>
                <tr>
                    <td>Repositories</td>
                    <td>{summary['total_repositories']}</td>
                    <td><span class="badge {summary['complexity']['repositories']['rating'].lower()}">{summary['complexity']['repositories']['rating']}</span></td>
                    <td>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {summary['complexity']['repositories']['score']}%; background: {self._score_color(summary['complexity']['repositories']['score'])};"></div>
                        </div>
                    </td>
                    <td>{summary['complexity']['repositories']['effort']}</td>
                </tr>
                <tr>
                    <td>Pipelines</td>
                    <td>{summary['total_pipelines']}</td>
                    <td><span class="badge {summary['complexity']['pipelines']['rating'].lower()}">{summary['complexity']['pipelines']['rating']}</span></td>
                    <td>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {summary['complexity']['pipelines']['score']}%; background: {self._score_color(summary['complexity']['pipelines']['score'])};"></div>
                        </div>
                    </td>
                    <td>{summary['complexity']['pipelines']['effort']}</td>
                </tr>
                <tr>
                    <td>Work Items</td>
                    <td>{summary['total_work_items']:,}</td>
                    <td><span class="badge {summary['complexity']['work_items']['rating'].lower()}">{summary['complexity']['work_items']['rating']}</span></td>
                    <td>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {summary['complexity']['work_items']['score']}%; background: {self._score_color(summary['complexity']['work_items']['score'])};"></div>
                        </div>
                    </td>
                    <td>{summary['complexity']['work_items']['effort']}</td>
                </tr>
            </table>
        </div>
        
        <h2>📁 Projects</h2>
        <div class="card">
            <table>
                <tr>
                    <th>Project</th>
                    <th>Repos</th>
                    <th>Pipelines</th>
                    <th>Work Items</th>
                    <th>Notes</th>
                </tr>
                {''.join(self._project_row(p) for p in results['projects'])}
            </table>
        </div>
        
        {self._blockers_html(summary)}
        
        <h2>💡 Recommendations</h2>
        <div class="card">
            <div class="recommendation">Start with repositories - they typically have the lowest complexity</div>
            <div class="recommendation">Use GitHub Enterprise Importer (GEI) for repository migration</div>
            <div class="recommendation">Convert Classic pipelines to YAML before migrating</div>
            <div class="recommendation">Plan work item migration separately - consider GitHub Issues or Projects</div>
            <div class="recommendation">Review service connections and variable groups for secrets handling</div>
        </div>
        
        <p style="text-align: center; margin-top: 3rem; color: #666;">
            Generated by <strong>ADO Migration Readiness Analyzer</strong><br>
            <a href="https://github.com/nkusakula/ADO-to-GitHub-Pre-migration-assessment-tool" style="color: #3498db;">GitHub Repository</a>
        </p>
    </div>
</body>
</html>"""
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
    
    def _project_row(self, proj: dict[str, Any]) -> str:
        """Generate HTML table row for a project."""
        notes = []
        if proj["repositories"]["tfvc_used"]:
            notes.append("⚠️ TFVC")
        if proj["pipelines"]["release_definitions"] > 0:
            notes.append(f"{proj['pipelines']['release_definitions']} Classic")
        if proj["work_items"]["custom_types"]:
            notes.append(f"{len(proj['work_items']['custom_types'])} custom types")
        
        return f"""<tr>
            <td>{proj['name']}</td>
            <td>{proj['repositories']['count']}</td>
            <td>{proj['pipelines']['yaml_count'] + proj['pipelines']['release_definitions']}</td>
            <td>{proj['work_items']['total']:,}</td>
            <td>{', '.join(notes) if notes else '-'}</td>
        </tr>"""
    
    def _blockers_html(self, summary: dict[str, Any]) -> str:
        """Generate blockers HTML section."""
        if not summary["blockers"]:
            return """<h2>✅ No Blockers</h2>
            <div class="card" style="background: rgba(0,210,106,0.1); border-left: 4px solid var(--success);">
                No major migration blockers identified!
            </div>"""
        
        blockers_html = "\n".join(f'<div class="blocker">⚠️ {b}</div>' for b in summary["blockers"])
        return f"""<h2>⚠️ Migration Blockers</h2>
        <div class="card">
            {blockers_html}
        </div>"""
    
    def _score_color(self, score: int) -> str:
        """Get color for score."""
        if score < 35:
            return "#00d26a"
        elif score < 65:
            return "#ffb830"
        else:
            return "#ff6b6b"
    
    def _color_rating(self, rating: str) -> str:
        """Color-code a rating for console."""
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
    
    def _progress_bar(self, score: int, width: int = 20) -> str:
        """Generate a text progress bar."""
        filled = int(score / 100 * width)
        empty = width - filled
        return "█" * filled + "░" * empty
