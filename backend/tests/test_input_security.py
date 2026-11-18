import pytest
from accounts.models import User
from core.forms import ComplaintForm
from core.models import Complaint
from django.urls import reverse


pytestmark = pytest.mark.django_db


def valid_complaint_data(**overrides):
    data = {
        "category": "water",
        "title": "Water supply interruption",
        "description": "No water has been available since morning.",
        "ward": "Ward 12",
    }
    data.update(overrides)
    return data


@pytest.mark.parametrize("field", ["title", "description", "ward"])
def test_complaint_form_rejects_html_and_script_payloads(field):
    form = ComplaintForm(data=valid_complaint_data(**{field: "<script>alert('xss')</script>"}))

    assert not form.is_valid()
    assert "HTML and script content" in form.errors[field][0]


def test_public_tracking_escapes_legacy_html_data(client):
    citizen = User.objects.create_user(
        "citizen@example.com", "+919000000001", "Citizen One", "StrongPass2026!"
    )
    complaint = Complaint.create_with_tracking_id(
        citizen=citizen,
        category=Complaint.Category.WATER,
        title="<script>alert('legacy')</script>",
        description="safe",
        ward="Ward 12",
    )

    response = client.get(reverse("track"), {"tracking_id": complaint.tracking_id})

    assert response.status_code == 200
    assert b"<script>alert('legacy')</script>" not in response.content
    assert b"&lt;script&gt;alert(&#x27;legacy&#x27;)&lt;/script&gt;" in response.content


def test_tracking_id_sqli_payload_does_not_expose_other_complaints(client):
    citizen = User.objects.create_user(
        "citizen@example.com", "+919000000001", "Citizen One", "StrongPass2026!"
    )
    Complaint.create_with_tracking_id(
        citizen=citizen,
        category=Complaint.Category.WATER,
        title="Private water complaint",
        description="safe",
        ward="Ward 12",
    )

    response = client.get(reverse("track"), {"tracking_id": "' OR 1=1 --"})

    assert response.status_code == 200
    assert b"Private water complaint" not in response.content
