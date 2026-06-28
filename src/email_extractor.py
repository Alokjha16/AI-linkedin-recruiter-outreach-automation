"""
email_extractor.py - Email Extraction Module
"""

import re
import logging
from typing import List, Set

logger = logging.getLogger(__name__)

EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

EXCLUDED_DOMAINS = {
    "example.com",
    "test.com",
    "linkedin.com",
    "noreply.com",
    "placeholder.com",
    "thegaogroup.com",
}

EXCLUDED_EMAILS = {
    "noreply@linkedin.com",
    "notifications@linkedin.com",
    "security@linkedin.com",
}

BLOCKED_EMAIL_KEYWORDS = [
    "hire-bangladesh",
    "hire-pakistan",
    "hire-india",
    "bangladesh",
    "pakistan",
    "noreply",
    "no-reply",
    "donotreply",
]


def extract_emails(text: str) -> List[str]:
    if not text or not str(text).strip():
        return []

    text = str(text)
    emails: Set[str] = set()

    for email in EMAIL_PATTERN.findall(text):
        cleaned = _clean_email(email)
        if cleaned and _is_valid_email(cleaned):
            emails.add(cleaned)

    normalized_text = _normalize_obfuscated_text(text)

    for email in EMAIL_PATTERN.findall(normalized_text):
        cleaned = _clean_email(email)
        if cleaned and _is_valid_email(cleaned):
            emails.add(cleaned)

    return sorted(emails)


def _normalize_obfuscated_text(text: str) -> str:
    text = str(text)

    text = re.sub(r"\s*\[\s*at\s*\]\s*", "@", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*\(\s*at\s*\)\s*", "@", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+\bat\b\s+", "@", text, flags=re.IGNORECASE)

    text = re.sub(r"\s*\[\s*dot\s*\]\s*", ".", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*\(\s*dot\s*\)\s*", ".", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+\bdot\b\s+", ".", text, flags=re.IGNORECASE)

    return text


def _clean_email(email: str) -> str:
    email = str(email).strip().lower()
    email = email.replace("mailto:", "")
    email = email.rstrip(".,;:!?)>]}'\"")
    email = email.lstrip("([{<'\"")
    return email


def _is_valid_email(email: str) -> bool:
    email_lower = email.lower()

    if not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email):
        return False

    if email_lower in EXCLUDED_EMAILS:
        return False

    for keyword in BLOCKED_EMAIL_KEYWORDS:
        if keyword in email_lower:
            return False

    domain = email_lower.split("@")[-1]

    if domain in EXCLUDED_DOMAINS:
        return False

    if "." not in domain:
        return False

    return True


def extract_emails_batch(texts: List[str]) -> List[str]:
    all_emails: Set[str] = set()

    for text in texts:
        all_emails.update(extract_emails(text))

    return sorted(all_emails)