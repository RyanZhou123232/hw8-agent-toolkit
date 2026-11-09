"""Minimal MCP stdio tools server, implementing the 2025-06-18 specification.

Scope: initialize, initialized notification, ping, tools/list, tools/call.
No HTTP, authentication, resources, prompts, sampling, or background jobs.
Reference: https://modelcontextprotocol.io/specification/2025-06-18
"""

import inspect
import json
import sys
from typing import Literal, get_args, get_origin, get_type_hints

PROTOCOLS = ("2024-11-05", "2025-03-26", "2025-06-18")


def tool_schema(tool):
    hints = get_type_hints(tool)
    properties, required = {}, []
    for name, arg in inspect.signature(tool).parameters.items():
        hint = hints[name]
        if get_origin(hint) is Literal:
            prop = {"type": "string", "enum": list(get_args(hint))}
        elif hint is str:
            prop = {"type": "string"}
        elif hint is int:
            prop = {"type": "integer"}
        else:
            types = ["null" if t is type(None) else "integer" if t is int else "string" for t in get_args(hint)]
            prop = {"type": types}
        if arg.default is inspect.Parameter.empty:
            required.append(name)
        else:
            prop["default"] = arg.default
        properties[name] = prop
    return {"type": "object", "properties": properties, "required": required, "additionalProperties": False}


def validate(arguments, schema):
    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be an object.")
    if set(arguments) - schema["properties"].keys():
        raise ValueError("Unknown tool argument.")
    if set(schema["required"]) - arguments.keys():
        raise ValueError("Missing required tool argument.")
    for key, value in arguments.items():
        prop = schema["properties"][key]
        actual = "null" if value is None else "boolean" if isinstance(value, bool) else "integer" if isinstance(value, int) else "string" if isinstance(value, str) else "other"
        types = prop["type"] if isinstance(prop["type"], list) else [prop["type"]]
        if actual not in types or ("enum" in prop and value not in prop["enum"]):
            raise ValueError(f"Invalid type or value for {key}.")


def serve(tool):
    schema = tool_schema(tool)
    initialized = False
    ready = False
    for line in sys.stdin.buffer:
        request_id = None
        try:
            try:
                request = json.loads(line)
            except (ValueError, UnicodeError):
                response = {"error": {"code": -32700, "message": "Parse error"}}
            else:
                if not isinstance(request, dict) or request.get("jsonrpc") != "2.0" or not isinstance(request.get("method"), str):
                    response = {"error": {"code": -32600, "message": "Invalid request"}}
                else:
                    request_id = request.get("id")
                    method, params = request["method"], request.get("params", {})
                    if "id" not in request:
                        if initialized and method == "notifications/initialized":
                            ready = True
                        continue
                    if not isinstance(params, dict):
                        response = {"error": {"code": -32602, "message": "params must be an object"}}
                    elif method == "initialize":
                        version = params.get("protocolVersion")
                        if not isinstance(version, str):
                            response = {"error": {"code": -32602, "message": "protocolVersion is required"}}
                        else:
                            initialized = True
                            response = {"result": {"protocolVersion": version if version in PROTOCOLS else PROTOCOLS[-1],
                                        "capabilities": {"tools": {"listChanged": False}},
                                        "serverInfo": {"name": "application-tracker", "version": "0.1.0"}}}
                    elif method == "ping":
                        response = {"result": {}}
                    elif not ready:
                        response = {"error": {"code": -32600, "message": "Initialize the session first"}}
                    elif method == "tools/list":
                        response = {"result": {"tools": [{"name": tool.__name__, "description": inspect.getdoc(tool), "inputSchema": schema}]}}
                    elif method == "tools/call":
                        if params.get("name") != tool.__name__:
                            response = {"error": {"code": -32602, "message": "Unknown tool"}}
                        else:
                            try:
                                arguments = params.get("arguments", {})
                                validate(arguments, schema)
                                result = tool(**arguments)
                                response = {"result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}], "isError": False}}
                            except Exception as exc:
                                response = {"result": {"content": [{"type": "text", "text": str(exc)}], "isError": True}}
                    else:
                        response = {"error": {"code": -32601, "message": "Method not found"}}
        except Exception as exc:
            print(f"MCP request failed: {type(exc).__name__}", file=sys.stderr)
            response = {"error": {"code": -32603, "message": "Internal error"}}
        envelope = {"jsonrpc": "2.0", "id": request_id, **response}
        sys.stdout.buffer.write(json.dumps(envelope, ensure_ascii=False).encode("utf-8") + b"\n")
        sys.stdout.buffer.flush()
