"""Issue #23 (SCMS-NF-004 / TC-UX-01): static accessibility checks.

These do not replace the Lighthouse / manual WCAG 2.1 AA evidence; they stop regressions
in basics that automated audits flag (form labels, landmarks, skip link, language).
"""

import re

import pytest
from accounts.models import User
from core.models import Complaint
from django.urls import reverse

pytestmark = pytest.mark.django_db


def assert_inputs_are_labelled(html):
    labelled = set(re.findall(r'<label[^>]*\sfor="([^"]+)"', html))
    for tag in re.findall(r"<(?:input|select|textarea)\b[^>]*>", html):
        if re.search(r'type="(hidden|submit)"', tag):
            continue
        field_id = re.search(r'\bid="([^"]+)"', tag)
        assert field_id and field_id.group(1) in labelled, f"Unlabelled control: {tag}"


@pytest.mark.parametrize("url_name", ["home", "login", "register", "track"])
def test_public_pages_have_landmarks_and_labels(client, url_name):
    html = client.get(reverse(url_name)).content.decode()

    assert '<html lang="en">' in html
    assert 'name="viewport"' in html
    assert 'href="#main"' in html and 'id="main"' in html
    assert "<h1" in html
    assert_inputs_are_labelled(html)


def test_lodge_form_is_labelled(client):
    user = User.objects.create_user("c@example.com", "+919000000001", "Citizen", "StrongPass2026!")
    client.force_login(user)

    assert_inputs_are_labelled(client.get(reverse("lodge_complaint")).content.decode())


def test_staff_pages_are_labelled(client):
    staff = User.objects.create_user(
        "s@example.com", "+919000000002", "Staff", "StrongPass2026!", role="staff"
    )
    citizen = User.objects.create_user("c@example.com", "+919000000001", "Citizen", "StrongPass2026!")
    complaint = Complaint.create_with_tracking_id(
        citizen=citizen, category="water", title="t", description="d", ward="Ward 1"
    )
    client.force_login(staff)

    for url in (
        reverse("triage"),
        reverse("manage_complaint", args=[complaint.tracking_id]),
        reverse("complaint_report"),
    ):
        assert_inputs_are_labelled(client.get(url).content.decode())
