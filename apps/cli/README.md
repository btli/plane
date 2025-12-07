# Plane CLI (v1)

The Plane CLI provides typed, authenticated access to the Plane v1 API. It is built with `uv`, `typer`, and `httpx`.

## Quick start

```bash
uv run --project apps/cli plane --help
uv run --project apps/cli plane auth
```

The CLI stores credentials in `$HOME/.plane/config.yaml` (host + PAT).

## Commands

- `plane auth` – Authenticate via browser (default), or `--no-browser` for email/password. Stores the PAT.
- `plane whoami` – Show the current user.
- `plane workspaces list` – List workspaces you can access.
- `plane projects list --workspace <slug>` – List projects within a workspace.
- `plane issues list --workspace <slug> --project <uuid>` – List work items in a project.
- `plane issues create --workspace <slug> --project <uuid> --title "..." [--description "..."]` – Create a work item.

## Development

Install tooling with `uv`:

```bash
uv run --project apps/cli ruff check
uv run --project apps/cli ruff format
uv run --project apps/cli --extra dev ty check apps/cli/plane

### Build a standalone executable

```bash
uv run --project apps/cli --extra dev pyinstaller --onefile --name plane --distpath dist apps/cli/plane/main.py
# binary will be at dist/plane
```
```
