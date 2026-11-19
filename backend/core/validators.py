"""Validation helpers for user-controlled plain-text fields."""

import re

from django.core.exceptions import ValidationError


# SCMS stores these fields as plain text; it never needs user-supplied HTML.
# Any "<" that starts a tag, comment or declaration (even without a closing ">"),
# plus script-capable URI schemes.
UNSAFE_HTML = re.compile(
    r"<\s*/?\s*[a-z!?]|(?:javascript|vbscript)\s*:|data\s*:\s*text/html",
    re.IGNORECASE,
)


def validate_plain_text(value: str) -> str:
    """Reject HTML/script-style payloads before they enter the database."""
    if value and UNSAFE_HTML.search(value):
        raise ValidationError("HTML and script content are not permitted in this field.")
    return value
