"""
Repair Query File rows that stayed attached to temporary new-query-* names.

Dry run:
    bench --site evaluation.sanha.org.pk execute sanha.scripts.query_file_relink.run

Apply safe relinks:
    bench --site evaluation.sanha.org.pk execute sanha.scripts.query_file_relink.run --kwargs "{'apply': 1}"
"""

import frappe


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _get_bad_file_docs():
    return frappe.db.sql(
        """
        select
            f.name,
            f.file_url,
            f.file_name,
            f.owner,
            f.attached_to_name,
            f.attached_to_field
        from `tabFile` f
        left join `tabQuery` q on q.name = f.attached_to_name
        where f.attached_to_doctype = 'Query'
          and f.attached_to_name like 'new-query-%'
          and q.name is null
        order by f.modified desc
        """,
        as_dict=True,
    )


def _get_candidates(file_url):
    return frappe.db.sql(
        """
        select
            d.parent as query,
            d.name as child_row,
            d.documents,
            q.owner as query_owner,
            q.client_name
        from `tabDocuments` d
        join `tabQuery` q on q.name = d.parent
        where d.parenttype = 'Query'
          and d.attachment = %s
        order by q.modified desc
        """,
        file_url,
        as_dict=True,
    )


def _choose_candidate(file_doc, candidates):
    if not candidates:
        return None, "no_child_row"

    owner_matches = [c for c in candidates if c.query_owner == file_doc.owner]
    if len(owner_matches) == 1:
        return owner_matches[0], "owner_match"

    if len(candidates) == 1:
        return candidates[0], "single_match"

    return None, "ambiguous"


def run(apply=0, limit=0):
    """
    Relink only rows with one safe target.

    This does not move files on disk and does not edit child Documents rows.
    It only updates tabFile.attached_to_name / attached_to_field for File docs
    that point to missing temporary new-query-* names.
    """

    apply_changes = _as_bool(apply)
    limit = int(limit or 0)

    bad_files = _get_bad_file_docs()
    if limit:
        bad_files = bad_files[:limit]

    result = {
        "apply": apply_changes,
        "checked": len(bad_files),
        "safe_to_relink": 0,
        "relinked": 0,
        "no_child_row": 0,
        "ambiguous": 0,
        "samples": {
            "safe": [],
            "no_child_row": [],
            "ambiguous": [],
        },
    }

    for file_doc in bad_files:
        candidates = _get_candidates(file_doc.file_url)
        chosen, reason = _choose_candidate(file_doc, candidates)

        if chosen:
            result["safe_to_relink"] += 1
            if len(result["samples"]["safe"]) < 20:
                result["samples"]["safe"].append(
                    {
                        "file": file_doc.name,
                        "file_url": file_doc.file_url,
                        "from": file_doc.attached_to_name,
                        "to": chosen.query,
                        "child_row": chosen.child_row,
                        "reason": reason,
                    }
                )

            if apply_changes:
                frappe.db.set_value(
                    "File",
                    file_doc.name,
                    {
                        "attached_to_name": chosen.query,
                        "attached_to_field": "attachment",
                    },
                    update_modified=False,
                )
                result["relinked"] += 1
            continue

        result[reason] += 1
        if len(result["samples"][reason]) < 20:
            result["samples"][reason].append(
                {
                    "file": file_doc.name,
                    "file_url": file_doc.file_url,
                    "from": file_doc.attached_to_name,
                    "candidate_count": len(candidates),
                    "candidate_queries": [c.query for c in candidates[:10]],
                }
            )

    if apply_changes:
        frappe.db.commit()

    return result
