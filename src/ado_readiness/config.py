"""Configuration management for ADO Readiness Analyzer."""

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class ADOConfig(BaseModel):
    """Azure DevOps configuration settings."""
    
    organization_url: str = Field(..., description="Azure DevOps organization URL")
    pat: str = Field(..., description="Personal Access Token")
    default_project: Optional[str] = Field(None, description="Default project to scan")


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    config_dir = Path.home() / ".ado-readiness"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_file() -> Path:
    """Get the configuration file path."""
    return get_config_dir() / "config.yaml"


def config_exists() -> bool:
    """Check if configuration file exists."""
    return get_config_file().exists()


def save_config(config: ADOConfig) -> None:
    """Save configuration to file."""
    config_file = get_config_file()
    
    data = {
        "organization_url": config.organization_url,
        "pat": config.pat,
    }
    
    if config.default_project:
        data["default_project"] = config.default_project
    
    with open(config_file, "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False)
    
    # Set restrictive permissions (owner read/write only)
    try:
        os.chmod(config_file, 0o600)
    except OSError:
        pass  # Windows may not support chmod


def get_config() -> ADOConfig:
    """Load configuration from file."""
    config_file = get_config_file()
    
    if not config_file.exists():
        raise FileNotFoundError(
            "Configuration not found. Run 'ado-readiness configure' first."
        )
    
    with open(config_file) as f:
        data = yaml.safe_load(f)
    
    return ADOConfig(**data)


def delete_config() -> None:
    """Delete configuration file."""
    config_file = get_config_file()
    if config_file.exists():
        config_file.unlink()
