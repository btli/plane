from __future__ import annotations

import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional
from urllib.parse import parse_qs, urlparse

import httpx
import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt

from .config import CONFIG_PATH, PlaneConfig, save_config

console = Console()


def normalize_host(host: str) -> str:
    cleaned = host.strip().rstrip("/")
    if cleaned.startswith("http://") or cleaned.startswith("https://"):
        return cleaned
    return cleaned


class _AuthCallbackHandler(BaseHTTPRequestHandler):
    # These class attributes are set by browser_auth before the server starts
    event: threading.Event
    token: Optional[str] = None
    host_value: Optional[str] = None

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        # Silence HTTP server logging
        return

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/plane-cli/callback":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")
            return

        params = parse_qs(parsed.query)
        token = params.get("token", [None])[0]
        host = params.get("host", [None])[0]
        if not token:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing token")
            return

        _AuthCallbackHandler.token = token
        _AuthCallbackHandler.host_value = host

        self.send_response(200)
        self.end_headers()
        self.wfile.write(
            b"<html><body><h2>Plane CLI authenticated</h2>"
            b"<p>You can return to your terminal.</p></body></html>"
        )
        _AuthCallbackHandler.event.set()


def _create_token_with_credentials(host: str, email: str, password: str, label: str = "plane-cli") -> PlaneConfig:
    normalized_host = normalize_host(host)
    base_url = normalized_host if normalized_host.startswith("http") else f"https://{normalized_host}"
    url = f"{base_url}/api/cli/token/"
    with httpx.Client(timeout=15.0) as client:
        response = client.post(
            url,
            json={"email": email, "password": password, "label": label},
        )
    if response.status_code >= 400:
        raise typer.BadParameter(f"Authentication failed: {response.text}")

    data = response.json()
    token = data.get("token")
    if not token:
        raise typer.BadParameter("No token returned from CLI authentication endpoint.")
    return PlaneConfig(host=normalized_host, token=token)


def browser_auth(host: str, timeout_seconds: int = 300) -> PlaneConfig:
    normalized_host = normalize_host(host)
    base_url = normalized_host if normalized_host.startswith("http") else f"https://{normalized_host}"
    event = threading.Event()
    _AuthCallbackHandler.event = event

    server = ThreadingHTTPServer(("127.0.0.1", 0), _AuthCallbackHandler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    connect_url = f"{base_url}/cli/connect?port={port}"
    console.print(f"[bold]Opening browser:[/] {connect_url}")
    opened = webbrowser.open(connect_url, new=2)
    if not opened:
        console.print(f"Open this URL manually to continue authentication:\n{connect_url}")

    start = time.time()
    while time.time() - start < timeout_seconds:
        if event.wait(timeout=1):
            break

    server.shutdown()
    thread.join(timeout=1)

    if not event.is_set():
        raise typer.BadParameter("Timed out waiting for browser authentication.")

    token = _AuthCallbackHandler.token
    host_value = _AuthCallbackHandler.host_value or normalized_host
    if not token:
        raise typer.BadParameter("Authentication callback did not include a token.")

    return PlaneConfig(host=host_value, token=token)


def auth_flow(
    host: str = "app.plane.so",
    use_browser: bool = True,
    email: Optional[str] = None,
    password: Optional[str] = None,
    token: Optional[str] = None,
) -> PlaneConfig:
    normalized_host = normalize_host(host)
    if token:
        config = PlaneConfig(host=normalized_host, token=token)
        save_config(config)
        console.print("[green]Saved token from --token flag.[/]")
        return config

    if use_browser:
        console.print("Starting browser-based authentication...")
        config = browser_auth(normalized_host)
        save_config(config)
        console.print(f"[green]Token saved to {CONFIG_PATH}.[/]")
        return config

    email = email or Prompt.ask("Email")
    password = password or Prompt.ask("Password", password=True)
    confirm = Confirm.ask(f"Issuing a new PAT for {email} on {host}. Continue?", default=True)
    if not confirm:
        raise typer.Abort()

    config = _create_token_with_credentials(normalized_host, email, password)
    save_config(config)
    console.print(f"[green]Token saved to {CONFIG_PATH} after credential authentication.[/]")
    return config
