from django.conf import settings
from django.db import models
from django.utils import timezone


class Service(models.Model):
    CATEGORY_CHOICES = [
        ("electrician", "Electrician"),
        ("plumber", "Plumber"),
        ("carpenter", "Carpenter"),
        ("painter", "Painter"),
        ("cleaner", "Cleaner"),
        ("caregiver", "Caregiver"),
        ("driver", "Driver"),
        ("gardener", "Gardener"),
        ("technician", "Technician"),
        ("domestic_helper", "Domestic Helper"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default="other",
    )
    description = models.TextField(blank=True, default="")
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="services",
        null=True,
        blank=True,
    )
    experience = models.PositiveIntegerField(
        default=0,
        help_text="Experience in years",
    )
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.worker.username if self.worker else 'No Worker'}"


class WorkerProfile(models.Model):
    VERIFICATION_STATUS_CHOICES = [
        ("pending", "Not Submitted"),
        ("under_review", "Under Review"),
        ("verified", "Verified"),
        ("rejected", "Rejected"),
    ]

    INSURANCE_STATUS_CHOICES = [
        ("not_enrolled", "Not Enrolled"),
        ("pending", "Pending"),
        ("active", "Active"),
        ("expired", "Expired"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    phone = models.CharField(max_length=15, blank=True, default="")
    skill = models.CharField(max_length=100, blank=True, default="")
    certification = models.CharField(max_length=200, blank=True, default="")
    experience = models.PositiveIntegerField(default=0)
    bio = models.TextField(blank=True, default="")
    address = models.TextField(blank=True, default="")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    profile_image = models.ImageField(
        upload_to="workers/",
        blank=True,
        null=True,
    )
    verification_document = models.FileField(
        upload_to="verification/",
        blank=True,
        null=True,
    )
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default="pending",
    )
    verification_note = models.TextField(blank=True, default="")
    verified_at = models.DateTimeField(null=True, blank=True)
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
    )
    total_reviews = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    insurance_status = models.CharField(
        max_length=20,
        choices=INSURANCE_STATUS_CHOICES,
        default="not_enrolled",
    )
    insurance_provider = models.CharField(
        max_length=120,
        blank=True,
        default="",
    )
    insurance_policy_number = models.CharField(
        max_length=120,
        blank=True,
        default="",
    )
    insurance_valid_until = models.DateField(
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
    )

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def verification_label(self):
        return self.get_verification_status_display()

    @property
    def insurance_active(self):
        return (
            self.insurance_status == "active"
            and (
                not self.insurance_valid_until
                or self.insurance_valid_until >= timezone.localdate()
            )
        )

    def __str__(self):
        return self.user.username


class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("on_the_way", "On the Way"),
        ("arrived", "Arrived"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    BOOKING_TYPE_CHOICES = [("now", "Book Now"), ("schedule", "Scheduled")]

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_bookings",
    )
    worker = models.ForeignKey(
        WorkerProfile,
        on_delete=models.CASCADE,
        related_name="worker_bookings",
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
    )

    address = models.TextField()
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # -------------------------------------------------
    # LIVE WORKER TRACKING
    # -------------------------------------------------
    # These fields store the worker's latest GPS position
    # for this specific booking.
    live_latitude = models.FloatField(
        null=True,
        blank=True,
    )
    live_longitude = models.FloatField(
        null=True,
        blank=True,
    )
    location_updated_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    # -------------------------------------------------
    # BILLING BREAKDOWN
    # -------------------------------------------------
    # amount remains the final customer payable amount.
    base_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    emergency_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    approved_extra_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    is_emergency = models.BooleanField(default=False)
    booking_type = models.CharField(max_length=10, choices=BOOKING_TYPE_CHOICES, default="now")
    distance_km = models.FloatField(null=True, blank=True)
    matching_score = models.FloatField(null=True, blank=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Pending request auto-expires after this time.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking #{self.id}"


class Payment(models.Model):
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
    )

    PAYMENT_METHOD_CHOICES = [
        ("upi", "UPI / Online"),
        ("cash", "Cash"),
    ]

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default="upi",
    )
    upi_transaction_id = models.CharField(
        max_length=200,
        blank=True,
        default="",
    )
    payment_screenshot = models.ImageField(
        upload_to="payments/",
        blank=True,
        null=True,
    )
    razorpay_order_id = models.CharField(
        max_length=200,
        blank=True,
    )
    razorpay_payment_id = models.CharField(
        max_length=200,
        blank=True,
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("submitted", "Payment Submitted"),
        ("verified", "Payment Verified"),
        ("rejected", "Payment Rejected"),
    ]

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="pending",
    )
    rejection_reason = models.TextField(
        blank=True,
        default="",
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_payments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.id}"


class Rating(models.Model):
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
    )
    rating = models.PositiveIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating {self.rating}/5"


class WorkerWelfare(models.Model):
    worker = models.OneToOneField(
        WorkerProfile,
        on_delete=models.CASCADE,
        related_name="welfare",
    )
    enrolled = models.BooleanField(default=False)
    plan_name = models.CharField(
        max_length=120,
        blank=True,
        default="Community Protection Plan",
    )
    monthly_contribution = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    coverage_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    emergency_support = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Welfare - {self.worker.user.username}"


class ExtraCharge(models.Model):
    """
    Additional amount proposed by the worker.
    It is not included in the customer's payable amount
    until the customer approves it.
    """

    CHARGE_TYPE_CHOICES = [
        ("material", "Parts / Material"),
        ("labour", "Additional Labour"),
        ("service", "Additional Service"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("pending", "Awaiting Customer Approval"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="extra_charges",
    )
    worker = models.ForeignKey(
        WorkerProfile,
        on_delete=models.CASCADE,
        related_name="extra_charges",
    )
    charge_type = models.CharField(
        max_length=20,
        choices=CHARGE_TYPE_CHOICES,
        default="other",
    )
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    customer_note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} - ₹{self.total}"


class BillingApproval(models.Model):
    """
    Audit record for the customer's decision on additional charges.
    """

    DECISION_CHOICES = [
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="billing_approvals",
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="billing_approvals",
    )
    decision = models.CharField(
        max_length=20,
        choices=DECISION_CHOICES,
    )
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Billing approval #{self.id} - {self.decision}"


class Invoice(models.Model):
    STATUS_CHOICES = [
        ("issued", "Issued"),
        ("paid", "Paid"),
        ("void", "Void"),
    ]

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="invoice",
    )
    invoice_number = models.CharField(
        max_length=40,
        unique=True,
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    platform_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    worker_earnings = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="issued",
    )
    issued_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.invoice_number


class DemandForecast(models.Model):
    category = models.CharField(max_length=50)
    forecast_date = models.DateField()
    predicted_bookings = models.FloatField(default=0)
    confidence = models.FloatField(default=0)
    model_name = models.CharField(
        max_length=80,
        default="Moving Average",
    )
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("category", "forecast_date")
        ordering = ["forecast_date", "category"]

    def __str__(self):
        return f"{self.category} - {self.forecast_date}"