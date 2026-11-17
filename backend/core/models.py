import secrets

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models, transaction
from django.utils import timezone


class Complaint(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        ASSIGNED = "assigned", "Assigned"
        UNDER_REVIEW = "under_review", "Under Review"
        RESOLVED = "resolved", "Resolved"
        REJECTED = "rejected", "Rejected"

    class Category(models.TextChoices):
        ROADS = "roads", "Roads & Footpaths"
        WATER = "water", "Water Supply"
        SANITATION = "sanitation", "Sanitation"
        STREETLIGHT = "streetlight", "Streetlights"
        OTHER = "other", "Other"

    class RejectionCode(models.TextChoices):
        DUPLICATE = "duplicate", "Duplicate complaint"
        INVALID = "invalid", "Invalid complaint"
        INSUFFICIENT_INFO = "insufficient_info", "Insufficient information"
        OUT_OF_SCOPE = "out_of_scope", "Outside department scope"

    tracking_id = models.CharField(max_length=24, unique=True, editable=False)
    citizen = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="complaints"
    )
    category = models.CharField(max_length=20, choices=Category.choices)
    title = models.CharField(max_length=120)
    description = models.TextField(max_length=2000)
    ward = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_complaints",
    )
    internal_note = models.TextField(blank=True, max_length=1000)
    resolution_note = models.TextField(blank=True, max_length=2000)
    rejection_reason = models.TextField(blank=True, max_length=1000)
    rejection_code = models.CharField(blank=True, choices=RejectionCode.choices, max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @classmethod
    def create_with_tracking_id(cls, **kwargs):
        """Create an immutable SCMS-YYYYMM-XXXXX tracking ID from the database ID."""
        with transaction.atomic():
            # A temporary value satisfies the unique field until the database assigns its ID.
            complaint = cls.objects.create(tracking_id=f"PENDING-{secrets.token_hex(8)}", **kwargs)
            complaint.tracking_id = f"SCMS-{timezone.now():%Y%m}-{complaint.pk:05d}"
            complaint.save(update_fields=["tracking_id"])
            AuditLog.objects.create(
                complaint=complaint,
                actor=complaint.citizen,
                previous_status="",
                new_status=cls.Status.SUBMITTED,
                note="Complaint submitted",
            )
            StatusNotification.queue_for_citizen(complaint, cls.Status.SUBMITTED)
            return complaint

    def change_status(self, *, actor, new_status, note=""):
        with transaction.atomic():
            previous = self.status
            self.status = new_status
            self.save()
            AuditLog.objects.create(
                complaint=self,
                actor=actor,
                previous_status=previous,
                new_status=new_status,
                note=note,
            )
            StatusNotification.queue_for_citizen(self, new_status)


class Evidence(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="evidence")
    file = models.FileField(
        upload_to="evidence/%Y/%m/",
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "pdf"])],
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)


class ResolutionProof(models.Model):
    """Photographic proof supplied by staff before a complaint is resolved."""

    complaint = models.ForeignKey(
        Complaint, on_delete=models.CASCADE, related_name="resolution_proofs"
    )
    image = models.FileField(
        upload_to="resolution-proofs/%Y/%m/",
        validators=[FileExtensionValidator(["jpg", "jpeg", "png"])],
    )
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class AppendOnlyAuditQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("Audit records are append-only and cannot be updated.")

    def delete(self):
        raise ValidationError("Audit records are append-only and cannot be deleted directly.")


class AuditLog(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="history")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    note = models.TextField(blank=True, max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = AppendOnlyAuditQuerySet.as_manager()

    class Meta:
        ordering = ["created_at"]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Audit records are append-only and cannot be updated.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Audit records are append-only and cannot be deleted directly.")


class AssignmentEmail(models.Model):
    """Durable notification job for a newly assigned complaint."""

    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="assignment_emails")
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    next_attempt_at = models.DateTimeField(default=timezone.now)
    attempts = models.PositiveSmallIntegerField(default=0)
    sent_at = models.DateTimeField(null=True, blank=True)
    dead_lettered = models.BooleanField(default=False)


class RejectionEmail(models.Model):
    """Durable outbox record for a citizen rejection explanation email."""

    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="rejection_emails")
    citizen = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    next_attempt_at = models.DateTimeField(default=timezone.now)
    attempts = models.PositiveSmallIntegerField(default=0)
    sent_at = models.DateTimeField(null=True, blank=True)
    dead_lettered = models.BooleanField(default=False)


class StatusNotification(models.Model):
    """Durable, retryable email/SMS outbox for complaint status changes."""

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"

    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="status_notifications")
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Complaint.Status.choices)
    channel = models.CharField(max_length=10, choices=Channel.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    next_attempt_at = models.DateTimeField(default=timezone.now)
    attempts = models.PositiveSmallIntegerField(default=0)
    sent_at = models.DateTimeField(null=True, blank=True)
    dead_lettered = models.BooleanField(default=False)

    @classmethod
    def queue_for_citizen(cls, complaint, status):
        cls.objects.bulk_create(
            [
                cls(
                    complaint=complaint,
                    recipient=complaint.citizen,
                    status=status,
                    channel=cls.Channel.EMAIL,
                ),
                cls(
                    complaint=complaint,
                    recipient=complaint.citizen,
                    status=status,
                    channel=cls.Channel.SMS,
                ),
            ]
        )
