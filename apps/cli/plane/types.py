from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class WorkspaceResponse(BaseModel):
    id: Optional[str] = Field(default=None, alias="workspace_id")
    slug: str
    name: str


class ProjectResponse(BaseModel):
    id: str
    name: str
    identifier: str
    description: Optional[str] = None
    is_member: Optional[bool] = None


class IssueResponse(BaseModel):
    id: str
    name: str = Field(alias="name", default="")
    description: Optional[str] = None
    state: Optional[str] = None
    assignees: Optional[list[str]] = None
    sequence_id: Optional[int] = Field(default=None, alias="sequence_id")


class IssueCreate(BaseModel):
    name: str
    description: Optional[str] = None
    assignees: Optional[list[str]] = None
    state: Optional[str] = None
