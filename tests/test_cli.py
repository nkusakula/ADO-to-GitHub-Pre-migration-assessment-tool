"""Tests for CLI commands."""

import pytest
from typer.testing import CliRunner
from ado_readiness.cli import app


runner = CliRunner()


def test_version():
    """Test version command."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_help():
    """Test help output."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Azure DevOps Migration Readiness Analyzer" in result.output


def test_configure_help():
    """Test configure command help."""
    result = runner.invoke(app, ["configure", "--help"])
    assert result.exit_code == 0
    assert "organization" in result.output.lower()


def test_scan_without_config():
    """Test scan fails without configuration."""
    result = runner.invoke(app, ["scan"])
    assert result.exit_code == 1
    assert "configure" in result.output.lower()


def test_test_connection_without_config():
    """Test test-connection fails without configuration."""
    result = runner.invoke(app, ["test-connection"])
    assert result.exit_code == 1
    assert "configure" in result.output.lower()
