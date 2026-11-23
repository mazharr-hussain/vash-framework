"""`vash mcp`: VASH's tools for a chat harness, over MCP (stdio, or HTTP on 127.0.0.1 for the web chat). Uses the official MCP Python SDK (MIT)."""
from __future__ import annotations

import functools

from vash.core.exceptions import VashError

INSTRUCTIONS = (
    "You are the front desk of VASH, a virtual software house. Turn the owner's requests into VASH projects and "
    "tasks: pick a short task id and the kind of work (code, test, artifact for documents, feature, prompt), write "
    "the request clearly with what the result must contain, then start it with run_task and report task_status. "
    "VASH itself writes, checks (Gate 1) and reviews the work (AvA); never write the deliverable yourself. "
    "For heavy model work (a big model, many prompts) use the free GPU tools (gpu_quota, gpu_run, gpu_status, "
    "gpu_result); their prompts leave the VM, so never put client data in them."
)


def build():
    try:
        from mcp.server.mcpserver import MCPServer
    except ImportError as e:
        raise VashError(f"The MCP library is missing ({e})", "pip install 'mcp==2.3.0' into VASH's environment")
    from vash.mcp import tools

    from mcp.server.mcpserver.exceptions import ToolError as McpToolError

    def guarded(fn):
        """A refused argument goes back to the harness as a plain tool error with its explanation."""
        @functools.wraps(fn)
        def call(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except (tools.ToolError, VashError) as e:
                raise McpToolError(str(e)) from None
        return call

    server = MCPServer("vash", instructions=INSTRUCTIONS)
    for fn in (tools.list_projects, tools.new_project, tools.new_task, tools.run_task, tools.task_status,
               tools.read_result, tools.list_tasks, tools.doctor, tools.gpu_quota, tools.gpu_run, tools.gpu_status,
               tools.gpu_result):
        server.add_tool(guarded(fn))
    return server


HTTP_PORT = 8765  # `vash mcp --http`: for the web chat on the same VM (Open WebUI), on the VM's own interface only


def run(http: bool = False, port: int = HTTP_PORT) -> int:
    if http:
        # Bound to 127.0.0.1 only: the web page reaches it on the VM; nothing outside the VM can.
        build().run("streamable-http", host="127.0.0.1", port=port, stateless_http=True)
    else:
        build().run("stdio")
    return 0
