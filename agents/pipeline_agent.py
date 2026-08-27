"""Pipeline generation agent - creates CI/CD configs for GitHub Actions and ArgoCD."""

from __future__ import annotations

from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from agents.common.prompts import PIPELINE_AGENT_PROMPT


GITHUB_ACTIONS_TEMPLATE = """\
name: {name}

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{{{ github.repository }}}}

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{{{ env.REGISTRY }}}}
          username: ${{{{ github.actor }}}}
          password: ${{{{ secrets.GITHUB_TOKEN }}}}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{{{ env.REGISTRY }}}}/${{{{{ env.IMAGE_NAME }}}}:latest
            ${{{{ env.REGISTRY }}}}/${{{{{ env.IMAGE_NAME }}}}:${{{{ github.sha }}}}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Kubernetes
        run: |
          kubectl apply -f k8s/
          kubectl set image deployment/{name} {name}=${{{{ env.REGISTRY }}}}/${{{{{ env.IMAGE_NAME }}}}:${{{{ github.sha }}}}
"""

ARGOCD_APPLICATION_TEMPLATE = """\
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: {name}
  namespace: argocd
spec:
  project: default
  source:
    repoURL: {repo_url}
    targetRevision: HEAD
    path: {chart_path}
  destination:
    server: https://kubernetes.default.svc
    namespace: {namespace}
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
"""


async def generate_github_actions(
    name: str,
    output_dir: str = ".github/workflows",
) -> str:
    """Generate a GitHub Actions workflow file."""
    content = GITHUB_ACTIONS_TEMPLATE.format(name=name)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = output_path / "ci-cd.yaml"
    file_path.write_text(content)
    return str(file_path)


async def generate_argocd_application(
    name: str,
    repo_url: str = "https://github.com/example/repo",
    chart_path: str = ".",
    namespace: str = "default",
    output_dir: str = "argocd",
) -> str:
    """Generate an ArgoCD Application manifest."""
    content = ARGOCD_APPLICATION_TEMPLATE.format(
        name=name,
        repo_url=repo_url,
        chart_path=chart_path,
        namespace=namespace,
    )
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = output_path / f"{name}-application.yaml"
    file_path.write_text(content)
    return str(file_path)


async def run_pipeline_agent(
    platform: str,
    project_name: str,
    **kwargs,
) -> dict:
    """Generate pipeline config for the specified platform."""
    if platform == "github_actions":
        path = await generate_github_actions(project_name, **kwargs)
        return {"platform": platform, "path": path, "status": "generated"}
    elif platform == "argocd":
        path = await generate_argocd_application(project_name, **kwargs)
        return {"platform": platform, "path": path, "status": "generated"}
    else:
        return {"platform": platform, "error": f"Unsupported platform: {platform}"}
