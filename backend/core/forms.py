from pathlib import Path

from accounts.models import User
from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

from .models import Complaint
from .validators import validate_plain_text


def validate_proof_image_content(file):
    """Accept only JPEG or PNG bytes for a resolution proof image."""
    signature = file.read(8)
    file.seek(0)
    is_jpeg = signature.startswith(b"\xff\xd8\xff")
    is_png = signature.startswith(b"\x89PNG\r\n\x1a\n")
    if not (is_jpeg or is_png):
        raise forms.ValidationError("Resolution proof must be a genuine JPEG or PNG image.")


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput, min_length=8)

    class Meta:
        model = User
        fields = ["full_name", "email", "phone", "password"]

    def clean_full_name(self):
        return validate_plain_text(self.cleaned_data["full_name"])

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        if password:
            try:
                validate_password(password)
            except ValidationError as error:
                self.add_error("password", error)
        if password != cleaned.get("confirm_password"):
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned

    def save(self, commit=True):
        return User.objects.create_user(
            email=self.cleaned_data["email"],
            phone=self.cleaned_data["phone"],
            full_name=self.cleaned_data["full_name"],
            password=self.cleaned_data["password"],
            role=User.Role.CITIZEN,
        )


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class EvidenceField(forms.FileField):
    def clean(self, data, initial=None):
        files = data if isinstance(data, (list, tuple)) else [data]
        return [super(EvidenceField, self).clean(file, initial) for file in files if file]


class ComplaintForm(forms.ModelForm):
    evidence_files = EvidenceField(required=False, widget=MultipleFileInput)

    class Meta:
        model = Complaint
        fields = ["category", "title", "description", "ward"]
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}

    def clean_title(self):
        return validate_plain_text(self.cleaned_data["title"])

    def clean_description(self):
        return validate_plain_text(self.cleaned_data["description"])

    def clean_ward(self):
        return validate_plain_text(self.cleaned_data["ward"])

    def clean_evidence_files(self):
        files = self.cleaned_data["evidence_files"]
        if len(files) > 5:
            raise forms.ValidationError("You may upload a maximum of five files.")
        for file in files:
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError(f"{file.name} is larger than 5 MB.")
            detected_type = self._detect_file_type(file)
            extension = Path(file.name).suffix.lower()
            allowed_extensions = {
                "image/jpeg": {".jpg", ".jpeg"},
                "image/png": {".png"},
                "application/pdf": {".pdf"},
            }
            if detected_type is None or extension not in allowed_extensions.get(detected_type, set()):
                raise forms.ValidationError(
                    "Only genuine JPG, PNG, and PDF evidence is allowed.",
                    code="unsupported_media_type",
                )
        return files

    @staticmethod
    def _detect_file_type(file):
        """Identify the actual file content; browser MIME headers are untrusted."""
        signature = file.read(16)
        file.seek(0)
        if signature.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if signature.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if signature.startswith(b"%PDF-"):
            return "application/pdf"
        return None


class AssignmentForm(forms.Form):
    assigned_to = forms.ModelChoiceField(queryset=User.objects.none(), label="Assign to")
    internal_note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = User.objects.filter(
            role__in=[User.Role.STAFF, User.Role.ADMIN]
        )

    def clean_internal_note(self):
        return validate_plain_text(self.cleaned_data["internal_note"])


class StatusForm(forms.Form):
    status = forms.ChoiceField(
        choices=[
            (Complaint.Status.UNDER_REVIEW, "Under Review"),
            (Complaint.Status.RESOLVED, "Resolved"),
            (Complaint.Status.REJECTED, "Rejected"),
        ]
    )
    note = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)
    proof_image = forms.FileField(
        required=False,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png"]), validate_proof_image_content],
        help_text="Required when setting status to Resolved.",
    )
    rejection_code = forms.ChoiceField(
        choices=[("", "Select a justification code")] + list(Complaint.RejectionCode.choices),
        required=False,
    )

    def clean_note(self):
        return validate_plain_text(self.cleaned_data["note"])
