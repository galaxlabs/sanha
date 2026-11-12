"""Deterministic message drafts for clients. Pure text only: nothing is sent or executed here."""

import re

PURPOSES = {
    "request_info": "معلومات کی درخواست",
    "send_document": "دستاویز بھیجنے کی اطلاع",
    "status_question": "Query کی حالت کے بارے میں سوال",
}

RECIPIENTS = {
    "evaluation": "SANHA ایوالیوایشن",
    "certificate_manager": "سرٹیفکیٹ منیجر",
    "shariah": "شریعہ ممبر",
    "client_contact": "کلائنٹ کا اپنا رابطہ",
}

MAX_DETAILS = 1000
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def clean_details(value):
    text = _CONTROL.sub("", str(value or "")).strip()
    return text[:MAX_DETAILS]


def build_draft(purpose, recipient, query_name, raw_material, details="", sender_name=""):
    if purpose not in PURPOSES:
        raise ValueError("unknown purpose")
    if recipient not in RECIPIENTS:
        raise ValueError("unknown recipient")
    details = clean_details(details)
    to = RECIPIENTS[recipient]
    sender = (sender_name or "").strip() or "[آپ کا نام]"
    material = (raw_material or "").strip() or "[raw material]"
    subject = f"Query {query_name} - {material}"
    if purpose == "request_info":
        intro = "براہِ کرم درج ذیل معلومات فراہم کریں:"
        ask = details or "[مطلوبہ معلومات یہاں لکھیں]"
    elif purpose == "send_document":
        intro = "اس Query کے ساتھ درج ذیل دستاویز منسلک کی جا رہی ہے:"
        ask = details or "[دستاویز کی تفصیل یہاں لکھیں]"
    else:
        intro = "اس Query کی موجودہ حالت اور اگلے قدم کے بارے میں معلومات درکار ہیں:"
        ask = details or "[سوال یہاں لکھیں]"
    body = (
        f"محترم {to}،\n\n"
        f"Query {query_name} ({material}) کے سلسلے میں:\n\n"
        f"{intro}\n{ask}\n\n"
        "شکریہ۔\n"
        f"{sender}"
    )
    return {"subject": subject, "body": body, "to_label": to}
