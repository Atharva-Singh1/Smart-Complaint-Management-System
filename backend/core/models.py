import secrets

from django.conf import settings
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
            return complaint

    def change_status(self, *, actor, new_status, note=""):
        previous = self.status
        self.status = new_status
        self.save()
        AuditLog.objects.create(
            complaint=self, actor=actor, previous_status=previous, new_status=new_status, note=note
        )


class Evidence(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="evidence")
    file = models.FileField(
        upload_to="evidence/%Y/%m/",
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "pdf"])],
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)


class AuditLog(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="history")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    note = models.TextField(blank=True, max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
