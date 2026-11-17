from unittest.mock import patch

import pytest
from accounts.models import User
from core.management.commands.send_assignment_emails import deliver_one
from core.models import AssignmentEmail, Complaint
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


def test_assignment_sets_assignee_status_note_and_email_job(client):
    citizen = create_user(User.Role.CITIZEN, 1)
    administrator = create_user(User.Role.ADMIN, 2)
    assignee = create_user(User.Role.STAFF, 3)
    complaint = create_complaint(citizen)
    client.force_login(administrator)

    response = client.post(
        reverse("manage_complaint", args=[complaint.tracking_id]),
        {
            "assign-assigned_to": assignee.id,
            "assign-internal_note": "Inspect the reported water pipeline today.",
            "assign-submit": "",
        },
    )

    complaint.refresh_from_db()
    job = AssignmentEmail.objects.get(complaint=complaint)
    assert response.status_code == 302
    assert complaint.assigned_to_id == assignee.id
    assert complaint.status == Complaint.Status.ASSIGNED
    assert complaint.internal_note.startswith("Inspect")
    assert complaint.history.last().new_status == Complaint.Status.ASSIGNED
    assert job.assignee_id == assignee.id


def test_assignment_email_delivery_marks_job_as_sent():
    citizen = create_user(User.Role.CITIZEN, 4)
    assignee = create_user(User.Role.STAFF, 5)
    complaint = create_complaint(citizen)
    job = AssignmentEmail.objects.create(complaint=complaint, assignee=assignee)

    with patch("core.management.commands.send_assignment_emails.send_mail", return_value=1) as send:
        assert deliver_one()

    job.refresh_from_db()
    assert send.called
    assert job.sent_at is not None
