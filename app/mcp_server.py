"""Minimal MCP-style JSON-RPC server over stdio is intentionally optional for this POC.
The same tools are exposed through the secure internal tool registry in app.tools.
For a full MCP client/server deployment, add the official MCP SDK and transport-specific auth.
"""
import json, sys
from app.tools import call_tool

def handle(msg):
    method=msg.get("method"); ident=msg.get("id")
    if method=="initialize": return {"jsonrpc":"2.0","id":ident,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"serverInfo":{"name":"orysys-demo-mcp","version":"0.1.0"}}}
    if method=="tools/list": return {"jsonrpc":"2.0","id":ident,"result":{"tools":[{"name":n,"description":d,"inputSchema":{"type":"object","properties":{"query":{"type":"string"}},"additionalProperties":False}} for n,d in [("mcp_employee_lookup","Search mock employee directory"),("mcp_service_catalog","Search service catalog"),("mcp_incident_lookup","Search incident records")]]}}
    if method=="tools/call":
        params=msg.get("params",{}); name=params.get("name"); args=params.get("arguments",{})
        # stdio server does not trust role from remote caller; administrator role is local demo only.
        try: result=call_tool("administrator",name,args); return {"jsonrpc":"2.0","id":ident,"result":{"content":[{"type":"text","text":json.dumps(result)}]}}
        except Exception as e: return {"jsonrpc":"2.0","id":ident,"error":{"code":-32000,"message":str(e)}}
    return {"jsonrpc":"2.0","id":ident,"error":{"code":-32601,"message":"Method not found"}}
if __name__=="__main__":
    for line in sys.stdin:
        try: print(json.dumps(handle(json.loads(line))),flush=True)
        except Exception: print(json.dumps({"jsonrpc":"2.0","id":None,"error":{"code":-32700,"message":"Parse error"}}),flush=True)
