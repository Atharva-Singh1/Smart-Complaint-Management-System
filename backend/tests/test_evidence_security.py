import pytest
from accounts.models import User
from core.forms import ComplaintForm
from core.models import Evidence
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

pytestmark = pytest.mark.django_db


def complaint_data():
    return {
        "category": "water",
        "title": "Water supply issue",
        "description": "Water has not been available since morning.",
        "ward": "Ward 12",
    }


def test_disguised_executable_is_rejected_by_magic_bytes():
    disguised_file = SimpleUploadedFile(
        "not-safe.jpg", b"MZ\x90\x00not-an-image", content_type="image/jpeg"
    )
    form = ComplaintForm(data=complaint_data(), files={"evidence_files": [disguised_file]})

    assert not form.is_valid()
    assert form.errors.as_data()["evidence_files"][0].code == "unsupported_media_type"


def test_valid_png_content_is_accepted_even_when_browser_mime_is_wrong():
    png_file = SimpleUploadedFile(
        "evidence.png", b"\x89PNG\r\n\x1a\nminimal-png-data", content_type="application/octet-stream"
    )
    form = ComplaintForm(data=complaint_data(), files={"evidence_files": [png_file]})

    assert form.is_valid()


def test_disguised_upload_returns_415_and_is_not_stored(client):
    user = User.objects.create_user(
        "citizen@example.com", "+919000000001", "Citizen One", "StrongPass2026!"
    )
    client.force_login(user)
    disguised_file = SimpleUploadedFile(
        "proof.pdf", b"#!/bin/sh\necho unsafe", content_type="application/pdf"
    )

    response = client.post(
        reverse("lodge_complaint"), {**complaint_data(), "evidence_files": disguised_file}
    )

    assert response.status_code == 415
    assert Evidence.objects.count() == 0
