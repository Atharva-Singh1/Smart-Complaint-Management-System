from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import User


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
