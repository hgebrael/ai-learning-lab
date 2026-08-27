"""Deployment agent - applies manifests and Helm charts to K8s clusters."""

from __future__ import annotations

from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

from agents.common.prompts import DEPLOY_AGENT_PROMPT
from agents.common.tools import (
    kubectl_apply,
    kubectl_get_resources,
    kubectl_delete,
    kubectl_get_nodes,
    helm_install,
    helm_uninstall,
    helm_list,
)


def get_deploy_tools():
    """Return list of tool functions for the deploy agent."""
    return [
        kubectl_apply,
        kubectl_get_resources,
        kubectl_delete,
        kubectl_get_nodes,
        helm_install,
        helm_uninstall,
        helm_list,
    ]


def create_deploy_agent(model: str = "llama3.1:8b"):
    """Create a LangGraph ReAct agent for deployments."""
    llm = ChatOllama(model=model)
    tools = get_deploy_tools()

    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=DEPLOY_AGENT_PROMPT,
    )
    return agent


async def run_deploy_agent(user_request: str, model: str = "llama3.1:8b") -> dict:
    """Run the deploy agent with a user request."""
    agent = create_deploy_agent(model)
    result = await agent.ainvoke({
        "messages": [HumanMessage(content=user_request)],
    })
    return result


def run_deploy_agent_sync(user_request: str, model: str = "llama3.1:8b") -> dict:
    """Synchronous wrapper for the deploy agent."""
    import asyncio
    return asyncio.run(run_deploy_agent(user_request, model))


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv

    load_dotenv()

    request = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Show all pods in default namespace"
    result = run_deploy_agent_sync(request)

    for msg in result["messages"]:
        role = msg.__class__.__name__.replace("Message", "")
        print(f"[{role}] {msg.content}")
