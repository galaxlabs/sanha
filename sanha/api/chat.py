import frappe
import json
import requests
from frappe import _
from frappe.utils.password import get_decrypted_password
from difflib import SequenceMatcher

MODEL_MAP = {
    "GPT-4o": "gpt-4o",
    "GPT-4o Mini": "gpt-4o-mini",
    "GPT-3.5 Turbo": "gpt-3.5-turbo",
    "Claude 3 Haiku": "claude-3-haiku-20240307",
    "Claude 3 Sonnet": "claude-3-sonnet-20240229",
    # Also accept raw API names directly
    "gpt-4o": "gpt-4o",
    "gpt-4o-mini": "gpt-4o-mini",
    "gpt-3.5-turbo": "gpt-3.5-turbo",
    "claude-3-haiku-20240307": "claude-3-haiku-20240307",
    "claude-3-sonnet-20240229": "claude-3-sonnet-20240229",
}

ALLOWED_DOCTYPES = ["Query", "Client", "E-NUMBERS"]

def _get_user_filters():
    user = frappe.session.user
    roles = frappe.get_roles(user)
    # Admin/Evaluation/SB User see all data
    if any(r in roles for r in ["System Manager", "Administrator", "Evaluation", "SB User"]):
        return {}
    # Client user — only their own queries
    client_name = frappe.db.get_value("Client", {"owner": user}, "client_name")
    if client_name:
        return {"client_name": client_name}
    return {"owner": user}

def _similarity(a, b):
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

def _fuzzy_groups(items, threshold=0.55):
    checked = set()
    groups = []
    for i, item in enumerate(items):
        if i in checked:
            continue
        group = [item]
        checked.add(i)
        for j in range(i + 1, len(items)):
            if j in checked:
                continue
            if _similarity(item, items[j]) >= threshold:
                group.append(items[j])
                checked.add(j)
        if len(group) > 1:
            groups.append(group)
    return groups

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
    """Return grouped similar names + contact-based merge suggestions."""
    MAX_ITEMS = 50
    filters = _get_user_filters()
    queries = frappe.get_all("Query", filters=filters,
        fields=["supplier", "manufacturer", "raw_material", "manufacturer_contact", "supplier_contact"],
        limit_page_length=500)

    all_suppliers = sorted({q.supplier for q in queries if q.supplier})[:MAX_ITEMS]
    all_manufacturers = sorted({q.manufacturer for q in queries if q.manufacturer})[:MAX_ITEMS]
    all_raw_materials = sorted({q.raw_material for q in queries if q.raw_material})[:MAX_ITEMS]
    contact_map = {}
    for q in queries:
        if q.manufacturer_contact and q.manufacturer:
            contact_map.setdefault(q.manufacturer_contact.strip().lower(), set()).add(q.manufacturer)
        if q.supplier_contact and q.supplier:
            contact_map.setdefault(q.supplier_contact.strip().lower(), set()).add(q.supplier)

    return {
        "similar_suppliers": _fuzzy_groups(all_suppliers, 0.5)[:5],
        "similar_manufacturers": _fuzzy_groups(all_manufacturers, 0.5)[:5],
        "similar_raw_materials": _fuzzy_groups(all_raw_materials, 0.6)[:5],
        "same_contact_different_names": [
            {"contact": c, "names": sorted(n)}
            for c, n in contact_map.items() if len(n) > 1
        ][:5],
        "total_suppliers": len(all_suppliers),
        "total_manufacturers": len(all_manufacturers),
        "total_raw_materials": len(all_raw_materials),
    }

def _build_system_prompt(config, user_roles, context):
    role_desc = "You are a Client user — you can ONLY see and discuss your own queries and data. Do not reveal other clients' information."
    if "SB User" in user_roles:
        role_desc = "You are a Shariah Board user at SANHA. You can see all queries."
    elif "Evaluation" in user_roles:
        role_desc = "You are an Evaluation officer at SANHA. You can see all queries."
    elif "System Manager" in user_roles or "Administrator" in user_roles:
        role_desc = "You are an Administrator with full access to all SANHA data."

    extra = ""
    custom_prompt = (config.get("system_prompt") or "").strip()
    if custom_prompt:
        extra = f"\n\nAdditional user-provided instructions:\n{custom_prompt}"

    return f"""You are the SANHA Halal Query Assistant, an AI helper for the SANHA halal certification platform.

{role_desc}

You have access to the following database context to answer the user's question:
{json.dumps(context, indent=2, default=str)}

Guidelines:
- Use the context above to answer questions about queries, suppliers, manufacturers, raw materials, and data quality.
- If you find similar supplier/manufacturer names (e.g., "Alnor" and "Alnoor Sugar"), suggest standardization.
- If the user asks about queries, list them with their current status and ID.
- Be concise, professional, and helpful. Use bullet points for lists.
- If you don't have enough data, ask the user to be more specific.
- Do NOT fabricate data — only use what's in the context above.
- Address the user naturally (Assalam-o-Alaikum, etc.).{extra}"""

def _call_llm(config, messages):
    provider = (config.get("provider") or "Open AI").strip().lower()
    try:
        api_key = get_decrypted_password("AI Agent Config", "AI Agent Config", "api_key")
    except frappe.AuthenticationError:
        api_key = ""
    display_model = (config.get("model") or "gpt-4o-mini").strip()
    model = MODEL_MAP.get(display_model, display_model)

    if not api_key:
        return "AI Agent is not configured. Please set an API Key in Chat Agent Config (Settings → Chat Agent Config)."

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
        if "error" in data:
            return f"OpenAI error: {data['error'].get('message', str(data['error']))}"
        return data["choices"][0]["message"]["content"]
    except KeyError as e:
        frappe.log_error(f"OpenAI unexpected response: {resp.text[:500]}", "sanha_chat")
        return f"Unexpected response from AI provider. Check your API key and model settings."
    except Exception as e:
        frappe.log_error(f"OpenAI call failed: {e}", "sanha_chat")
        return f"Could not reach AI provider: {str(e)}"

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
        if "error" in data:
            return f"Claude error: {data['error'].get('message', str(data['error']))}"
        return data["content"][0]["text"]
    except KeyError as e:
        frappe.log_error(f"Claude unexpected response: {resp.text[:500]}", "sanha_chat")
        return f"Unexpected response from AI provider. Check your API key and model settings."
    except Exception as e:
        frappe.log_error(f"Claude call failed: {e}", "sanha_chat")
        return f"Could not reach AI provider: {str(e)}"

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
        import traceback
        error_tb = traceback.format_exc()
        frappe.log_error(f"sanha_chat: {e}\n{error_tb}")
        return {"reply": "An error occurred. Please try again.", "intent": "error"}
