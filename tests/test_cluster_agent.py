"""Basic tests for cluster agent tools."""

import pytest
from unittest.mock import patch, MagicMock

from agents.common.tools import (
    run_command,
    ToolResult,
    kind_list_clusters,
    kind_get_cluster_status,
)


class TestToolResult:
    def test_success(self):
        result = ToolResult(stdout="ok", stderr="", returncode=0)
        assert result.success is True
        assert result.output == "ok"

    def test_failure(self):
        result = ToolResult(stdout="", stderr="error", returncode=1)
        assert result.success is False
        assert result.output == "error"


class TestRunCommand:
    @patch("agents.common.tools.subprocess.run")
    def test_successful_command(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="hello\n", stderr="", returncode=0
        )
        result = run_command(["echo", "hello"])
        assert result.success is True
        assert result.stdout == "hello"

    @patch("agents.common.tools.subprocess.run")
    def test_failed_command(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="", stderr="not found", returncode=1
        )
        result = run_command(["false"])
        assert result.success is False

    def test_command_not_found(self):
        result = run_command(["nonexistent_command_xyz"])
        assert result.success is False
        assert result.returncode == 127


class TestKindTools:
    @patch("agents.common.tools.run_command")
    def test_kind_list_clusters(self, mock_run):
        mock_run.return_value = ToolResult(
            stdout="dev-cluster\nstaging", stderr="", returncode=0
        )
        result = kind_list_clusters()
        assert result.success is True
        assert "dev-cluster" in result.stdout

    @patch("agents.common.tools.run_command")
    def test_kind_get_cluster_status_found(self, mock_run):
        mock_run.return_value = ToolResult(
            stdout="Kubernetes control plane is running",
            stderr="",
            returncode=0,
        )
        result = kind_get_cluster_status("dev-cluster")
        assert result.success is True

    @patch("agents.common.tools.run_command")
    def test_kind_get_cluster_status_not_found(self, mock_run):
        mock_run.return_value = ToolResult(
            stdout="",
            stderr="error: no context",
            returncode=1,
        )
        result = kind_get_cluster_status("nonexistent")
        assert result.success is False
