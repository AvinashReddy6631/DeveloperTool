import asyncio
import json
import os

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# ============================================
# 1. Load environment variables
# ============================================

load_dotenv()


# ============================================
# 2. OpenRouter LLM
# ============================================

llm = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)


# ============================================
# 3. MCP Server configuration
# ============================================

server_params = StdioServerParameters(
    command="python",
    args=["server.py"],
    env=os.environ.copy(),
)


# ============================================
# 4. Convert MCP tools to OpenRouter format
# ============================================

def convert_tools(mcp_tools):

    tools = []

    for tool in mcp_tools:

        tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.input_schema,
            }
        })

    return tools


# ============================================
# 5. Main function
# ============================================

async def main():

    # ========================================
    # Connect to MCP server
    # ========================================

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            # ========================================
            # Initialize MCP
            # ========================================

            await session.initialize()
            
            
            print("Connected to MCP server!")


            # ========================================
            # Discover MCP resources
            # ========================================

            resources = await session.list_resources()

            print("\nMCP Resources:")

            for resource in resources.resources:
                print("-", resource.uri)


            # ========================================
            # Discover MCP tools
            # ========================================

            tools = await session.list_tools()

            print("\nMCP Tools:")

            for tool in tools.tools:
                print("-", tool.name)


            # ========================================
            # Convert MCP tools for OpenRouter
            # ========================================

            openrouter_tools = convert_tools(tools.tools)


            # ========================================
            # Conversation memory
            # ========================================

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an AI assistant with access to MCP tools. "
                        "Use an MCP tool whenever the user's question "
                        "requires external or database information. "
                        "For employee questions, use the appropriate "
                        "employee tool. "
                        "Do not invent information. "
                        "Do not assume a currency unless the data "
                        "explicitly provides one. "
                        "You can call multiple tools when necessary."
                    )
                }
            ]


            # ========================================
            # Continuous conversation
            # ========================================

            while True:

                user_input = input("\nYou: ")


                # ====================================
                # Exit
                # ====================================

                if user_input.lower() in ["exit", "quit"]:

                    print("Goodbye!")

                    break


                # ====================================
                # Add user message
                # ====================================

                messages.append({
                    "role": "user",
                    "content": user_input
                })


                # ====================================
                # AGENT LOOP
                # ====================================

                while True:

                    # =================================
                    # Ask LLM
                    # =================================

                    try:

                        response = llm.chat.completions.create(
                        model="openrouter/free",
                        max_tokens=500,
                        messages=messages,
                        tools=openrouter_tools,
                        tool_choice="auto"
                    )

                    except RateLimitError:

                        print("\n⚠️ OpenRouter rate limit reached.")
                        print(
                            "The free-model daily limit has been reached."
                        )
                        print(
                            "Please wait for the limit to reset "
                            "or add credits to OpenRouter."
                        )

                        return


                    # =================================
# Get LLM message safely
# =================================

                    if not response.choices:
                        print("\n⚠️ LLM returned no choices.")
                        print("Full response:", response)
                        break

                    message = response.choices[0].message


                    # =================================
                    # No tool required
                    # =================================

                    if not message.tool_calls:

                        print("\nAI:", message.content)

                        messages.append({
                            "role": "assistant",
                            "content": message.content
                        })

                        break


                    # =================================
                    # LLM requested tool(s)
                    # =================================

                    print("\nLLM requested tool(s):")


                    # Save assistant tool-call message
                    messages.append(
                        message.model_dump(exclude_none=True)
                    )


                    # =================================
                    # Execute requested tools
                    # =================================

                    for tool_call in message.tool_calls:

                        tool_name = tool_call.function.name

                        arguments = json.loads(
                            tool_call.function.arguments
                        )


                        print("Tool:", tool_name)
                        print("Arguments:", arguments)


                        # =================================
                        # Execute MCP tool
                        # =================================

                        result = await session.call_tool(
                            tool_name,
                            arguments=arguments
                        )


                        print("\nMCP Tool Result:")
                        print(result.content)


                        # =================================
                        # Extract tool result
                        # =================================

                        if result.content:

                            tool_result = result.content[0].text

                        else:

                            tool_result = (
                                "The MCP tool returned no result."
                            )


                        # =================================
                        # Send MCP result back to LLM
                        # =================================

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_result
                        })


                    # =================================
                    # IMPORTANT
                    #
                    # Do NOT break here.
                    #
                    # The loop goes back to the LLM.
                    # The LLM sees the MCP result and
                    # decides whether to give a final
                    # answer or call another tool.
                    # =================================


# ============================================
# 6. Run program
# ============================================

if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        print("\nProgram stopped.")