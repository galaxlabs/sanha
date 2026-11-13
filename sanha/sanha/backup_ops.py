import os

import frappe

from frappe.integrations.doctype.google_drive.google_drive import (
    get_absolute_path,
    get_google_drive_object,
    upload_system_backup_to_google_drive,
)
from frappe.integrations.offsite_backup_utils import get_latest_backup_file


def _list_files(drive, folder_id):
    files = []
    page_token = None
    query = f"'{folder_id}' in parents and trashed = false"

    while True:
        page = (
            drive.files()
            .list(
                q=query,
                fields="nextPageToken,files(id,name,size,createdTime)",
                pageSize=1000,
                pageToken=page_token,
            )
            .execute()
        )
        files.extend(page.get("files", []))
        page_token = page.get("nextPageToken")
        if not page_token:
            return files


def _latest_local_files(with_files):
    paths = get_latest_backup_file(with_files=with_files)
    return [get_absolute_path(path) for path in paths if path]


def run():
    """Upload one fresh full set, verify it, then remove older remote sets."""
    drive, account = get_google_drive_object()
    before_ids = {item["id"] for item in _list_files(drive, account.backup_folder_id)}

    upload_system_backup_to_google_drive()

    drive, account = get_google_drive_object()
    remote_files = _list_files(drive, account.backup_folder_id)
    uploaded = [item for item in remote_files if item["id"] not in before_ids]
    expected_paths = _latest_local_files(bool(account.file_backup))
    keep_ids = set()
    missing = []

    for path in expected_paths:
        name = os.path.basename(path)
        size = str(os.path.getsize(path))
        matches = [
            item
            for item in uploaded
            if item.get("name") == name and item.get("size") == size
        ]
        if not matches:
            missing.append(name)
            continue
        keep_ids.add(max(matches, key=lambda item: item.get("createdTime", ""))["id"])

    if missing or len(keep_ids) != len(expected_paths):
        raise RuntimeError(
            "Google Drive backup verification failed; missing files: "
            + ", ".join(missing or ["duplicate or unmatched backup files"])
        )

    deleted = 0
    for item in remote_files:
        if item["id"] not in keep_ids:
            drive.files().delete(fileId=item["id"]).execute()
            deleted += 1

    result = {
        "uploaded_files": len(keep_ids),
        "deleted_old_files": deleted,
        "retained_remote_sets": 1,
    }
    print(result)
    return result


def migrate_to_single_daily():
    """Create a clean folder while preserving the newest old full backup until verified."""
    drive, account = get_google_drive_object()
    old_folder_id = account.backup_folder_id
    old_files = _list_files(drive, old_folder_id)
    private_files = sorted(
        [item for item in old_files if "private-files" in item.get("name", "")],
        key=lambda item: item.get("createdTime", ""),
    )

    # Free enough quota for a replacement while retaining the newest full archive.
    for item in private_files[:-1]:
        drive.files().delete(fileId=item["id"]).execute()

    new_folder = (
        drive.files()
        .create(
            body={
                "name": account.backup_folder_name,
                "mimeType": "application/vnd.google-apps.folder",
            },
            fields="id",
        )
        .execute()
    )
    new_folder_id = new_folder["id"]
    frappe.db.set_single_value("Google Drive", "backup_folder_id", new_folder_id)
    frappe.db.commit()

    try:
        result = run()
    except Exception:
        frappe.db.set_single_value("Google Drive", "backup_folder_id", old_folder_id)
        frappe.db.commit()
        drive.files().delete(fileId=new_folder_id).execute()
        raise

    drive.files().delete(fileId=old_folder_id).execute()
    result["migration_complete"] = True
    print(result)
    return result
