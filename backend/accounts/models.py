from django.contrib.auth import SESSION_KEY
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.sessions.models import Session
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Lower
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, phone, full_name, password=None, **extra):
        user = self.model(email=email.strip().lower(), phone=phone, full_name=full_name, **extra)
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    class Role(models.TextChoices):
        CITIZEN = "citizen", "Citizen"
        STAFF = "staff", "Department Staff"
        ADMIN = "admin", "Administrator"

    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=16,
        unique=True,
        validators=[
            RegexValidator(
                r"^\+[1-9][0-9]{7,14}$",
                "Use an international phone number, e.g. +919876543210.",
            )
        ],
    )
    full_name = models.CharField(max_length=150)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CITIZEN)
    is_active = models.BooleanField(default=True)
    failed_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["phone", "full_name"]

    @property
    def is_staff(self):
        return self.role in {self.Role.STAFF, self.Role.ADMIN}

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("email"), name="user_email_case_insensitive"),
            models.CheckConstraint(
                condition=models.Q(role__in=["citizen", "staff", "admin"]),
                name="user_valid_role",
            ),
        ]


class LockoutEmail(models.Model):
    """Durable lockout alert; contains no password or session token."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    locked_until = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    next_attempt_at = models.DateTimeField(default=timezone.now)
    attempts = models.PositiveSmallIntegerField(default=0)
    sent_at = models.DateTimeField(null=True, blank=True)
    dead_lettered = models.BooleanField(default=False)


@receiver(pre_save, sender=User)
def remember_role_change(sender, instance, **kwargs):
    """Record role changes so stale authenticated sessions can be revoked."""
    if instance._state.adding:
        return
    previous_role = sender.objects.filter(pk=instance.pk).values_list("role", flat=True).first()
    instance._role_changed = previous_role is not None and previous_role != instance.role


@receiver(post_save, sender=User)
def revoke_sessions_after_role_change(sender, instance, created, **kwargs):
    """Force fresh authentication after a privilege change.

    Django cycles a session key at login. Deleting old user sessions here prevents
    a pre-change cookie from continuing to carry the old privilege context.
    """
    if created or not getattr(instance, "_role_changed", False):
        return
    for session in Session.objects.iterator():
        try:
            session_data = session.get_decoded()
        except Exception:  # Corrupt/expired sessions are not security-relevant.
            continue
        if str(session_data.get(SESSION_KEY)) == str(instance.pk):
            session.delete()
