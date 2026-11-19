"""Issue #5 (SCMS-F-008 / TC-LODGE-04): unsafe or incomplete input is rejected."""

import pytest
from accounts.models import User
from core.forms import ComplaintForm, RegistrationForm
from core.validators import validate_plain_text
from django.core.exceptions import ValidationError

pytestmark = pytest.mark.django_db

UNSAFE_PAYLOADS = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)",  # unterminated tag
    "<svg/onload=alert(1)>",
    "< script >alert(1)</ script >",
    "<!-- comment -->",
    "JaVaScRiPt:alert(1)",
    "vbscript:msgbox(1)",
    "data:text/html;base64,PHNjcmlwdD4=",
]


def complaint_data(**overrides):
    data = {
        "category": "water",
        "title": "Water supply interruption",
        "description": "No water has been available since morning.",
        "ward": "Ward 12",
    }
    data.update(overrides)
    return data


def registration_data(**overrides):
    data = {
        "full_name": "Citizen One",
        "email": "citizen@example.com",
        "phone": "+919000000001",
        "password": "StrongPass2026!",
        "confirm_password": "StrongPass2026!",
    }
    data.update(overrides)
    return data


@pytest.mark.parametrize("payload", UNSAFE_PAYLOADS)
def test_validator_rejects_unsafe_payloads(payload):
    with pytest.raises(ValidationError):
        validate_plain_text(payload)


@pytest.mark.parametrize(
    "text",
    ["Water pressure is below 5 bar", "Ward 12 - Main Road, near temple", "Pothole > 30 cm deep"],
)
def test_validator_accepts_ordinary_text(text):
    assert validate_plain_text(text) == text


@pytest.mark.parametrize("payload", UNSAFE_PAYLOADS)
def test_registration_rejects_unsafe_full_name(payload):
    form = RegistrationForm(data=registration_data(full_name=payload))

    assert not form.is_valid()
    assert "HTML and script content" in form.errors["full_name"][0]
    assert not User.objects.filter(email="citizen@example.com").exists()


def test_registration_accepts_normal_name():
    assert RegistrationForm(data=registration_data(full_name="Asha Rao-Menon")).is_valid()


@pytest.mark.parametrize("missing", ["category", "title", "description", "ward"])
def test_complaint_form_rejects_missing_required_fields(missing):
    form = ComplaintForm(data=complaint_data(**{missing: ""}))

    assert not form.is_valid()
    assert missing in form.errors


@pytest.mark.parametrize("field", ["title", "description", "ward"])
def test_complaint_form_rejects_whitespace_only_values(field):
    form = ComplaintForm(data=complaint_data(**{field: "     "}))

    assert not form.is_valid()
    assert field in form.errors


def test_complaint_form_rejects_invalid_category():
    assert not ComplaintForm(data=complaint_data(category="not-a-category")).is_valid()


def test_complaint_form_rejects_overlong_title():
    assert not ComplaintForm(data=complaint_data(title="x" * 121)).is_valid()


@pytest.mark.parametrize("payload", UNSAFE_PAYLOADS)
def test_complaint_form_rejects_all_unsafe_payloads(payload):
    form = ComplaintForm(data=complaint_data(description=payload))

    assert not form.is_valid()
    assert "description" in form.errors
