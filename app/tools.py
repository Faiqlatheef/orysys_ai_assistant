"""Tools are deliberately small and permission-checked at the orchestration boundary."""
import ast, operator
from app.security import authorize
EMPLOYEES=[{"name":"Maya Perera","department":"Payments","role":"Service Owner"},{"name":"Ravi Silva","department":"Platform","role":"SRE Lead"}]
SERVICES=[{"name":"Payment Gateway","owner":"Payments","criticality":"Tier 1"},{"name":"Customer Portal","owner":"Digital","criticality":"Tier 2"}]
INCIDENTS=[{"id":"INC-2041","service":"Payment Gateway","summary":"Timeout spike after upstream certificate rotation","status":"resolved"},{"id":"INC-2050","service":"Payment Gateway","summary":"Retry storm during database failover","status":"resolved"}]

def call_tool(role: str, name: str, args: dict):
    authorize(role,name)
    if name=="mcp_employee_lookup":
        q=str(args.get("query",""))[:100].lower(); terms=[t for t in q.split() if len(t)>2 and t not in {"who","owns","the","service","please","find"}]; return [x for x in EMPLOYEES if any(t in x["name"].lower() or t in x["department"].lower() for t in terms)]
    if name=="mcp_service_catalog":
        q=str(args.get("query",""))[:100].lower(); terms=[t for t in q.split() if len(t)>2 and t not in {"who","owns","the","service","please","find"}]; return [x for x in SERVICES if any(t in x["name"].lower() or t in x["owner"].lower() for t in terms)]
    if name=="mcp_incident_lookup":
        q=str(args.get("query",""))[:100].lower(); return [x for x in INCIDENTS if q in str(x).lower()]
    if name=="python_analysis":
        values=args.get("values",[])
        if not isinstance(values,list) or len(values)>1000 or not all(isinstance(x,(int,float)) for x in values): raise ValueError("values must be up to 1000 numeric values")
        if not values: return {"count":0,"mean":None,"min":None,"max":None}
        return {"count":len(values),"mean":sum(values)/len(values),"min":min(values),"max":max(values)}
    if name=="admin_stats": return {"document_count":4,"service_count":len(SERVICES),"incident_count":len(INCIDENTS)}
    raise ValueError(f"Unknown tool: {name}")
