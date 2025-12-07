# Plane CLI

This CLI targets the v1 API and is packaged with `uv` for reproducible installs.

## Install and run

```bash
# Run without installing
uv run --project apps/cli plane --help

# Install as a tool (optional)
uv tool install --python 3.11 --script plane --editable ./apps/cli
```

## Authenticate

```bash
uv run --project apps/cli plane auth
```

The CLI starts a local callback server and opens `<host>/cli/connect`, which issues a PAT and posts it back to the CLI. Credentials are stored at `$HOME/.plane/config.yaml`:

```yaml
host: app.plane.so
token: "<personal access token>"
```

Credential-based auth is also available:

```bash
uv run --project apps/cli plane auth --no-browser --email user@example.com
```

## Common commands

- `plane whoami` – Display the current user.
- `plane workspaces list` – List workspaces accessible to the PAT.
- `plane projects list --workspace <slug>` – Show projects.
- `plane issues list --workspace <slug> --project <project_id>` – List work items.
- `plane issues create --workspace <slug> --project <project_id> --title "..." --description "..."` – Create a work item.

## Development

```bash
uv run --project apps/cli ruff check
uv run --project apps/cli ruff format
uv run --project apps/cli --extra dev ty check apps/cli/plane

### Build a standalone executable

```bash
uv run --project apps/cli --extra dev pyinstaller --onefile --name plane --distpath dist apps/cli/plane/main.py
```
```
