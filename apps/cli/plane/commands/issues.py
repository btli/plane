from __future__ import annotations

import typer
from rich.console import Console

from ..client import PlaneAPIError, PlaneClient
from ..config import CONFIG_PATH, PlaneConfig, load_config
from ..types import IssueCreate

console = Console()
issues_app = typer.Typer()


def _client(config: PlaneConfig | None = None) -> PlaneClient:
    cfg = config or load_config()
    if not cfg:
        raise typer.BadParameter(f"No config found. Run `plane auth` to populate {CONFIG_PATH}.")
    return PlaneClient(cfg)


@issues_app.command("list")
def list_issues(
    workspace: str = typer.Option(..., "--workspace", "-w", help="Workspace slug"),
    project: str = typer.Option(..., "--project", "-p", help="Project UUID"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of results"),
) -> None:
    """List work items in a project."""
    client = _client()
    try:
        issues = client.list_issues(workspace=workspace, project_id=project, limit=limit)
    except PlaneAPIError as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print([issue.model_dump() for issue in issues])


@issues_app.command("create")
def create_issue(
    workspace: str = typer.Option(..., "--workspace", "-w", help="Workspace slug"),
    project: str = typer.Option(..., "--project", "-p", help="Project UUID"),
    title: str = typer.Option(..., "--title", "-t", help="Issue title"),
    description: str | None = typer.Option(None, "--description", "-d", help="Issue description"),
) -> None:
    """Create a new work item."""
    client = _client()
    payload = IssueCreate(name=title, description=description)
    try:
        issue = client.create_issue(workspace=workspace, project_id=project, payload=payload)
    except PlaneAPIError as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print(issue.model_dump())
