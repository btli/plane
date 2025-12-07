from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


CONFIG_DIR = Path(os.environ.get("PLANE_CONFIG_DIR", Path.home() / ".plane"))
CONFIG_PATH = CONFIG_DIR / "config.yaml"


@dataclass
class PlaneConfig:
    host: str
    token: str
    default_workspace: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlaneConfig":
        return cls(
            host=data.get("host", ""),
            token=data.get("token", ""),
            default_workspace=data.get("default_workspace"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "host": self.host,
            "token": self.token,
            "default_workspace": self.default_workspace,
        }


def ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Optional[PlaneConfig]:
    if not CONFIG_PATH.exists():
        return None
    with CONFIG_PATH.open("r") as f:
        data = yaml.safe_load(f) or {}
    if not data.get("host") or not data.get("token"):
        return None
    return PlaneConfig.from_dict(data)


def save_config(config: PlaneConfig) -> None:
    ensure_config_dir()
    with CONFIG_PATH.open("w") as f:
        yaml.safe_dump(config.to_dict(), f)
