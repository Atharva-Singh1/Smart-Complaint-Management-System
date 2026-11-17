from datetime import timedelta

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import AssignmentEmail


def deliver_one():
    """Deliver one queued assignment email without affecting the complaint status."""
    with transaction.atomic():
        job = (
            AssignmentEmail.objects.select_for_update(skip_locked=True)
            .select_related("assignee", "complaint")
            .filter(sent_at__isnull=True, dead_lettered=False, next_attempt_at__lte=timezone.now())
            .order_by("id")
            .first()
        )
        if job is None:
            return False

        job.attempts += 1
        try:
            count = send_mail(
                f"SCMS complaint assigned: {job.complaint.tracking_id}",
                "You have been assigned a complaint. "
                f"Tracking ID: {job.complaint.tracking_id}. "
                f"Internal note: {job.complaint.internal_note or 'No internal note provided.'}",
                None,
                [job.assignee.email],
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
    help = "Deliver queued complaint-assignment emails."

    def handle(self, *args, **options):
        while deliver_one():
            pass
