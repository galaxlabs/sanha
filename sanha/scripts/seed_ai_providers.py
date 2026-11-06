from uuid import uuid4

import frappe

PROFILE_TITLE = "OpenAI GPT-4o (text)"


def run():
    frappe.set_user("Administrator")
    legacy = frappe.get_single("AI Agent Config")
    key = legacy.get_password("api_key", raise_exception=False)

    name = frappe.db.get_value("AI Provider Profile", {"title": PROFILE_TITLE}, "name")
    doc = frappe.get_doc("AI Provider Profile", name) if name else frappe.new_doc("AI Provider Profile")
    doc.update({
        "title": PROFILE_TITLE,
        "provider": "OpenAI",
        "model": "gpt-4o",
        "enabled": 1 if key else 0,
        "use_for_text": 1,
        "use_for_vision": 0,
        "priority": 10,
        "max_output_tokens": 2048,
        "daily_token_budget": 50000,
        "setup_note": "Seeded from AI Agent Config (GPT-4o). Key copied server-side; rotate in the app if needed.",
    })
    if key and doc.get_password("api_key", raise_exception=False) != key:
        doc.api_key = key
        doc.credential_revision = uuid4().hex
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"name": doc.name, "enabled": doc.enabled, "has_key": bool(key), "model": doc.model}
