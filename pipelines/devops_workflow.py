"""LangGraph orchestrator that chains cluster, deploy, and pipeline agents."""

from __future__ import annotations

from dataclasses import dataclass, field

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END

from agents.common.prompts import ORCHESTRATOR_PROMPT
from agents.cluster_agent import create_cluster_agent
from agents.deploy_agent import create_deploy_agent
from agents.pipeline_agent import run_pipeline_agent


@dataclass
class OrchestratorState:
    user_request: str = ""
    current_step: str = ""
    cluster_name: str = "dev-cluster"
    cluster_status: str = ""
    deploy_result: str = ""
    pipeline_result: str = ""
    error: str | None = None
    messages: list = field(default_factory=list)


async def route_request(state: OrchestratorState) -> OrchestratorState:
    """Analyze the user request and determine which agents to invoke."""
    llm = ChatOllama(model="llama3.1:8b")

    response = await llm.ainvoke([
        SystemMessage(content=ORCHESTRATOR_PROMPT),
        HumanMessage(content=f"""Analyze this request and determine what needs to happen:
- needs_cluster: does it need cluster creation/management?
- needs_deploy: does it need deployments?
- needs_pipeline: does it need CI/CD generation?
- cluster_name: extracted or default cluster name

Request: {state.user_request}"""),
    ])

    content = response.content.lower()
    state.current_step = "analyzed"

    if "create" in content or "cluster" in content or "kind" in content:
        state.cluster_status = "needs_action"

    if "deploy" in content or "apply" in content or "helm" in content:
        state.deploy_result = "needs_action"

    if "pipeline" in content or "ci/cd" in content or "github" in content or "argocd" in content:
        state.pipeline_result = "needs_action"

    if not any([state.cluster_status, state.deploy_result, state.pipeline_result]):
        state.cluster_status = "needs_action"

    state.messages.append(AIMessage(content=response.content))
    return state


async def handle_cluster(state: OrchestratorState) -> OrchestratorState:
    """Delegate cluster operations to the cluster agent."""
    if not state.cluster_status:
        return state

    try:
        agent = create_cluster_agent()
        result = await agent.ainvoke({
            "messages": [HumanMessage(content=state.user_request)],
        })
        last_msg = result["messages"][-1]
        state.cluster_status = f"completed: {last_msg.content[:200]}"
        state.messages.extend(result["messages"])
    except Exception as e:
        state.error = f"Cluster agent error: {str(e)}"
        state.cluster_status = "failed"

    return state


async def handle_deploy(state: OrchestratorState) -> OrchestratorState:
    """Delegate deployment operations to the deploy agent."""
    if not state.deploy_result:
        return state

    try:
        agent = create_deploy_agent()
        result = await agent.ainvoke({
            "messages": [HumanMessage(content=state.user_request)],
        })
        last_msg = result["messages"][-1]
        state.deploy_result = f"completed: {last_msg.content[:200]}"
        state.messages.extend(result["messages"])
    except Exception as e:
        state.error = f"Deploy agent error: {str(e)}"
        state.deploy_result = "failed"

    return state


async def handle_pipeline(state: OrchestratorState) -> OrchestratorState:
    """Delegate pipeline generation to the pipeline agent."""
    if not state.pipeline_result:
        return state

    try:
        platform = "github_actions"
        if "argocd" in state.user_request.lower():
            platform = "argocd"

        result = await run_pipeline_agent(
            platform=platform,
            project_name=state.cluster_name,
        )
        state.pipeline_result = f"completed: {result}"
    except Exception as e:
        state.error = f"Pipeline agent error: {str(e)}"
        state.pipeline_result = "failed"

    return state


def build_orchestrator_graph():
    """Build the LangGraph orchestration workflow."""
    workflow = StateGraph(OrchestratorState)

    workflow.add_node("route", route_request)
    workflow.add_node("cluster", handle_cluster)
    workflow.add_node("deploy", handle_deploy)
    workflow.add_node("pipeline", handle_pipeline)

    workflow.set_entry_point("route")

    workflow.add_conditional_edges(
        "route",
        lambda state: "cluster" if state.cluster_status else (
            "deploy" if state.deploy_result else (
                "pipeline" if state.pipeline_result else END
            )
        ),
    )
    workflow.add_edge("cluster", "deploy")
    workflow.add_edge("deploy", "pipeline")
    workflow.add_edge("pipeline", END)

    return workflow.compile()


async def run_orchestrator(user_request: str) -> dict:
    """Run the full orchestrator workflow."""
    graph = build_orchestrator_graph()
    initial_state = OrchestratorState(user_request=user_request)
    result = await graph.ainvoke(initial_state)
    return result


def run_orchestrator_sync(user_request: str) -> dict:
    """Synchronous wrapper for the orchestrator."""
    import asyncio
    return asyncio.run(run_orchestrator(user_request))


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv

    load_dotenv()

    request = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Create a kind cluster and deploy nginx"
    result = run_orchestrator_sync(request)

    print(f"Cluster: {result.cluster_status}")
    print(f"Deploy: {result.deploy_result}")
    print(f"Pipeline: {result.pipeline_result}")
    if result.error:
        print(f"Error: {result.error}")
