"""Tests for configuration module."""

import pytest
from pathlib import Path
from ado_readiness.config import ADOConfig, save_config, get_config, config_exists, delete_config


@pytest.fixture
def temp_config(tmp_path, monkeypatch):
    """Use temporary directory for config."""
    monkeypatch.setattr("ado_readiness.config.get_config_dir", lambda: tmp_path)
    yield tmp_path


def test_ado_config_model():
    """Test ADOConfig model validation."""
    config = ADOConfig(
        organization_url="https://dev.azure.com/myorg",
        pat="secret123"
    )
    assert config.organization_url == "https://dev.azure.com/myorg"
    assert config.pat == "secret123"
    assert config.default_project is None


def test_save_and_load_config(temp_config):
    """Test saving and loading configuration."""
    config = ADOConfig(
        organization_url="https://dev.azure.com/testorg",
        pat="testpat123"
    )
    
    save_config(config)
    assert config_exists()
    
    loaded = get_config()
    assert loaded.organization_url == config.organization_url
    assert loaded.pat == config.pat


def test_delete_config(temp_config):
    """Test deleting configuration."""
    config = ADOConfig(
        organization_url="https://dev.azure.com/testorg",
        pat="testpat123"
    )
    
    save_config(config)
    assert config_exists()
    
    delete_config()
    assert not config_exists()


def test_get_config_not_found(temp_config):
    """Test error when config doesn't exist."""
    with pytest.raises(FileNotFoundError):
        get_config()
