"""Issue #27 (SCMS-SR-003 / TC-SEC-03): SQL injection and XSS protection."""

import pytest
from accounts.models import User
from core.models import Complaint
from django.urls import reverse

pytestmark = pytest.mark.django_db

SQLI_PAYLOADS = ["' OR 1=1 --", "'; DROP TABLE core_complaint; --", '" OR ""="', "1 UNION SELECT 1"]


@pytest.fixture
def staff(client):
    user = User.objects.create_user(
        "staff@example.com", "+919000000002", "Staff One", "StrongPass2026!", role="staff"
    )
    client.force_login(user)
    return user


@pytest.fixture
def complaint():
    citizen = User.objects.create_user(
        "citizen@example.com", "+919000000001", "Citizen One", "StrongPass2026!"
    )
    return Complaint.create_with_tracking_id(
        citizen=citizen,
        category=Complaint.Category.WATER,
        title="Private water complaint",
        description="safe",
        ward="Ward 12",
    )


@pytest.mark.parametrize("payload", SQLI_PAYLOADS)
def test_login_identifier_sqli_does_not_authenticate(client, complaint, payload):
    response = client.post(reverse("login"), {"identifier": payload, "password": payload})

    assert response.status_code in (200, 400, 401, 403)
    assert "_auth_user_id" not in client.session


@pytest.mark.parametrize("payload", SQLI_PAYLOADS)
def test_tracking_sqli_returns_no_data(client, complaint, payload):
    response = client.get(reverse("track"), {"tracking_id": payload})

    assert response.status_code == 200
    assert b"Private water complaint" not in response.content


@pytest.mark.parametrize("payload", SQLI_PAYLOADS)
def test_triage_filters_are_not_injectable(client, staff, complaint, payload):
    for params in ({"status": payload}, {"ward": payload}):
        response = client.get(reverse("triage"), params)
        assert response.status_code == 200
        assert b"Private water complaint" not in response.content

    assert Complaint.objects.count() == 1  # table still intact


def test_oversized_tracking_id_is_handled(client, complaint):
    response = client.get(reverse("track"), {"tracking_id": "A" * 5000})

    assert response.status_code == 200
    assert b"No complaint was found" in response.content


def test_reflected_tracking_id_is_escaped(client):
    response = client.get(reverse("track"), {"tracking_id": '"><script>alert(1)</script>'})

    assert b"<script>alert(1)</script>" not in response.content
