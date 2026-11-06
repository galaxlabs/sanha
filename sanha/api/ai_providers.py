"""Server-only provider credentials; task routing, cache, fallback and token accounting."""
import hashlib
import json
import re

import frappe
import requests
from frappe.utils import cint, now, today

PROVIDERS = {"OpenAI", "Claude", "Gemini", "DeepSeek"}
EDITABLE = {"title", "provider", "model", "api_key", "enabled", "use_for_text", "use_for_vision", "priority", "max_output_tokens", "daily_token_budget"}
SAFE_FIELDS = ["name", "title", "provider", "model", "enabled", "use_for_text", "use_for_vision", "priority", "max_output_tokens", "daily_token_budget", "credential_revision", "legacy_imported", "setup_note", "last_test_status", "last_tested"]


class ProviderError(Exception):
    def __init__(self, reason, status=None):
        self.reason, self.status = reason, status
        super().__init__(reason)


def require_admin():
    if frappe.session.user != "Administrator" and not {"Admin", "System Manager"}.intersection(frappe.get_roles()):
        frappe.throw("Administrator access required.", frappe.PermissionError)


def model_compatible(provider, model):
    checks = {"OpenAI": r"(?:gpt-|chatgpt-|o[134](?:-|$))", "Claude": r"claude-", "Gemini": r"gemini-", "DeepSeek": r"deepseek-"}
    if provider not in PROVIDERS or not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", model) or not re.match(checks.get(provider, r"(?!)"), model):
        return False
    return not (provider == "OpenAI" and any(word in model.lower() for word in ("audio", "realtime", "image", "transcribe", "search", "tts")))


def validate_model(provider, model):
    if not model_compatible(provider, model):
        frappe.throw("Choose a model ID belonging to the selected provider. GPT models cannot be used with Claude.")


def profiles_available():
    return bool(frappe.db.exists("DocType", "AI Provider Profile"))


def ready_profiles(task="review"):
    if not profiles_available():
        return []
    flag = "use_for_vision" if task == "vision" else "use_for_text"
    rows = frappe.get_all("AI Provider Profile", filters={"enabled": 1, flag: 1}, pluck="name", order_by="priority asc, name asc", limit_page_length=0)
    result = []
    for name in rows:
        doc = frappe.get_doc("AI Provider Profile", name)
        try:
            if not model_compatible(doc.provider, doc.model): continue
            if doc.get_password("api_key", raise_exception=False) and cint(doc.daily_token_budget) > 0:
                result.append(doc)
        except Exception:
            continue
    return result


def routing_signature(task=None):
    if not profiles_available():
        return "no-provider-profiles"
    filters = {"enabled": 1}
    if task:
        filters["use_for_vision" if task == "vision" else "use_for_text"] = 1
    rows = frappe.get_all("AI Provider Profile", filters=filters, fields=["name", "provider", "model", "enabled", "use_for_text", "use_for_vision", "priority", "max_output_tokens", "credential_revision"], order_by="name asc", limit_page_length=0)
    return hashlib.sha256(json.dumps(rows, default=str, sort_keys=True).encode()).hexdigest()


def day_usage(name):
    rows = frappe.db.sql("SELECT COALESCE(SUM(total_tokens),0) AS tokens, COUNT(*) AS calls, COALESCE(SUM(estimated),0) AS estimated_calls FROM `tabAI Usage Log` WHERE profile=%s AND usage_date=%s", (name, today()), as_dict=True)
    return rows[0] if rows else {"tokens": 0, "calls": 0, "estimated_calls": 0}


def budget_signature():
    rows = frappe.get_all("AI Provider Profile", filters={"enabled": 1}, fields=["name", "daily_token_budget"], order_by="name asc", limit_page_length=0) if profiles_available() else []
    return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()


@frappe.whitelist()
def list_profiles():
    require_admin()
    result = []
    for row in frappe.get_all("AI Provider Profile", fields=SAFE_FIELDS, order_by="priority asc, name asc", limit_page_length=0):
        doc = frappe.get_doc("AI Provider Profile", row.name)
        row["key_configured"] = bool(doc.get_password("api_key", raise_exception=False))
        row["usage"] = day_usage(row.name)
        result.append(row)
    return result


@frappe.whitelist(methods=["POST"])
def save_profile(data, name=None):
    require_admin()
    data = frappe.parse_json(data)
    if not isinstance(data, dict) or set(data) - EDITABLE:
        frappe.throw("Unsupported provider fields.")
    doc = frappe.get_doc("AI Provider Profile", name) if name else frappe.new_doc("AI Provider Profile")
    for field, value in data.items():
        if field == "api_key" and (not value or value == "********"):
            continue
        doc.set(field, value)
    doc.save(ignore_permissions=True)
    return {"name": doc.name}


@frappe.whitelist(methods=["POST"])
def delete_profile(name):
    require_admin()
    # Keep audit references; disabling is reversible and does not delete credentials/logs.
    frappe.db.set_value("AI Provider Profile", name, "enabled", 0)
    return {"disabled": True}


def bootstrap_legacy():
    """Idempotently preserve the legacy secret in a disabled, unverified profile."""
    require_admin()
    frappe.db.add_index("AI Usage Log", ["profile", "usage_date"], index_name="profile_usage_day")
    if not frappe.db.sql("SELECT value FROM `tabSingles` WHERE doctype=%s AND field=%s", ("AI Agent Config", "auto_staff_review")):
        frappe.db.set_single_value("AI Agent Config", "auto_staff_review", 1)
    found = frappe.db.get_value("AI Provider Profile", {"legacy_imported": 1}, "name")
    if found:
        return {"preserved": True, "name": found}
    legacy = frappe.get_single("AI Agent Config")
    key = legacy.get_password("api_key", raise_exception=False)
    if not key:
        return {"preserved": False, "reason": "no-legacy-key"}
    provider = {"Open AI": "OpenAI", "Claude": "Claude"}.get(legacy.provider, "OpenAI")
    model = {"GPT-4o": "gpt-4o", "GPT-4o Mini": "gpt-4o-mini", "GPT-3.5 Turbo": "gpt-3.5-turbo", "Claude 3 Haiku": "claude-3-haiku-20240307", "Claude 3 Sonnet": "claude-3-sonnet-20240229"}.get(legacy.model, legacy.model or "")
    if not model_compatible(provider, model):
        model = ""
    doc = frappe.get_doc({"doctype": "AI Provider Profile", "title": "Preserved legacy connection", "provider": provider, "model": model, "api_key": key, "enabled": 0, "use_for_text": 1, "use_for_vision": 0, "priority": 10, "max_output_tokens": 2048, "daily_token_budget": 50000, "legacy_imported": 1, "setup_note": f"Original provider/model: {legacy.provider} / {legacy.model}. Key preserved; select a compatible model, test and enable this profile."})
    doc.insert(ignore_permissions=True)
    return {"preserved": True, "name": doc.name, "enabled": False, "model_needs_selection": not bool(model)}


def key_for(doc):
    key = doc.get_password("api_key", raise_exception=False)
    if not key:
        raise ProviderError("missing_key")
    brand = "Claude" if key.startswith("sk-ant-") else "Gemini" if key.startswith("AIza") else "OpenAI" if key.startswith(("sk-proj-", "sk-svcacct-")) else None
    if brand and brand != doc.provider:
        raise ProviderError("key_provider_mismatch")
    return key


def endpoint(doc):
    key = key_for(doc)
    if doc.provider == "OpenAI":
        return "https://api.openai.com/v1", {"Authorization": "Bearer " + key}
    if doc.provider == "Claude":
        return "https://api.anthropic.com/v1", {"x-api-key": key, "anthropic-version": "2023-06-01"}
    if doc.provider == "Gemini":
        return "https://generativelanguage.googleapis.com/v1beta", {"x-goog-api-key": key}
    if doc.provider == "DeepSeek":
        return "https://api.deepseek.com", {"Authorization": "Bearer " + key}
    raise ProviderError("unsupported_provider")


@frappe.whitelist(methods=["POST"])
def test_connection(name):
    require_admin()
    doc = frappe.get_doc("AI Provider Profile", name)
    models = []
    status = "connection_error"
    try:
        base, headers = endpoint(doc)
        params = {"pageSize": 1000} if doc.provider == "Gemini" else {"limit": 1000} if doc.provider == "Claude" else {}
        for _ in range(10):
            response = requests.get(base + "/models", headers=headers, params=params, timeout=20)
            if response.status_code != 200:
                raise ProviderError("authentication_failed" if response.status_code in {401, 403} else "models_request_failed")
            body = response.json()
            records = body.get("models", []) if doc.provider == "Gemini" else body.get("data", [])
            for model in records:
                if model.get("lifecycle") == "retired":
                    continue
                if model.get("shutdown_date") and model["shutdown_date"] <= today():
                    continue
                if doc.provider == "Gemini" and "generateContent" not in model.get("supportedGenerationMethods", []):
                    continue
                identifier = (model.get("id") or model.get("name") or "").removeprefix("models/")
                if not model_compatible(doc.provider, identifier): continue
                models.append(identifier)
            if doc.provider == "Gemini" and body.get("nextPageToken"):
                params["pageToken"] = body["nextPageToken"]
            elif doc.provider == "Claude" and body.get("has_more") and body.get("last_id"):
                params["after_id"] = body["last_id"]
            else:
                break
        models = sorted(set(models))
        status = "authenticated_model_listed" if doc.model in models else "authenticated_select_available_model"
    except ProviderError as error:
        status = error.reason
    except Exception:
        status = "connection_error"
    frappe.db.set_value("AI Provider Profile", name, {"last_test_status": status, "last_tested": now()}, update_modified=False)
    return {"status": status, "models": models, "generation_calls": 0}


def estimate_tokens(messages):
    text, images = 0, 0
    for message in messages:
        content = message.get("content", "")
        if isinstance(content, str):
            text += len(content.encode("utf-8"))
        else:
            for part in content:
                if part.get("type") == "image_url": images += 1
                else: text += len(part.get("text", "").encode("utf-8"))
    # Conservative reservation, reconciled to provider-reported usage on success.
    return max(1, text) + len(messages) * 200 + images * 10000


def reserve(doc, amount, task, request_hash, reference):
    """AI entry points are read-only jobs/RPCs; commit only technical usage here.

    No provider calls are made inside business document validation/save hooks.
    An advisory lock keeps reservations from overrunning a profile across workers.
    """
    lock = "sanha-ai-" + hashlib.sha256((doc.name + today()).encode()).hexdigest()[:40]
    # Start a fresh snapshot before the advisory lock; previous read snapshots
    # must not hide another worker's committed usage reservation.
    frappe.db.commit()
    if frappe.db.sql("SELECT GET_LOCK(%s,5)", (lock,))[0][0] != 1:
        raise ProviderError("budget_busy")
    try:
        used = int(day_usage(doc.name)["tokens"])
        if amount > cint(doc.daily_token_budget):
            raise ProviderError("request_exceeds_profile_budget")
        if used + amount > cint(doc.daily_token_budget):
            raise ProviderError("daily_token_budget_reached")
        entry = frappe.get_doc({"doctype": "AI Usage Log", "profile": doc.name, "model": doc.model, "task": task, "usage_date": today(), "actor": frappe.session.user, "query_reference": reference, "status": "Reserved", "total_tokens": amount, "estimated": 1, "request_hash": request_hash})
        entry.insert(ignore_permissions=True)
        frappe.db.commit()
        return entry.name
    finally:
        frappe.db.sql("SELECT RELEASE_LOCK(%s)", (lock,))


def finish(name, status, usage=None):
    values = {"status": status}
    if usage is not None:
        values.update(input_tokens=usage[0], output_tokens=usage[1], total_tokens=sum(usage), estimated=0)
    frappe.db.set_value("AI Usage Log", name, values)
    frappe.db.commit()


def invoke(doc, messages, maximum):
    base, headers = endpoint(doc)
    if doc.provider in {"OpenAI", "DeepSeek"}:
        payload = {"model": doc.model, "messages": messages}
        if not re.match(r"(?:gpt-5|o[134])", doc.model):
            payload["temperature"] = 0.2
        payload["max_completion_tokens" if doc.provider == "OpenAI" and re.match(r"(?:gpt-5|o[134])", doc.model) else "max_tokens"] = maximum
        url = base + "/chat/completions"
    elif doc.provider == "Claude":
        content = []
        system = "\n".join(message["content"] for message in messages if message["role"] == "system")
        for message in messages:
            if message["role"] == "system": continue
            copied = dict(message)
            if isinstance(copied["content"], list):
                parts = []
                for part in copied["content"]:
                    if part.get("type") == "image_url":
                        header, data = part["image_url"]["url"].split(",", 1)
                        parts.append({"type": "image", "source": {"type": "base64", "media_type": header.split(":", 1)[1].split(";", 1)[0], "data": data}})
                    else: parts.append(part)
                copied["content"] = parts
            content.append(copied)
        payload = {"model": doc.model, "system": system, "messages": content, "max_tokens": maximum}
        url = base + "/messages"
    else:
        system, content = [], []
        for message in messages:
            if message["role"] == "system": system.append({"text": message["content"]}); continue
            parts = [{"text": message["content"]}] if isinstance(message["content"], str) else []
            if isinstance(message["content"], list):
                for part in message["content"]:
                    if part.get("type") == "image_url":
                        header, data = part["image_url"]["url"].split(",", 1)
                        parts.append({"inlineData": {"mimeType": header.split(":", 1)[1].split(";", 1)[0], "data": data}})
                    else: parts.append({"text": part.get("text", "")})
            content.append({"role": "model" if message["role"] == "assistant" else "user", "parts": parts})
        payload = {"contents": content, "systemInstruction": {"parts": system}, "generationConfig": {"maxOutputTokens": maximum}}
        url = base + "/models/" + doc.model + ":generateContent"
    response = requests.post(url, headers={**headers, "Content-Type": "application/json"}, json=payload, timeout=45)
    if response.status_code != 200:
        raise ProviderError("provider_rejected" if response.status_code < 500 and response.status_code != 429 else "provider_busy", response.status_code)
    body = response.json()
    if doc.provider == "Claude":
        text = "\n".join(part.get("text", "") for part in body.get("content", []) if part.get("type") == "text")
        raw = body.get("usage", {}); usage = (cint(raw.get("input_tokens")) + cint(raw.get("cache_creation_input_tokens")) + cint(raw.get("cache_read_input_tokens")), cint(raw.get("output_tokens"))) if raw else None
    elif doc.provider == "Gemini":
        candidates = body.get("candidates", [])
        text = "\n".join(part.get("text", "") for part in (candidates[0].get("content", {}).get("parts", []) if candidates else []) if not part.get("thought"))
        raw = body.get("usageMetadata", {}); usage = (cint(raw.get("promptTokenCount")), max(0, cint(raw.get("totalTokenCount")) - cint(raw.get("promptTokenCount")))) if raw else None
    else:
        text = body["choices"][0]["message"]["content"]
        raw = body.get("usage", {}); usage = (cint(raw.get("prompt_tokens")), cint(raw.get("completion_tokens"))) if raw else None
    if not isinstance(text, str) or not text.strip(): raise ProviderError("empty_model_output")
    return text, usage


def call(messages, task="review", reference=None):
    frappe.local.ai_last_cache_key = None
    from sanha.api.live_data import scope
    _, authorization = scope("Query")
    profiles = ready_profiles(task)
    if not profiles: raise ProviderError("no_enabled_compatible_provider")
    request_hash = hashlib.sha256(json.dumps(messages, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    routes = routing_signature(task)
    failures = []
    candidates = []
    for doc in profiles:
        cache_key = "ai-call:" + hashlib.sha256(f"{frappe.session.user}:{authorization}:{doc.name}:{doc.credential_revision}:{doc.model}:{doc.max_output_tokens}:{routes}:{task}:{request_hash}".encode()).hexdigest()
        candidates.append((doc, cache_key))
        cached = frappe.cache().get_value(cache_key)
        if cached:
            frappe.local.ai_last_cache_key = cache_key
            frappe.local.ai_last_call = {"provider": doc.provider, "model": doc.model, "cache_hit": True}
            return cached
    for doc, cache_key in candidates:
        maximum = max(128, min(cint(doc.max_output_tokens), 8192))
        entry = None
        try:
            key_for(doc)
            entry = reserve(doc, estimate_tokens(messages) + maximum, task, request_hash, reference)
            text, usage = invoke(doc, messages, maximum)
            finish(entry, "Success", usage)
            frappe.cache().set_value(cache_key, text, expires_in_sec=86400)
            frappe.local.ai_last_cache_key = cache_key
            frappe.local.ai_last_call = {"provider": doc.provider, "model": doc.model, "cache_hit": False, "usage_estimated": usage is None}
            return text
        except ProviderError as error:
            if entry: finish(entry, "Rejected" if error.status and error.status < 500 and error.status != 429 else "Unknown", (0, 0) if error.status and error.status < 500 and error.status != 429 else None)
            failures.append(error.reason)
        except Exception:
            if entry: finish(entry, "Unknown")
            failures.append("provider_request_failed")
    raise ProviderError("; ".join(dict.fromkeys(failures)) or "providers_unavailable")
