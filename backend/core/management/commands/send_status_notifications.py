import time
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import StatusNotification


def send_sms(phone, message):
    """Use a deployment-configured SMS sender without storing provider secrets in code."""
    sender = getattr(settings, "SCMS_SMS_SENDER", None)
    if not callable(sender):
        raise RuntimeError("SMS provider is not configured")
    return sender(phone, message)


def deliver_one():
    """Deliver one queued status alert; provider errors only affect the job retry state."""
    with transaction.atomic():
        job = (
            StatusNotification.objects.select_for_update(skip_locked=True)
            .select_related("complaint", "recipient")
            .filter(sent_at__isnull=True, dead_lettered=False, next_attempt_at__lte=timezone.now())
            .order_by("id")
            .first()
        )
        if job is None:
            return False

        job.attempts += 1
        status_display = job.complaint.get_status_display()
        message = (
            f"SCMS update: complaint {job.complaint.tracking_id} is now {status_display}."
        )
        try:
            if job.channel == StatusNotification.Channel.EMAIL:
                delivered = send_mail(
                    f"SCMS complaint update: {status_display}",
                    message,
                    None,
                    [job.recipient.email],
                    fail_silently=False,
                )
                if delivered != 1:
                    raise RuntimeError("Email was not accepted")
            else:
                if not send_sms(job.recipient.phone, message):
                    raise RuntimeError("SMS was not accepted")
        except Exception:
            job.dead_lettered = job.attempts >= 5
            job.next_attempt_at = timezone.now() + timedelta(seconds=30 * 2 ** (job.attempts - 1))
        else:
            job.sent_at = timezone.now()
        job.save(update_fields=["attempts", "dead_lettered", "next_attempt_at", "sent_at"])
        return True


class Command(BaseCommand):
    help = "Deliver queued complaint status notifications; --watch polls every two seconds."

    def add_arguments(self, parser):
        parser.add_argument("--watch", action="store_true")

    def handle(self, *args, **options):
        while True:
            while deliver_one():
                pass
            if not options["watch"]:
                break
            time.sleep(2)
