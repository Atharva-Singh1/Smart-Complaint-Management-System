import time
from datetime import timedelta

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import LockoutEmail


def deliver_one():
    # Holding the row lock through the bounded SMTP call prevents concurrent workers
    # from sending the same job. SMTP remains at-least-once if a worker crashes after send.
    with transaction.atomic():
        job = (
            LockoutEmail.objects.select_for_update(skip_locked=True)
            .filter(
                sent_at__isnull=True,
                dead_lettered=False,
                next_attempt_at__lte=timezone.now(),
            )
            .order_by("id")
            .first()
        )
        if job is None:
            return False
        job.attempts += 1
        try:
            count = send_mail(
                "SCMS account temporarily locked",
                "Five unsuccessful sign-in attempts locked your account. "
                f"You may try again after {job.locked_until.isoformat()}. "
                "If this was not you, contact your administrator.",
                None,
                [job.user.email],
                fail_silently=False,
            )
            if count != 1:
                raise RuntimeError("Email was not accepted")
        except Exception:
            # Do not log SMTP exceptions: gateways can echo recipient PII or credentials.
            job.dead_lettered = job.attempts >= 5
            job.next_attempt_at = timezone.now() + timedelta(seconds=30 * 2 ** (job.attempts - 1))
        else:
            job.sent_at = timezone.now()
        job.save()
        return True


class Command(BaseCommand):
    help = "Deliver durable lockout alerts; --watch polls until stopped."

    def add_arguments(self, parser):
        parser.add_argument("--watch", action="store_true")

    def handle(self, *args, **options):
        while True:
            while deliver_one():
                pass
            if not options["watch"]:
                break
            time.sleep(2)
