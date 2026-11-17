from datetime import timedelta
from unittest.mock import patch

import pytest
from accounts.management.commands.send_lockout_emails import deliver_one
from accounts.models import LockoutEmail, User
from accounts.services import authenticate_credentials
from django.utils import timezone

pytestmark = pytest.mark.django_db


def create_citizen():
    return User.objects.create_user(
        "citizen@example.com", "+919000000001", "Citizen One", "StrongPass2026!"
    )


def test_five_failed_attempts_lock_for_thirty_minutes_and_queue_email():
    user = create_citizen()
    locked_at = timezone.now()

    with patch("accounts.services.timezone.now", return_value=locked_at):
        for _ in range(5):
            assert authenticate_credentials(user.email, "incorrect-password") is None

    user.refresh_from_db()
    assert user.failed_attempts == 5
    assert user.locked_until == locked_at + timedelta(minutes=30)
    queued = LockoutEmail.objects.get(user=user)
    assert queued.locked_until == user.locked_until
    assert queued.sent_at is None


def test_locked_account_rejects_correct_password_without_creating_extra_alert():
    user = create_citizen()
    for _ in range(5):
        authenticate_credentials(user.email, "incorrect-password")

    assert authenticate_credentials(user.email, "StrongPass2026!") is None
    user.refresh_from_db()
    assert user.failed_attempts == 5
    assert LockoutEmail.objects.filter(user=user).count() == 1


def test_lockout_email_is_retried_without_unlocking_the_account():
    user = create_citizen()
    for _ in range(5):
        authenticate_credentials(user.email, "incorrect-password")
    job = LockoutEmail.objects.get(user=user)

    with patch(
        "accounts.management.commands.send_lockout_emails.send_mail", side_effect=RuntimeError
    ):
        assert deliver_one()

    job.refresh_from_db()
    user.refresh_from_db()
    assert job.sent_at is None
    assert job.attempts == 1
    assert user.locked_until is not None

    job.next_attempt_at = timezone.now() - timedelta(seconds=1)
    job.save(update_fields=["next_attempt_at"])
    with patch("accounts.management.commands.send_lockout_emails.send_mail", return_value=1):
        assert deliver_one()

    job.refresh_from_db()
    assert job.sent_at is not None
