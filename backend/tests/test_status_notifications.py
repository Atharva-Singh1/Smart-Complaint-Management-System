from unittest.mock import patch

import pytest
from accounts.models import User
from core.management.commands.send_status_notifications import deliver_one
from core.models import Complaint, StatusNotification
from django.utils import timezone

pytestmark = pytest.mark.django_db


def create_citizen():
    return User.objects.create_user(
        "citizen@example.com", "+919000000001", "Citizen One", "StrongPass2026!"
    )


def create_complaint(citizen):
    return Complaint.create_with_tracking_id(
        citizen=citizen,
        category=Complaint.Category.WATER,
        title="Water supply issue",
        description="Water has not been available since morning.",
        ward="Ward 12",
    )


def test_submission_and_status_change_queue_email_and_sms():
    citizen = create_citizen()
    complaint = create_complaint(citizen)

    submitted_jobs = StatusNotification.objects.filter(
        complaint=complaint, status=Complaint.Status.SUBMITTED
    )
    assert set(submitted_jobs.values_list("channel", flat=True)) == {"email", "sms"}

    complaint.change_status(actor=citizen, new_status=Complaint.Status.UNDER_REVIEW)

    review_jobs = StatusNotification.objects.filter(
        complaint=complaint, status=Complaint.Status.UNDER_REVIEW
    )
    assert set(review_jobs.values_list("channel", flat=True)) == {"email", "sms"}


def test_provider_failure_does_not_undo_the_status_change():
    citizen = create_citizen()
    complaint = create_complaint(citizen)
    # Finish the initial submission alerts so the delivery worker picks the
    # newly-created resolved alert below.
    StatusNotification.objects.filter(complaint=complaint).update(sent_at=timezone.now())
    complaint.change_status(actor=citizen, new_status=Complaint.Status.RESOLVED)
    job = StatusNotification.objects.get(
        complaint=complaint,
        status=Complaint.Status.RESOLVED,
        channel=StatusNotification.Channel.EMAIL,
    )

    with patch("core.management.commands.send_status_notifications.send_mail", side_effect=RuntimeError):
        assert deliver_one()

    complaint.refresh_from_db()
    job.refresh_from_db()
    assert complaint.status == Complaint.Status.RESOLVED
    assert job.sent_at is None
    assert job.attempts == 1


def test_email_and_sms_jobs_can_be_dispatched():
    citizen = create_citizen()
    complaint = create_complaint(citizen)

    with (
        patch("core.management.commands.send_status_notifications.send_mail", return_value=1),
        patch("core.management.commands.send_status_notifications.send_sms", return_value=True),
    ):
        assert deliver_one()
        assert deliver_one()

    assert StatusNotification.objects.filter(complaint=complaint, sent_at__isnull=False).count() == 2
