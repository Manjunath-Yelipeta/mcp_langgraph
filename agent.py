import asyncio
import os
from pathlib import Path

from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage
from langchain.mcp import MCPAdapter
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode


async def main():
    server_file = Path(__file__).parent / "log_server.py"

    # Connect to the MCP server.
    # The adapter starts log_server.py as a separate process.
    async with MCPAdapter(server_file) as adapter:

        # Discover the server's tools and convert them into
        # LangChain-compatible tool objects.
        tools = await adapter.list_tools()

        print("Discovered tools:", [tool.name for tool in tools])

        # Use a tool-capable model from your chosen provider.
        model = init_chat_model(os.environ["CHAT_MODEL"])
        model_with_tools = model.bind_tools(tools)

        # Node 1: ask the LLM what to do.
        async def assistant(state: MessagesState):
            response = await model_with_tools.ainvoke(
                [
                    SystemMessage(
                        content=(
                            "Investigate application failures. "
                            "Read the payment logs before diagnosing "
                            "a payment failure. Explain the evidence."
                        )
                    ),
                    *state["messages"],
                ]
            )

            print("LLM requested:", response.tool_calls)

            return {"messages": [response]}

        # Decide which connection to follow after the LLM responds.
        def route(state: MessagesState):
            last_message = state["messages"][-1]

            if last_message.tool_calls:
                return "tools"

            return END

        # Define the graph.
        builder = StateGraph(MessagesState)

        builder.add_node("assistant", assistant)
        builder.add_node("tools", ToolNode(tools))

        builder.add_edge(START, "assistant")
        builder.add_conditional_edges("assistant", route)
        builder.add_edge("tools", "assistant")

        graph = builder.compile()

        # Execute the graph.
        result = await graph.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "Why is my payment application failing?",
                    }
                ]
            }
        )

        print("\nFinal answer:")
        print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
