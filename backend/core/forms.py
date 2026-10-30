from accounts.models import User
from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Complaint


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput, min_length=8)

    class Meta:
        model = User
        fields = ["full_name", "email", "phone", "password"]

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

    def clean_evidence_files(self):
        files = self.cleaned_data["evidence_files"]
        if len(files) > 5:
            raise forms.ValidationError("You may upload a maximum of five files.")
        allowed = {"image/jpeg", "image/png", "application/pdf"}
        for file in files:
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError(f"{file.name} is larger than 5 MB.")
            if file.content_type not in allowed:
                raise forms.ValidationError("Only JPG, PNG, and PDF evidence is allowed.")
        return files


class AssignmentForm(forms.Form):
    assigned_to = forms.ModelChoiceField(queryset=User.objects.none(), label="Assign to")
    internal_note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = User.objects.filter(
            role__in=[User.Role.STAFF, User.Role.ADMIN]
        )


class StatusForm(forms.Form):
    status = forms.ChoiceField(
        choices=[
            (Complaint.Status.UNDER_REVIEW, "Under Review"),
            (Complaint.Status.RESOLVED, "Resolved"),
            (Complaint.Status.REJECTED, "Rejected"),
        ]
    )
    note = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)
