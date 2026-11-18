"""Validation helpers for user-controlled plain-text fields."""

import re

from django.core.exceptions import ValidationError


# SCMS stores these fields as plain text; it never needs user-supplied HTML.
UNSAFE_HTML = re.compile(r"<\s*/?\s*[a-z!][^>]*>|javascript\s*:", re.IGNORECASE)


def validate_plain_text(value: str) -> str:
    """Reject HTML/script-style payloads before they enter the database."""
    if value and UNSAFE_HTML.search(value):
        raise ValidationError("HTML and script content are not permitted in this field.")
    return value
