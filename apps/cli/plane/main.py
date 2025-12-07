from __future__ import annotations

import typer
from rich.console import Console

from .auth import auth_flow
from .client import PlaneAPIError, PlaneClient
from .config import CONFIG_PATH, load_config
from .commands.issues import issues_app
from .commands.projects import projects_app
from .commands.workspaces import workspaces_app

console = Console()
app = typer.Typer(help="Plane CLI for the v1 API")


def _ensure_config() -> PlaneClient:
    config = load_config()
    if not config:
        raise typer.BadParameter(
            f"No config found. Run `plane auth` first to populate {CONFIG_PATH}."
        )
    return PlaneClient(config)


@app.command()
def auth(
    host: str = typer.Option("app.plane.so", "--host", "-h", help="Plane host, e.g., app.plane.so"),
    token: str | None = typer.Option(None, "--token", help="Existing PAT to save"),
    email: str | None = typer.Option(None, "--email", help="Email for credential auth"),
    password: str | None = typer.Option(None, "--password", help="Password for credential auth"),
    browser: bool = typer.Option(
        True,
        "--browser/--no-browser",
        help="Use browser-based PAT issuance (default) or credential flow.",
    ),
) -> None:
    """Authenticate and store a PAT in ~/.plane/config.yaml."""
    auth_flow(host=host, use_browser=browser, email=email, password=password, token=token)


@app.command()
def whoami() -> None:
    """Show the current authenticated user."""
    client = _ensure_config()
    try:
        user = client.whoami()
    except PlaneAPIError as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print(user.model_dump())


app.add_typer(workspaces_app, name="workspaces", help="Workspace level commands")
app.add_typer(projects_app, name="projects", help="Project level commands")
app.add_typer(issues_app, name="issues", help="Work item commands")


if __name__ == "__main__":
    app()
