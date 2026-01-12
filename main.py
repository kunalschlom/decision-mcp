from fastmcp import FastMCP, Client
from datetime import datetime
import os

# ----------------------------
# Remote MCP Clients
# ----------------------------
HEALTH_MCP = Client("https://romantic-black-camel.fastmcp.app/mcp")
PRODUCTIVITY_MCP = Client("https://maximum-brown-silverfish.fastmcp.app/mcp")
COGNITIVE_MCP = Client("https://dynamic-aquamarine-junglefowl.fastmcp.app/mcp")

mcp = FastMCP(name="DecisionMCP")

# ----------------------------
# Intent Detection
# ----------------------------
def detect_domain(text: str) -> str:
    t = text.lower()

    if any(k in t for k in ["sleep", "steps", "health", "fatigue"]):
        return "health"

    if any(k in t for k in ["task", "work", "deadline", "productivity"]):
        return "productivity"

    if any(k in t for k in ["focus", "stress", "mental", "cognitive"]):
        return "cognitive"

    if any(k in t for k in ["summary", "overall", "decision"]):
        return "summary"

    return "unknown"


# ----------------------------
# SINGLE USER ENTRYPOINT
# ----------------------------
@mcp.tool
async def decide(user_input: str, data: dict | None = None):
    """
    The ONLY tool the user ever calls.
    """
    if data is None:
        data = {}
    
    domain = detect_domain(user_input)
    today = datetime.today().strftime("%Y-%m-%d")

    # ----------------------------
    # HEALTH FLOW
    # ----------------------------
    if domain == "health":
        async with HEALTH_MCP as client:  
            await client.call_tool("add_health_data", data)  # Fixed: removed curly braces

            signal = await client.call_tool(
                "generate_signal",
                {"date": data.get("date", today)}
            )

            return {
                "handled_by": "health_mcp",
                "signal": signal
            }

    # ----------------------------
    # PRODUCTIVITY FLOW
    # ----------------------------
    if domain == "productivity":
        signal = await PRODUCTIVITY_MCP.call_tool("summary", data)

        return {
            "handled_by": "productivity_mcp",
            "signal": signal
        }

    # ----------------------------
    # COGNITIVE FLOW
    # ----------------------------
    if domain == "cognitive":
        await COGNITIVE_MCP.call_tool("add_data", data)  # Fixed: changed call to call_tool

        signal = await COGNITIVE_MCP.call_tool(  # Fixed: changed call to call_tool
            "cognitive_signal_",
            {"date": data.get("date", today)}
        )

        return {
            "handled_by": "cognitive_mcp",
            "signal": signal
        }

    # ----------------------------
    # GLOBAL SUMMARY
    # ----------------------------
    if domain == "summary":
        async with HEALTH_MCP as client:
            health = await client.call_tool(
                "generate_signal",
                {"date": today}
            )

        async with PRODUCTIVITY_MCP as client:
            productivity = await client.call_tool(
                "summary",
                {}
            )

        async with COGNITIVE_MCP as client:
            cognitive = await client.call_tool(
                "cognitive_signal_",
                {"date": today}
            )

        return {
            "date": today,
            "health": health,
            "productivity": productivity,
            "cognitive": cognitive,
            "final_decision": "Aggregated by Decision MCP"
        }

    return {
        "error": "Intent not recognized",
        "hint": "Provide health, productivity, cognitive data, or ask for summary"
    }


if __name__ == "__main__":
    mcp.run(transport="http",port=8005,host="0.0.0.0")