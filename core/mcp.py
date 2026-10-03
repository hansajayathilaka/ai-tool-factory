"""Project MCP servers: the repo-root .mcp.json, and the servers each tool may use (tool.json "mcp").

Claude Code reads .mcp.json only from the folder it was launched in, so these servers reach
sessions launched at the repo root. claude.ai connectors (Gmail, Google Drive...) need no entry
here: a tool names them by their server name, which starts with "claude_ai_".
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from .common import MCP_CONFIG
from .tool import MCP_NAME_RE, Tool
from .validate import BLOCKED_DOMAINS

CONNECTOR_PREFIX = "claude_ai_"
SERVER_TYPES = ("stdio", "http", "sse")
# Values under these env/header names must come from the environment as ${VAR}, never be committed.
SECRET_NAME_RE = re.compile(r"key|token|secret|password|passwd|auth|cookie|credential", re.I)
ENV_REF_RE = re.compile(r"\$\{[A-Za-z_][A-Za-z0-9_]*(?::-[^}]*)?\}")


def load_config(path: Path = MCP_CONFIG) -> tuple[dict, list[str]]:
    """Return (servers by name, problems). A missing file means no project servers."""
    if not path.is_file():
        return {}, []
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f".mcp.json: invalid JSON: {exc}"]
    if not isinstance(config, dict) or not isinstance(config.get("mcpServers"), dict):
        return {}, ['.mcp.json must be an object with an "mcpServers" object']
    servers = config["mcpServers"]
    return servers, check_servers(servers)


def server_type(server: dict) -> str | None:
    return server.get("type") or ("stdio" if "command" in server else None)


def check_servers(servers: dict) -> list[str]:
    """Return every problem in the mcpServers map; an empty list means it is safe to commit."""
    problems = []
    for name, s in servers.items():
        where = f".mcp.json: {name}"
        if not MCP_NAME_RE.match(name):
            problems.append(f"{where}: name must be letters, digits, _ and -")
        if not isinstance(s, dict):
            problems.append(f"{where}: must be an object")
            continue
        kind = server_type(s)
        if kind not in SERVER_TYPES:
            problems.append(f"{where}: type must be one of {', '.join(SERVER_TYPES)}")
        elif kind == "stdio" and not isinstance(s.get("command"), str):
            problems.append(f"{where}: a stdio server needs a command")
        elif kind != "stdio":
            url = s.get("url")
            host = (urlparse(url).hostname or "").lower() if isinstance(url, str) else ""
            if not host:
                problems.append(f"{where}: an {kind} server needs an http(s) url")
            elif any(host == d or host.endswith("." + d) for d in BLOCKED_DOMAINS):
                problems.append(f"{where}: Meta properties are never accessed ({host})")
        for field in ("env", "headers"):
            values = s.get(field, {})
            if not isinstance(values, dict):
                problems.append(f"{where}: {field} must be an object")
                continue
            for key, value in values.items():
                if SECRET_NAME_RE.search(key) and not (isinstance(value, str) and ENV_REF_RE.search(value)):
                    problems.append(f"{where}: {field}.{key} looks secret; use a ${{VAR}} reference, not a value")
    return problems


def target(server: dict) -> str:
    """Where a server runs, for listings. Never includes env, headers or URL query strings."""
    if server_type(server) == "stdio":
        return " ".join([server.get("command", ""), *map(str, server.get("args", []))]).strip()
    url = urlparse(str(server.get("url", "")))
    return f"{url.scheme}://{url.netloc}{url.path}"


def status(name: str, servers: dict) -> str:
    if name in servers:
        return "configured in .mcp.json"
    if name.startswith(CONNECTOR_PREFIX):
        return "claude.ai connector (enable it in claude.ai settings)"
    return "MISSING"


def tool_problems(tool: Tool, servers: dict) -> list[str]:
    return [f"tool.json mcp: {name!r} is not in .mcp.json and is not a claude.ai connector "
            f"({CONNECTOR_PREFIX}...)" for name in tool.mcp_servers if status(name, servers) == "MISSING"]
