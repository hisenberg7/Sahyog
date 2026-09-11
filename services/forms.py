from datetime import date

from django import forms

from .models import Booking, Rating, Service, WorkerProfile, WorkerWelfare


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["name", "category", "description", "base_price", "experience", "latitude", "longitude", "is_available"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Home Electrical Repair"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "What does this service include?"}),
            "base_price": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01", "placeholder": "Starting price"}),
            "experience": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "latitude": forms.NumberInput(attrs={"class": "form-control", "step": "any", "placeholder": "Latitude"}),
            "longitude": forms.NumberInput(attrs={"class": "form-control", "step": "any", "placeholder": "Longitude"}),
            "is_available": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class WorkerProfileForm(forms.ModelForm):
    class Meta:
        model = WorkerProfile
        fields = ["phone", "skill", "certification", "experience", "bio", "address", "latitude", "longitude", "profile_image", "verification_document", "is_available"]
        widgets = {
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter phone number"}),
            "skill": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Electrician"}),
            "certification": forms.TextInput(attrs={"class": "form-control", "placeholder": "ITI / trade / certification"}),
            "experience": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Tell customers about yourself..."}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Your service location/address"}),
            "latitude": forms.NumberInput(attrs={"class": "form-control", "step": "any", "placeholder": "Latitude"}),
            "longitude": forms.NumberInput(attrs={"class": "form-control", "step": "any", "placeholder": "Longitude"}),
            "profile_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "verification_document": forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".pdf,.jpg,.jpeg,.png"}),
            "is_available": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["address", "latitude", "longitude", "scheduled_date", "scheduled_time"]
        widgets = {
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Enter your service address"}),
            "latitude": forms.HiddenInput(),
            "longitude": forms.HiddenInput(),
            "scheduled_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "scheduled_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
        }

    def clean_scheduled_date(self):
        value = self.cleaned_data.get("scheduled_date")
        if value and value < date.today():
            raise forms.ValidationError("Please choose today or a future date.")
        return value

    def clean(self):
        cleaned = super().clean()
        lat, lng = cleaned.get("latitude"), cleaned.get("longitude")
        if lat is None or lng is None:
            raise forms.ValidationError("Please select your service location on the map.")
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            raise forms.ValidationError("The selected location is invalid. Please pick a location on the map again.")
        return cleaned


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.Select(choices=[(5, "★★★★★  Excellent"), (4, "★★★★☆  Very Good"), (3, "★★★☆☆  Good"), (2, "★★☆☆☆  Poor"), (1, "★☆☆☆☆  Very Poor")], attrs={"class": "form-select"}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Share your experience with this service..."}),
        }

    def clean_rating(self):
        rating = int(self.cleaned_data.get("rating"))
        if not 1 <= rating <= 5:
            raise forms.ValidationError("Rating must be between 1 and 5.")
        return rating


class WorkerWelfareForm(forms.ModelForm):
    PLAN_CHOICES = [
        ("Community Protection Plan", "Community Protection Plan"),
        ("Essential Worker Cover", "Essential Worker Cover"),
        ("Family Safety Plan", "Family Safety Plan"),
    ]
    plan_name = forms.ChoiceField(choices=PLAN_CHOICES, widget=forms.Select(attrs={"class": "form-select"}))

    class Meta:
        model = WorkerWelfare
        fields = ["enrolled", "plan_name", "monthly_contribution", "emergency_support", "notes"]
        widgets = {
            "enrolled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "monthly_contribution": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
            "emergency_support": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Optional notes for the cooperative"}),
        }
