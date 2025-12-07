from __future__ import annotations

import typer
from rich.console import Console

from ..client import PlaneAPIError, PlaneClient
from ..config import CONFIG_PATH, PlaneConfig, load_config

console = Console()
workspaces_app = typer.Typer()


def _client(config: PlaneConfig | None = None) -> PlaneClient:
    cfg = config or load_config()
    if not cfg:
        raise typer.BadParameter(f"No config found. Run `plane auth` to populate {CONFIG_PATH}.")
    return PlaneClient(cfg)


@workspaces_app.command("list")
def list_workspaces() -> None:
    """List workspaces available to the PAT."""
    client = _client()
    try:
        workspaces = client.list_workspaces()
    except PlaneAPIError as exc:
        raise typer.BadParameter(str(exc)) from exc
    rows = [ws.model_dump() for ws in workspaces]
    console.print(rows)
