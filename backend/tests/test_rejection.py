from unittest.mock import patch

import pytest
from accounts.models import User
from core.management.commands.send_rejection_emails import deliver_one
from core.models import Complaint, RejectionEmail
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


def rejection_payload(**extra):
    return {
        "status-status": Complaint.Status.REJECTED,
        "status-note": "This complaint duplicates an existing active complaint for the same location.",
        "status-submit": "",
        **extra,
    }


def test_rejection_requires_a_justification_code(client):
    citizen = create_user(User.Role.CITIZEN, 1)
    staff = create_user(User.Role.STAFF, 2)
    complaint = create_complaint(citizen)
    client.force_login(staff)

    response = client.post(reverse("manage_complaint", args=[complaint.tracking_id]), rejection_payload())

    complaint.refresh_from_db()
    assert response.status_code == 200
    assert complaint.status == Complaint.Status.SUBMITTED
    assert RejectionEmail.objects.count() == 0


def test_rejection_records_code_audit_entry_and_email_job(client):
    citizen = create_user(User.Role.CITIZEN, 3)
    staff = create_user(User.Role.STAFF, 4)
    complaint = create_complaint(citizen)
    client.force_login(staff)

    response = client.post(
        reverse("manage_complaint", args=[complaint.tracking_id]),
        rejection_payload(**{"status-rejection_code": Complaint.RejectionCode.DUPLICATE}),
    )

    complaint.refresh_from_db()
    job = RejectionEmail.objects.get(complaint=complaint)
    assert response.status_code == 302
    assert complaint.status == Complaint.Status.REJECTED
    assert complaint.rejection_code == Complaint.RejectionCode.DUPLICATE
    assert complaint.history.last().new_status == Complaint.Status.REJECTED
    assert job.citizen_id == citizen.id


def test_rejection_email_delivery_marks_job_as_sent():
    citizen = create_user(User.Role.CITIZEN, 5)
    complaint = create_complaint(citizen)
    complaint.rejection_code = Complaint.RejectionCode.INVALID
    complaint.rejection_reason = "The submitted complaint does not contain enough verifiable information."
    complaint.save(update_fields=["rejection_code", "rejection_reason", "updated_at"])
    job = RejectionEmail.objects.create(complaint=complaint, citizen=citizen)

    with patch("core.management.commands.send_rejection_emails.send_mail", return_value=1) as send:
        assert deliver_one()

    job.refresh_from_db()
    assert send.called
    assert job.sent_at is not None
