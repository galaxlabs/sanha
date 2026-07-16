import frappe
import json
import requests
from frappe import _

ALLOWED_DOCTYPES = ["Query", "Client", "E-NUMBERS"]

def _get_user_filters():
    user = frappe.session.user
    roles = frappe.get_roles(user)
    if "System Manager" in roles or "Administrator" in roles:
        return {}
    client_name = frappe.db.get_value("Client", {"owner": user}, "client_name")
    if client_name:
        return {"client_name": client_name}
    return {"owner": user}

def _get_query_context(search_term=None, limit=10):
    filters = _get_user_filters()
    if search_term:
        search = f"%{search_term}%"
        filters["raw_material"] = ["like", search]
    return frappe.get_all(
        "Query",
        filters=filters,
        fields=["name", "raw_material", "supplier", "manufacturer",
                "workflow_state", "client_name", "query_types", "creation"],
        order_by="creation desc",
        limit=limit,
    )

def _get_data_quality_context():
    filters = _get_user_filters()
    queries = frappe.get_all("Query", filters=filters,
        fields=["supplier", "manufacturer", "raw_material", "manufacturer_contact"])
    suppliers, manufacturers, materials = {}, {}, {}
    for q in queries:
        if q.supplier:
            suppliers.setdefault(q.supplier.lower().strip(), set()).add(q.supplier)
        if q.manufacturer:
            manufacturers.setdefault(q.manufacturer.lower().strip(), set()).add(q.manufacturer)
        if q.raw_material:
            materials.setdefault(q.raw_material.lower().strip(), set()).add(q.raw_material)
    return {
        "supplier_variants": {k: list(v) for k, v in suppliers.items() if len(v) > 1},
        "manufacturer_variants": {k: list(v) for k, v in manufacturers.items() if len(v) > 1},
        "raw_material_variants": {k: list(v) for k, v in materials.items() if len(v) > 1},
    }

def _build_system_prompt(config, user_roles, context):
    role_desc = "You are a Client user — you can ONLY see your own queries and data."
    if "Evaluation" in user_roles:
        role_desc = "You are an Evaluation officer — you can see queries assigned for evaluation."
    elif "SB User" in user_roles:
        role_desc = "You are a Shariah Board user — you can see queries submitted to SB."
    elif "System Manager" in user_roles or "Administrator" in user_roles:
        role_desc = "You are an Administrator — you have full access to all data."

    base = (config.get("system_prompt") or
        "You are a helpful assistant for SANHA (Sanha Halal Associates Pakistan).")
    return f"""{base}

{role_desc}

Current context from database:
{json.dumps(context, indent=2, default=str)}

Rules:
- Only answer based on the context provided above.
- Do NOT reveal other clients' data to a Client user.
- If you don't have enough context, say so and ask for more details.
- Be concise and professional.
"""

def _call_llm(config, messages):
    provider = (config.get("provider") or "Open AI").strip().lower()
    api_key = config.get("api_key") or ""
    model = config.get("model") or "gpt-4o-mini"

    if not api_key:
        return "AI Agent is not configured. Please set an API Key in Chat Agent Config."

    if "claude" in provider:
        return _call_claude(api_key, model, messages)
    return _call_openai(api_key, model, messages)

def _call_openai(api_key, model, messages):
    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": messages, "temperature": 0.3, "max_tokens": 1024},
            timeout=30,
        )
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        frappe.log_error(f"OpenAI call failed: {e}", "sanha_chat")
        return f"Sorry, I couldn't reach the AI provider: {str(e)}"

def _call_claude(api_key, model, messages):
    try:
        system_msg = messages[0]["content"] if messages[0]["role"] == "system" else ""
        conv = [m for m in messages if m["role"] != "system"]
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
            json={"model": model or "claude-3-haiku-20240307", "system": system_msg,
                  "messages": conv, "max_tokens": 1024, "temperature": 0.3},
            timeout=30,
        )
        data = resp.json()
        return data["content"][0]["text"]
    except Exception as e:
        frappe.log_error(f"Claude call failed: {e}", "sanha_chat")
        return f"Sorry, I couldn't reach the AI provider: {str(e)}"

def _detect_intent(message):
    msg = message.lower()
    if any(w in msg for w in ["similar", "duplicate", "variant", "spelling", "typo", "data quality"]):
        return "data_quality"
    if any(w in msg for w in ["query", "queries", "status", "submission", "raw material",
                               "manufacturer", "supplier", "find", "search", "lookup"]):
        return "query_lookup"
    return "general"

@frappe.whitelist()
def ask(message, history=None):
    try:
        user = frappe.session.user
        roles = frappe.get_roles(user)
        config = frappe.get_single("AI Agent Config").as_dict()

        intent = _detect_intent(message)
        context = {}

        if intent == "data_quality":
            context = _get_data_quality_context()
        elif intent == "query_lookup":
            search_terms = message.split()
            search = None
            for s in search_terms:
                if len(s) > 3 and s not in ("find", "search", "show", "get", "list", "query"):
                    search = s
                    break
            queries = _get_query_context(search_term=search)
            context = {"queries": queries[:5], "total_found": len(queries)}
        else:
            filters = _get_user_filters()
            total = frappe.db.count("Query", filters=filters)
            recent = _get_query_context(limit=3)
            context = {"total_queries": total, "recent_queries": recent}

        system_prompt = _build_system_prompt(config, roles, context)
        history_list = history or []
        messages = [{"role": "system", "content": system_prompt}]
        for h in history_list[-10:]:
            messages.append(h)
        messages.append({"role": "user", "content": message})

        reply = _call_llm(config, messages)

        return {"reply": reply, "intent": intent, "context_summary": len(str(context))}

    except Exception as e:
        frappe.log_error(f"Chat error for {frappe.session.user}: {e}", "sanha_chat")
        return {"reply": "An error occurred. Please try again.", "intent": "error"}
