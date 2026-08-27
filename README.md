# ai-learning-lab

AI agents for DevOps automation with local Kubernetes clusters.

## Overview

This project builds intelligent agents that manage Kubernetes infrastructure using natural language. Agents handle cluster lifecycle, deployments, and CI/CD pipeline generation.

## Architecture

- **Cluster Agent** — Creates, deletes, and inspects kind clusters
- **Deploy Agent** — Applies manifests and Helm charts to clusters
- **Pipeline Agent** — Generates GitHub Actions and ArgoCD configs
- **Orchestrator** — Chains agents via LangGraph for complex workflows

## Setup

### Prerequisites

- Python 3.10+
- Docker (with WSL integration if on Windows)
- kubectl
- helm
- kind

### Install dependencies

```bash
pip install -e .
```

### Configure

```bash
# Ollama runs locally — no API key needed
# Start ollama serve in another terminal, then:
ollama pull llama3.1:8b
```

## Usage

### List clusters

```bash
python -m agents.cluster_agent "List all kind clusters"
```

### Create a cluster

```bash
python -m agents.cluster_agent "Create a kind cluster called dev-cluster"
```

### Deploy an app

```bash
python -m agents.deploy_agent "Apply the manifest at k8s/deployment.yaml to kind-dev-cluster"
```

### Generate a pipeline

```bash
python -m agents.pipeline_agent "Generate a GitHub Actions workflow for my project"
```

### Full orchestrator

```bash
python -m pipelines.devops_workflow "Create a kind cluster, deploy nginx, and generate a CI pipeline"
```

## Project Structure

```
agents/
├── common/
│   ├── tools.py        # Shell + K8s tool wrappers
│   ├── state.py        # LangGraph state definitions
│   └── prompts.py      # System prompts
├── cluster_agent.py    # Kind cluster management
├── deploy_agent.py     # kubectl/helm deployments
└── pipeline_agent.py   # CI/CD generation
pipelines/
└── devops_workflow.py  # LangGraph orchestrator
examples/
└── demo_cluster.py     # Quick start demo
tests/
└── test_cluster_agent.py
```
