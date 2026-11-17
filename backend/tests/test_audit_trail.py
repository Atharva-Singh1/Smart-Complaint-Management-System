from unittest.mock import patch

import pytest
from accounts.models import User
from core.models import AuditLog, Complaint
from django.core.exceptions import ValidationError

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


def test_audit_history_records_submission_and_status_transition():
    citizen = create_user(User.Role.CITIZEN, 1)
    staff = create_user(User.Role.STAFF, 2)
    complaint = create_complaint(citizen)

    complaint.change_status(
        actor=staff,
        new_status=Complaint.Status.UNDER_REVIEW,
        note="Officer started investigating the supply issue.",
    )

    history = list(complaint.history.all())
    assert len(history) == 2
    assert history[0].previous_status == ""
    assert history[0].new_status == Complaint.Status.SUBMITTED
    assert history[0].actor_id == citizen.id
    assert history[1].previous_status == Complaint.Status.SUBMITTED
    assert history[1].new_status == Complaint.Status.UNDER_REVIEW
    assert history[1].actor_id == staff.id
    assert history[1].created_at is not None


def test_audit_records_cannot_be_updated_or_deleted():
    citizen = create_user(User.Role.CITIZEN, 3)
    complaint = create_complaint(citizen)
    entry = complaint.history.get()

    entry.note = "Changed after creation"
    with pytest.raises(ValidationError):
        entry.save()
    with pytest.raises(ValidationError):
        AuditLog.objects.filter(pk=entry.pk).update(note="Changed in a queryset")
    with pytest.raises(ValidationError):
        entry.delete()


def test_status_change_rolls_back_when_audit_write_fails():
    citizen = create_user(User.Role.CITIZEN, 4)
    staff = create_user(User.Role.STAFF, 5)
    complaint = create_complaint(citizen)

    with patch.object(AuditLog.objects, "create", side_effect=RuntimeError("audit unavailable")):
        with pytest.raises(RuntimeError, match="audit unavailable"):
            complaint.change_status(actor=staff, new_status=Complaint.Status.UNDER_REVIEW)

    complaint.refresh_from_db()
    assert complaint.status == Complaint.Status.SUBMITTED
    assert complaint.history.count() == 1
