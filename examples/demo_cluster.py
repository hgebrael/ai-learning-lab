"""Quick demo script for the cluster agent."""

import asyncio
from dotenv import load_dotenv

from agents.cluster_agent import run_cluster_agent


async def main():
    load_dotenv()

    print("=== DevOps AI Agent Demo ===\n")

    # List clusters
    print("1. Listing existing kind clusters...")
    result = await run_cluster_agent("List all kind clusters")
    for msg in result["messages"]:
        role = msg.__class__.__name__.replace("Message", "")
        print(f"  [{role}] {msg.content[:300]}")
    print()

    # Get cluster status
    print("2. Checking cluster status...")
    result = await run_cluster_agent("What is the status of the dev-cluster? Show me the nodes.")
    for msg in result["messages"]:
        role = msg.__class__.__name__.replace("Message", "")
        print(f"  [{role}] {msg.content[:300]}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
