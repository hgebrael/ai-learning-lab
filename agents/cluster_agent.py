"""Cluster management agent - creates, deletes, and inspects kind clusters."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

from agents.common.prompts import CLUSTER_AGENT_PROMPT
from agents.common.tools import (
    kind_create_cluster,
    kind_delete_cluster,
    kind_list_clusters,
    kind_get_cluster_status,
    kubectl_get_nodes,
)


def get_cluster_tools():
    """Return list of tool functions for the cluster agent."""
    return [
        kind_create_cluster,
        kind_delete_cluster,
        kind_list_clusters,
        kind_get_cluster_status,
        kubectl_get_nodes,
    ]


def create_cluster_agent(model: str = "llama3.1:8b"):
    """Create a LangGraph ReAct agent for cluster management."""
    llm = ChatOllama(model=model)
    tools = get_cluster_tools()

    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=CLUSTER_AGENT_PROMPT,
    )
    return agent


async def run_cluster_agent(user_request: str, model: str = "llama3.1:8b") -> dict:
    """Run the cluster agent with a user request."""
    agent = create_cluster_agent(model)
    result = await agent.ainvoke({
        "messages": [HumanMessage(content=user_request)],
    })
    return result


def run_cluster_agent_sync(user_request: str, model: str = "llama3.1:8b") -> dict:
    """Synchronous wrapper for the cluster agent."""
    import asyncio
    return asyncio.run(run_cluster_agent(user_request, model))


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv

    load_dotenv()

    request = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "List all kind clusters"
    result = run_cluster_agent_sync(request)

    for msg in result["messages"]:
        role = msg.__class__.__name__.replace("Message", "")
        print(f"[{role}] {msg.content}")
