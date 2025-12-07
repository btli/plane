from __future__ import annotations

from typing import Any

import httpx

from .config import PlaneConfig
from .types import IssueCreate, IssueResponse, ProjectResponse, UserResponse, WorkspaceResponse


class PlaneAPIError(Exception):
    """Raised when the Plane API returns an unexpected response."""


class PlaneClient:
    def __init__(self, config: PlaneConfig, timeout: float = 15.0) -> None:
        self.config = config
        base_url = config.host
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"
        self.base_url = base_url.rstrip("/")
        self.session = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={"X-Api-Key": config.token, "User-Agent": "plane-cli/0.1.0"},
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        response = self.session.request(method, path, **kwargs)
        if response.status_code >= 400:
            raise PlaneAPIError(f"{response.status_code}: {response.text}")
        return response.json()

    def whoami(self) -> UserResponse:
        data = self._request("GET", "/api/v1/users/me/")
        return UserResponse.model_validate(data)

    def list_workspaces(self) -> list[WorkspaceResponse]:
        data = self._request("GET", "/api/workspaces/")
        items = data.get("results", data) if isinstance(data, dict) else data
        return [WorkspaceResponse.model_validate(item) for item in items]

    def list_projects(self, workspace: str, order_by: str = "-created_at") -> list[ProjectResponse]:
        data = self._request(
            "GET",
            f"/api/v1/workspaces/{workspace}/projects/",
            params={"order_by": order_by},
        )
        items = data.get("results", data) if isinstance(data, dict) else data
        return [ProjectResponse.model_validate(item) for item in items]

    def list_issues(self, workspace: str, project_id: str, limit: int = 20) -> list[IssueResponse]:
        data = self._request(
            "GET",
            f"/api/v1/workspaces/{workspace}/projects/{project_id}/work-items/",
            params={"page_size": limit},
        )
        items = data.get("results", data) if isinstance(data, dict) else data
        return [IssueResponse.model_validate(item) for item in items]

    def create_issue(self, workspace: str, project_id: str, payload: IssueCreate) -> IssueResponse:
        data = self._request(
            "POST",
            f"/api/v1/workspaces/{workspace}/projects/{project_id}/work-items/",
            json=payload.model_dump(exclude_none=True),
        )
        return IssueResponse.model_validate(data)
