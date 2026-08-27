"""Shell and Kubernetes tool wrappers for DevOps agents."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field


@dataclass
class ToolResult:
    stdout: str
    stderr: str
    returncode: int

    @property
    def success(self) -> bool:
        return self.returncode == 0

    @property
    def output(self) -> str:
        return self.stdout if self.success else self.stderr


def run_command(cmd: list[str], timeout: int = 120) -> ToolResult:
    """Run a shell command and return structured output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return ToolResult(
            stdout=result.stdout.strip(),
            stderr=result.stderr.strip(),
            returncode=result.returncode,
        )
    except FileNotFoundError:
        return ToolResult(
            stdout="",
            stderr=f"Command not found: {cmd[0]}",
            returncode=127,
        )
    except subprocess.TimeoutExpired:
        return ToolResult(
            stdout="",
            stderr=f"Command timed out after {timeout}s",
            returncode=124,
        )


# --- Kind tools ---

def kind_create_cluster(name: str, nodes: int = 1, wait: str = "60s") -> ToolResult:
    """Create a new kind Kubernetes cluster with the given name."""
    cmd = ["kind", "create", "cluster", "--name", name, f"--wait={wait}"]
    if nodes > 1:
        # kind doesn't have a --nodes flag; use a config for multi-node
        # For simplicity, we create single node and note multi-node needs config
        pass
    return run_command(cmd)


def kind_delete_cluster(name: str) -> ToolResult:
    """Delete an existing kind cluster by name."""
    return run_command(["kind", "delete", "cluster", "--name", name])


def kind_list_clusters() -> ToolResult:
    """List all kind clusters."""
    return run_command(["kind", "get", "clusters"])


def kind_get_cluster_status(name: str) -> ToolResult:
    """Get the status of a kind cluster by name."""
    result = run_command(["kubectl", "cluster-info", "--context", f"kind-{name}"])
    if result.success:
        return result
    # Try to check if the cluster exists at all
    listing = kind_list_clusters()
    if name in listing.stdout:
        return ToolResult(
            stdout=f"Cluster '{name}' exists but is unreachable",
            stderr=result.stderr,
            returncode=1,
        )
    return ToolResult(
        stdout="",
        stderr=f"Cluster '{name}' not found",
        returncode=1,
    )


# --- Kubectl tools ---

def kubectl_apply(manifest_path: str, context: str | None = None) -> ToolResult:
    """Apply a Kubernetes manifest file to a cluster."""
    cmd = ["kubectl", "apply", "-f", manifest_path]
    if context:
        cmd.extend(["--context", context])
    return run_command(cmd)


def kubectl_get_resources(
    resource: str = "pods",
    namespace: str = "default",
    context: str | None = None,
) -> ToolResult:
    """Get Kubernetes resources (pods, services, etc) from a namespace."""
    cmd = ["kubectl", "get", resource, "-n", namespace, "-o", "wide"]
    if context:
        cmd.extend(["--context", context])
    return run_command(cmd)


def kubectl_delete(manifest_path: str, context: str | None = None) -> ToolResult:
    """Delete Kubernetes resources defined in a manifest file."""
    cmd = ["kubectl", "delete", "-f", manifest_path]
    if context:
        cmd.extend(["--context", context])
    return run_command(cmd)


def kubectl_get_nodes(context: str | None = None) -> ToolResult:
    """Get all nodes in the cluster."""
    cmd = ["kubectl", "get", "nodes", "-o", "wide"]
    if context:
        cmd.extend(["--context", context])
    return run_command(cmd)


# --- Helm tools ---

def helm_install(
    release: str,
    chart: str,
    namespace: str = "default",
    values_file: str | None = None,
    context: str | None = None,
) -> ToolResult:
    """Install a Helm chart as a release in a namespace."""
    cmd = ["helm", "install", release, chart, "-n", namespace, "--create-namespace"]
    if values_file:
        cmd.extend(["-f", values_file])
    if context:
        cmd.extend(["--kube-context", context])
    return run_command(cmd)


def helm_uninstall(
    release: str,
    namespace: str = "default",
    context: str | None = None,
) -> ToolResult:
    """Uninstall a Helm release from a namespace."""
    cmd = ["helm", "uninstall", release, "-n", namespace]
    if context:
        cmd.extend(["--kube-context", context])
    return run_command(cmd)


def helm_list(namespace: str = "all", context: str | None = None) -> ToolResult:
    """List all Helm releases in a namespace."""
    cmd = ["helm", "list", "-n", namespace]
    if context:
        cmd.extend(["--kube-context", context])
    return run_command(cmd)
