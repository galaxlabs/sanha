import re
from urllib.parse import parse_qs, urlparse

import frappe
from frappe.utils import cint
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


ADMIN_ROLES = {"Admin", "System Manager", "Administrator"}


def canonical_playlist_url(url):
    parsed = urlparse((url or "").strip())
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"} or parsed.username or parsed.password:
        frappe.throw("Enter a YouTube playlist URL containing list=.")
    playlist_id = parse_qs(parsed.query).get("list", [""])[0]
    if not re.fullmatch(r"[A-Za-z0-9_-]{10,128}", playlist_id):
        frappe.throw("The YouTube playlist ID is missing or invalid.")
    return f"https://www.youtube.com/playlist?list={playlist_id}"


def get_playlist_videos(url, start=0, page_size=50):
    if frappe.session.user == "Guest":
        frappe.throw("Login required.", frappe.PermissionError)
    normalized = canonical_playlist_url(url)
    # Only published, readable records are available to Clients. Admin can preview a URL.
    if not ADMIN_ROLES.intersection(frappe.get_roles()):
        published = frappe.get_list("Learning Playlist", filters={"published": 1}, fields=["youtube_url"], limit_page_length=0)
        if not any(canonical_playlist_url(row.youtube_url) == normalized for row in published):
            frappe.throw("This playlist is not published for your account.", frappe.PermissionError)
    start, page_size = max(0, cint(start)), min(100, max(1, cint(page_size)))
    cache_key = f"sanha:learning:{normalized}:{start}:{page_size}"
    cached = frappe.cache().get_value(cache_key)
    if cached is not None:
        return cached
    try:
        with YoutubeDL({
            "extract_flat": True, "skip_download": True, "quiet": True, "no_warnings": True,
            "playliststart": start + 1, "playlistend": start + page_size + 1,
            "socket_timeout": 15, "retries": 1, "extractor_retries": 1,
        }) as extractor:
            result = extractor.extract_info(normalized, download=False)
    except DownloadError:
        frappe.throw("YouTube could not load this playlist. Check that it is public or unlisted, then retry.")
    entries = (result or {}).get("entries") or []
    has_more = len(entries) > page_size
    videos = []
    for entry in entries[:page_size]:
        if not entry or not re.fullmatch(r"[\w-]{11}", entry.get("id") or ""):
            continue
        if entry.get("availability") in {"private", "premium_only", "subscriber_only", "needs_auth"} or entry.get("title") in {"[Private video]", "[Deleted video]"}:
            continue
        videos.append({
            "id": entry["id"], "title": entry.get("title") or "Untitled video",
            "description": entry.get("description") or "", "channel": entry.get("channel") or entry.get("uploader") or "",
            "duration": entry.get("duration"), "position": start + len(videos) + 1,
            "thumbnail": f"https://i.ytimg.com/vi/{entry['id']}/hqdefault.jpg",
        })
    response = {"videos": videos, "has_more": has_more, "next_start": start + page_size if has_more else None}
    frappe.cache().set_value(cache_key, response, expires_in_sec=300)
    return response
