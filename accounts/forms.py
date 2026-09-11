from django import forms
from django.contrib.auth.models import User
from .models import UserProfile
from services.models import WorkerProfile


class RegistrationForm(forms.ModelForm):

    ROLE_CHOICES = [
        ("customer", "Customer"),
        ("worker", "Worker"),
    ]

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Create a password",
            }
        )
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm your password",
            }
        )
    )

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        )
    )

    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter phone number",
            }
        )
    )

    address = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your address",
                "rows": 3,
            }
        )
    )

    class Meta:
        model = User

        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
        ]

        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "First name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Last name",
                }
            ),
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Username",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Email address",
                }
            ),
        }

    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError(
                    "Passwords do not match."
                )

        return cleaned_data

    def save(self, commit=True):

        user = super().save(commit=False)

        user.set_password(
            self.cleaned_data["password"]
        )

        if commit:
            user.save()

            UserProfile.objects.create(
                user=user,
                role=self.cleaned_data["role"],
                phone=self.cleaned_data["phone"],
                address=self.cleaned_data.get("address", ""),
            )

            if self.cleaned_data["role"] == "worker":
                WorkerProfile.objects.create(
                    user=user,
                    phone=self.cleaned_data["phone"],
                    address=self.cleaned_data.get("address", ""),
                )

        return user