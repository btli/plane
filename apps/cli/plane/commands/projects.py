from __future__ import annotations

import typer
from rich.console import Console

from ..client import PlaneAPIError, PlaneClient
from ..config import CONFIG_PATH, PlaneConfig, load_config

console = Console()
projects_app = typer.Typer()


def _client(config: PlaneConfig | None = None) -> PlaneClient:
    cfg = config or load_config()
    if not cfg:
        raise typer.BadParameter(f"No config found. Run `plane auth` to populate {CONFIG_PATH}.")
    return PlaneClient(cfg)


@projects_app.command("list")
def list_projects(
    workspace: str = typer.Option(..., "--workspace", "-w", help="Workspace slug"),
    order_by: str = typer.Option("-created_at", "--order-by", help="Ordering, default -created_at"),
) -> None:
    """List projects in a workspace."""
    client = _client()
    try:
        projects = client.list_projects(workspace, order_by)
    except PlaneAPIError as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print([proj.model_dump() for proj in projects])
