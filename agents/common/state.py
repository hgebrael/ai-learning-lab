"""LangGraph state definitions for DevOps agents."""

from __future__ import annotations

from typing import Annotated, Literal
from dataclasses import dataclass, field
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


@dataclass
class ClusterInfo:
    name: str
    status: Literal["creating", "running", "stopped", "deleted", "unknown"]
    nodes: int = 1
    context: str = ""
    error: str | None = None


@dataclass
class DeploymentInfo:
    name: str
    resource_type: str  # manifest, helm_chart
    resource_path: str
    namespace: str = "default"
    status: Literal["pending", "applied", "failed", "deleted"] = "pending"
    error: str | None = None


@dataclass
class PipelineInfo:
    name: str
    platform: str  # github_actions, argocd, etc.
    config_path: str | None = None
    status: Literal["generated", "applied", "failed"] = "generated"


class DevOpsState:
    """State shared across all DevOps agents in a LangGraph workflow."""

    def __init__(self):
        self.messages: list[BaseMessage] = []
        self.clusters: dict[str, ClusterInfo] = {}
        self.deployments: list[DeploymentInfo] = []
        self.pipelines: list[PipelineInfo] = []
        self.current_task: str = ""
        self.error: str | None = None

    def add_cluster(self, cluster: ClusterInfo) -> None:
        self.clusters[cluster.name] = cluster

    def get_cluster(self, name: str) -> ClusterInfo | None:
        return self.clusters.get(name)

    def add_deployment(self, deployment: DeploymentInfo) -> None:
        self.deployments.append(deployment)

    def add_pipeline(self, pipeline: PipelineInfo) -> None:
        self.pipelines.append(pipeline)

    def to_dict(self) -> dict:
        return {
            "messages": self.messages,
            "clusters": {k: vars(v) for k, v in self.clusters.items()},
            "deployments": [vars(d) for d in self.deployments],
            "pipelines": [vars(p) for p in self.pipelines],
            "current_task": self.current_task,
            "error": self.error,
        }
