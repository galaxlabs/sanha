# sanha/api/client_api.py
from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import nowdate, add_days, getdate

PARENT_DTYPE = "Client"

# Only parent fields (no child tables). Adjust if you add/remove fields later.
PARENT_FIELDS = [
    "name", "client_name", "contact_no", "telephone",
    "email", "business_name", "client_code", "contact_person",
    "certified_since", "certified_expiry", "ext", "status",
    "address_type", "address", "region", "city",
    "standards", "is_active", "scope", "products", "category",
    # meta fields
    "owner", "creation", "modified", "modified_by", "docstatus"
]

def _status_from_days(days_left: int | None) -> str:
    if days_left is None:
        return "Unknown"
    if days_left < 0:
        return "Expired"
    if days_left < 30:
        return "Expiring"
    if days_left < 65:
        return "Expiring Soon"
    return "Valid"

@frappe.whitelist()
def expiring_clients(
    days: int = 65,
    include_expired: int | bool = 0,
    fields: list[str] | None = None,
    order_by: str = "certified_expiry asc",
    limit: int = 1000,
    start: int = 0,
    q: str | None = None,
    extra_filters: dict | None = None,
) -> list[dict]:
    """Return only parent fields for Client where certified_expiry <= today + days.
    - No child doctypes are fetched.
    - Adds `days_left` and `status_calc` to each row.
    - `include_expired=0` removes already expired rows.
    - `q` does a lightweight OR-search across key fields.
    - `extra_filters` is ANDed with the base filter.
    """
    frappe.only_for(("System Manager", "Admin", "Certificate Manager", "Client"), _("Not permitted"))

    try:
        days = int(days)
    except Exception:
        days = 65

    try:
        limit = max(1, min(int(limit), 1000))
    except Exception:
        limit = 1000

    try:
        start = max(0, int(start))
    except Exception:
        start = 0

    today = nowdate()                  # "YYYY-MM-DD"
    within = add_days(today, days)

    base_filters = {"certified_expiry": ("<=", within)}
    if extra_filters and isinstance(extra_filters, dict):
        base_filters.update(extra_filters)

    or_filters = None
    if q:
        like = f"%{q}%"
        or_filters = [
            ["client_name", "like", like],
            ["client_code", "like", like],
            ["email", "like", like],
            ["business_name", "like", like],
            ["city", "like", like],
        ]

    selected_fields = fields if fields else PARENT_FIELDS

    rows = frappe.get_all(
        PARENT_DTYPE,
        fields=selected_fields,
        filters=base_filters,
        or_filters=or_filters,
        order_by=order_by,
        start=start,
        page_length=limit,
        as_list=False,
        ignore_permissions=False,
    )

    t = getdate(today)
    out: list[dict] = []
    for r in rows:
        expiry = r.get("certified_expiry")
        days_left = (getdate(expiry) - t).days if expiry else None

        # Respect include_expired switch
        if not int(include_expired or 0) and (days_left is None or days_left < 0):
            continue

        d = dict(r)  # parent-only row
        d["days_left"] = days_left
        d["status_calc"] = _status_from_days(days_left)
        # Optional: convenience merged status
        d["status_final"] = (str(d.get("status") or "").strip()) or d["status_calc"]

        out.append(d)

    return out
