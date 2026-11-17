from datetime import timedelta

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import RejectionEmail


def deliver_one():
    """Attempt one queued email without rolling back the complaint rejection."""
    with transaction.atomic():
        job = (
            RejectionEmail.objects.select_for_update(skip_locked=True)
            .select_related("citizen", "complaint")
            .filter(sent_at__isnull=True, dead_lettered=False, next_attempt_at__lte=timezone.now())
            .order_by("id")
            .first()
        )
        if job is None:
            return False

        job.attempts += 1
        try:
            count = send_mail(
                f"SCMS complaint {job.complaint.tracking_id} was rejected",
                "Your complaint was rejected. "
                f"Reason category: {job.complaint.get_rejection_code_display()}. "
                f"Explanation: {job.complaint.rejection_reason}",
                None,
                [job.citizen.email],
                fail_silently=False,
            )
            if count != 1:
                raise RuntimeError("Email was not accepted")
        except Exception:
            job.dead_lettered = job.attempts >= 5
            job.next_attempt_at = timezone.now() + timedelta(seconds=30 * 2 ** (job.attempts - 1))
        else:
            job.sent_at = timezone.now()
        job.save(update_fields=["attempts", "dead_lettered", "next_attempt_at", "sent_at"])
        return True


class Command(BaseCommand):
    help = "Deliver queued complaint-rejection explanation emails."

    def handle(self, *args, **options):
        while deliver_one():
            pass
