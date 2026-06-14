"""Composition demo: the intake agent reaching the rules core over MCP.

In production the screen step is not an in-process import but a tool call to the
rules-as-code-mcp server. This script demonstrates exactly that: it launches that
server over stdio (as a caseworker), sends a household derived from a synthetic
case, and captures the determination, rule trace, and citations it returns. That
is the deployable shape of the deterministic/probabilistic boundary.

No API key needed: this exercises the deterministic MCP server, not the model.

Run:  python clients/mcp_compose_demo.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

TRANSCRIPT = Path(__file__).with_name("compose_transcript.md")

# A household the way the validate node would hand it off (document-verified facts).
HOUSEHOLD = {
    "members": [{"age": 34}, {"age": 31}, {"age": 6}],
    "income": [{"kind": "earned", "monthly_amount": 2100}],
    "shelter_cost_monthly": 950,
    "utilities_monthly": 250,
}


def _server() -> StdioServerParameters:
    # Launch the rules-as-code-mcp server (installed in this venv) as a caseworker.
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "server.main"],
        env={"RULES_MCP_ROLE": "caseworker", "PYTHONUNBUFFERED": "1"},
    )


def _payload(result):
    if result.structuredContent is not None and not result.isError:
        return result.structuredContent
    text = "".join(getattr(c, "text", "") for c in result.content)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


async def main() -> None:
    lines = ["# Composition transcript — intake agent calling the rules core over MCP\n",
             "The intake agent's screen step delegates to the `rules-as-code-mcp` server "
             "over stdio. Below: a household sent to that server and the cited determination "
             "it returns.\n"]
    async with stdio_client(_server()) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            lines.append(f"Connected to **{init.serverInfo.name}** (caseworker scope).\n")

            screen = await session.call_tool("screen_programs", {"household": HOUSEHOLD})
            lines += ["## screen_programs", "```json", json.dumps(_payload(screen), indent=2)[:1500], "```\n"]

            det = await session.call_tool(
                "check_program_eligibility", {"program": "SNAP", "household": HOUSEHOLD}
            )
            payload = _payload(det)
            lines += ["## check_program_eligibility (determination + rule trace + citation)",
                      "```json", json.dumps(payload, indent=2)[:1800], "```\n"]
            if isinstance(payload, dict):
                lines.append(f"**Decision:** {payload.get('decision')} — every rule in the trace "
                             "carries a policy citation, so the agent's recommendation is auditable.\n")
    TRANSCRIPT.write_text("\n".join(lines))
    print(f"Wrote {TRANSCRIPT}")


if __name__ == "__main__":
    asyncio.run(main())
