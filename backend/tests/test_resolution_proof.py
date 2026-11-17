import pytest
from accounts.models import User
from core.models import Complaint, ResolutionProof
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

pytestmark = pytest.mark.django_db


def create_user(role, number):
    return User.objects.create_user(
        f"{role}{number}@example.com",
        f"+9190000000{number:02d}",
        f"{role.title()} {number}",
        "StrongPass2026!",
        role=role,
    )


def create_complaint(citizen):
    return Complaint.create_with_tracking_id(
        citizen=citizen,
        category=Complaint.Category.WATER,
        title="Water supply issue",
        description="Water has not been available since morning.",
        ward="Ward 12",
    )


def resolved_payload(**extra):
    return {
        "status-status": Complaint.Status.RESOLVED,
        "status-note": "Water pipeline repair was completed successfully today.",
        "status-submit": "",
        **extra,
    }


def test_resolution_without_proof_image_is_rejected(client):
    citizen = create_user(User.Role.CITIZEN, 1)
    staff = create_user(User.Role.STAFF, 2)
    complaint = create_complaint(citizen)
    client.force_login(staff)

    response = client.post(reverse("manage_complaint", args=[complaint.tracking_id]), resolved_payload())

    complaint.refresh_from_db()
    assert response.status_code == 200
    assert complaint.status == Complaint.Status.SUBMITTED
    assert ResolutionProof.objects.count() == 0


@override_settings(MEDIA_ROOT="/tmp/scms-resolution-proof-tests")
def test_resolution_with_note_and_proof_image_is_saved(client):
    citizen = create_user(User.Role.CITIZEN, 3)
    staff = create_user(User.Role.STAFF, 4)
    complaint = create_complaint(citizen)
    client.force_login(staff)
    proof_image = SimpleUploadedFile(
        "repair-proof.png", b"\x89PNG\r\n\x1a\nproof-image", content_type="image/png"
    )

    response = client.post(
        reverse("manage_complaint", args=[complaint.tracking_id]),
        resolved_payload(**{"status-proof_image": proof_image}),
    )

    complaint.refresh_from_db()
    proof = ResolutionProof.objects.get(complaint=complaint)
    assert response.status_code == 302
    assert complaint.status == Complaint.Status.RESOLVED
    assert complaint.resolution_note.startswith("Water pipeline repair")
    assert proof.uploaded_by_id == staff.id
    assert complaint.history.last().new_status == Complaint.Status.RESOLVED
