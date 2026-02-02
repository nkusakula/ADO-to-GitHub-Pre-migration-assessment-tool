"""CLI entry point for ADO Readiness Analyzer."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(
    name="ado-readiness",
    help="Azure DevOps Migration Readiness Analyzer - Assess your ADO org before migrating to GitHub",
    add_completion=False,
)
console = Console()


@app.command()
def configure(
    organization_url: str = typer.Option(
        None,
        "--org", "-o",
        prompt="Azure DevOps Organization URL (e.g., https://dev.azure.com/myorg)",
        help="Azure DevOps organization URL",
    ),
    pat: str = typer.Option(
        None,
        "--pat", "-p",
        prompt="Personal Access Token",
        hide_input=True,
        help="Azure DevOps PAT with read permissions",
    ),
) -> None:
    """Configure Azure DevOps connection settings."""
    from ado_readiness.config import ADOConfig, save_config
    
    # Validate URL format
    if not organization_url.startswith("http"):
        organization_url = f"https://dev.azure.com/{organization_url}"
    
    config = ADOConfig(organization_url=organization_url, pat=pat)
    save_config(config)
    
    console.print(f"[green]✅ Configuration saved![/green]")
    console.print(f"[dim]Organization: {organization_url}[/dim]")
    console.print("\n[cyan]Next step: Run 'ado-readiness test-connection' to verify.[/cyan]")


@app.command()
def test_connection() -> None:
    """Test connectivity to Azure DevOps."""
    from ado_readiness.config import get_config, config_exists
    from ado_readiness.ado_client import ADOClient
    
    if not config_exists():
        console.print("[red]❌ Not configured. Run 'ado-readiness configure' first.[/red]")
        raise typer.Exit(1)
    
    config = get_config()
    console.print(f"[cyan]Testing connection to {config.organization_url}...[/cyan]")
    
    try:
        client = ADOClient(config.organization_url, config.pat)
        projects = client.get_projects()
        
        console.print(f"[green]✅ Connected successfully![/green]")
        console.print(f"[green]   Found {len(projects)} projects[/green]")
        
        if projects:
            table = Table(title="Available Projects", show_header=True)
            table.add_column("Name", style="cyan")
            table.add_column("Description", style="dim")
            
            for proj in projects[:10]:
                table.add_row(proj.get("name", ""), (proj.get("description") or "")[:50])
            
            console.print(table)
            
            if len(projects) > 10:
                console.print(f"[dim]... and {len(projects) - 10} more projects[/dim]")
        
        client.close()
                
    except Exception as e:
        console.print(f"[red]❌ Connection failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def scan(
    project: str = typer.Option(
        None, "--project", "-p",
        help="Scan a specific project (default: all projects)",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="Show detailed output during scan",
    ),
    output: str = typer.Option(
        None, "--output", "-o",
        help="Save scan results to JSON file",
    ),
) -> None:
    """Scan Azure DevOps organization for migration assessment."""
    from ado_readiness.config import get_config, config_exists
    from ado_readiness.ado_client import ADOClient
    from ado_readiness.scanner import OrganizationScanner
    
    if not config_exists():
        console.print("[red]❌ Not configured. Run 'ado-readiness configure' first.[/red]")
        raise typer.Exit(1)
    
    config = get_config()
    
    console.print(Panel.fit(
        f"[bold cyan]Scanning Azure DevOps Organization[/bold cyan]\n"
        f"[dim]{config.organization_url}[/dim]",
        border_style="cyan",
    ))
    
    try:
        client = ADOClient(config.organization_url, config.pat)
        scanner = OrganizationScanner(client, console, verbose)
        
        results = scanner.scan(project_filter=project)
        
        # Display summary
        scanner.display_summary(results)
        
        # Save to file if requested
        if output:
            import json
            with open(output, "w") as f:
                json.dump(results, f, indent=2, default=str)
            console.print(f"\n[green]✅ Results saved to {output}[/green]")
        
        client.close()
        
    except Exception as e:
        console.print(f"[red]❌ Scan failed: {e}[/red]")
        if verbose:
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)


@app.command()
def report(
    format: str = typer.Option(
        "console", "--format", "-f",
        help="Output format: console, html, json",
    ),
    output: str = typer.Option(
        None, "--output", "-o",
        help="Output file path (required for html/json)",
    ),
    scan_file: str = typer.Option(
        None, "--scan-file", "-s",
        help="Use existing scan results JSON file",
    ),
) -> None:
    """Generate migration readiness report."""
    from ado_readiness.reporter import ReportGenerator
    
    if format in ["html", "json"] and not output:
        console.print(f"[red]❌ --output is required for {format} format[/red]")
        raise typer.Exit(1)
    
    # Load scan results
    if scan_file:
        import json
        with open(scan_file) as f:
            results = json.load(f)
    else:
        # Check for cached results
        from ado_readiness.config import get_config_dir
        cache_file = get_config_dir() / "last_scan.json"
        
        if not cache_file.exists():
            console.print("[red]❌ No scan results found. Run 'ado-readiness scan' first.[/red]")
            raise typer.Exit(1)
        
        import json
        with open(cache_file) as f:
            results = json.load(f)
    
    generator = ReportGenerator(console)
    
    if format == "console":
        generator.print_report(results)
    elif format == "html":
        generator.generate_html(results, output)
        console.print(f"[green]✅ Report saved to {output}[/green]")
    elif format == "json":
        import json
        with open(output, "w") as f:
            json.dump(results, f, indent=2)
        console.print(f"[green]✅ Report saved to {output}[/green]")


@app.command()
def version() -> None:
    """Show version information."""
    console.print(Panel.fit(
        "[bold cyan]ADO Migration Readiness Analyzer[/bold cyan]\n"
        "Version: 0.1.0\n"
        "GitHub: https://github.com/nkusakula/ADO-to-GitHub-Pre-migration-assessment-tool",
        title="ado-readiness",
    ))


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Azure DevOps Migration Readiness Analyzer."""
    if ctx.invoked_subcommand is None:
        console.print(Panel.fit(
            "[bold cyan]ADO Migration Readiness Analyzer[/bold cyan] 🔍\n\n"
            "Analyze your Azure DevOps organization before migrating to GitHub.\n\n"
            "[bold]Quick Start:[/bold]\n"
            "  1. [cyan]ado-readiness configure[/cyan]      - Set up your ADO connection\n"
            "  2. [cyan]ado-readiness test-connection[/cyan] - Verify connectivity\n"
            "  3. [cyan]ado-readiness scan[/cyan]           - Analyze your organization\n"
            "  4. [cyan]ado-readiness report[/cyan]         - Generate readiness report\n\n"
            "[dim]Use --help on any command for more information[/dim]",
            title="Welcome",
            border_style="cyan",
        ))


if __name__ == "__main__":
    app()
