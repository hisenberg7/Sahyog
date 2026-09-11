from datetime import timedelta
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

try:
    from sklearn.linear_model import LinearRegression
except Exception:
    LinearRegression = None

from services.models import Booking, DemandForecast, Invoice, Payment, Rating, Service, WorkerProfile, WorkerWelfare


def _expire_stale_requests(queryset=None):
    """Flip pending bookings whose 60s request window has passed to 'cancelled'.
    Runs on dashboard load (MVP polling approach) — status is always stored in the DB,
    never faked purely in JavaScript."""
    qs = queryset if queryset is not None else Booking.objects.all()
    stale = qs.filter(status="pending", expires_at__isnull=False, expires_at__lt=timezone.now())
    stale.update(status="cancelled")


def home(request):
    context = {
        "verified_worker_count": WorkerProfile.objects.filter(is_verified=True).count(),
        "service_count": Service.objects.filter(is_available=True).count(),
        "completed_job_count": Booking.objects.filter(status="completed").count(),
    }
    return render(request, "home.html", context)


@login_required
def customer_dashboard(request):
    _expire_stale_requests(Booking.objects.filter(customer=request.user))
    bookings = (Booking.objects.filter(customer=request.user)
                .select_related("service", "worker", "worker__user")
                .select_related("rating")
                .order_by("-created_at"))
    context = {
        "bookings": bookings,
        "category_choices": Service.CATEGORY_CHOICES,
        "recent_bookings": bookings[:8],
        "total_bookings": bookings.count(),
        "pending_bookings": bookings.filter(status="pending").count(),
        "accepted_bookings": bookings.filter(status__in=["accepted", "in_progress"]).count(),
        "completed_bookings": bookings.filter(status="completed").count(),
        "unpaid_completed": bookings.filter(status="completed").exclude(payment__status="verified").count(),
    }
    return render(request, "dashboard/customer.html", context)


@login_required
def customer_bookings(request):
    status = request.GET.get("status", "")
    bookings = Booking.objects.filter(customer=request.user).select_related("service", "worker", "worker__user").order_by("-created_at")
    if status in {"pending", "accepted", "in_progress", "completed", "cancelled"}:
        bookings = bookings.filter(status=status)
    return render(request, "dashboard/customer_bookings.html", {"bookings": bookings, "active_status": status})


@login_required
def worker_dashboard(request):
    profile = WorkerProfile.objects.filter(user=request.user).first()
    if profile:
        _expire_stale_requests(Booking.objects.filter(worker=profile))
    context = {
        "profile": profile, "active_bookings": 0, "completed_jobs": 0, "rating": 0,
        "total_earnings": 0, "booking_requests": [], "worker_bookings": [],
        "services_count": 0, "pending_payments": 0, "welfare": None,
    }
    if profile:
        bookings = Booking.objects.filter(worker=profile).select_related("customer", "service").order_by("-created_at")
        welfare, _ = WorkerWelfare.objects.get_or_create(worker=profile)
        context.update({
            "worker_bookings": bookings[:12],
            "active_bookings": bookings.filter(status__in=["pending", "accepted", "in_progress"]).count(),
            "completed_jobs": bookings.filter(status="completed").count(),
            "rating": profile.rating,
            "total_earnings": bookings.filter(status="completed").aggregate(total=Sum("amount"))["total"] or 0,
            "booking_requests": bookings.filter(status="pending")[:10],
            "services_count": Service.objects.filter(worker=request.user).count(),
            "pending_payments": Payment.objects.filter(booking__worker=profile, status="submitted").count(),
            "welfare": welfare,
        })
    return render(request, "dashboard/worker.html", context)


def _staff(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@user_passes_test(_staff, login_url="login")
def cooperative_dashboard(request):
    today = timezone.localdate()
    start = today - timedelta(days=29)
    workers = WorkerProfile.objects.select_related("user").order_by("-created_at")
    bookings = Booking.objects.select_related("customer", "worker__user", "service").order_by("-created_at")
    payments = Payment.objects.select_related("booking__customer", "booking__service").order_by("-created_at")
    pending_workers = workers.filter(verification_status__in=["pending", "under_review"])
    revenue = Payment.objects.filter(status="verified").aggregate(total=Sum("amount"))["total"] or 0
    pending_payments = payments.filter(status="submitted")

    daily = []
    for i in range(30):
        d = start + timedelta(days=i)
        daily.append({"date": d.strftime("%d %b"), "count": Booking.objects.filter(created_at__date=d).count()})

    category_counts = list(Booking.objects.filter(created_at__date__gte=start).values("service__category").annotate(total=Count("id")).order_by("-total"))
    forecasts = []
    choices = dict(Service.CATEGORY_CHOICES)
    for row in category_counts[:6]:
        cat = row["service__category"]
        series = [Booking.objects.filter(created_at__date=start + timedelta(days=i), service__category=cat).count() for i in range(30)]
        total_bookings = sum(series)
        if total_bookings < 5:
            # Not enough real history for a trustworthy forecast — say so instead of guessing.
            forecasts.append({"category": choices.get(cat, cat.title()), "predicted": None, "confidence": None, "model": None, "insufficient_data": True, "sample_size": total_bookings})
            continue
        if LinearRegression and any(series):
            x = [[i] for i in range(30)]
            model = LinearRegression().fit(x, series)
            pred = max(0, round(float(sum(model.predict([[i] for i in range(30, 37)]))), 1))
            confidence = min(95, max(65, round(70 + min(sum(series), 30) / 3)))
            model_name = "Linear trend"
        else:
            pred = round(sum(series[-7:]) / 7, 1) if any(series[-7:]) else 0
            confidence = min(90, round(55 + sum(series) * 2))
            model_name = "7-day moving average"
        forecasts.append({"category": choices.get(cat, cat.title()), "predicted": pred, "confidence": confidence, "model": model_name})
        for offset in range(1, 8):
            DemandForecast.objects.update_or_create(category=cat, forecast_date=today + timedelta(days=offset), defaults={"predicted_bookings": pred / 7 if pred else 0, "confidence": confidence, "model_name": model_name})

    welfare_active = WorkerProfile.objects.filter(insurance_status="active").count()
    context = {
        "workers": workers, "pending_workers": pending_workers[:12], "bookings": bookings[:12], "payments": payments[:20],
        "worker_count": workers.count(), "verified_workers": workers.filter(is_verified=True).count(),
        "pending_verification": pending_workers.count(), "booking_count": Booking.objects.count(), "revenue": revenue,
        "pending_payments": pending_payments.count(), "daily": daily, "daily_json": json.dumps(daily), "category_counts": category_counts, "forecasts": forecasts,
        "welfare_active": welfare_active,
    }
    return render(request, "dashboard/cooperative.html", context)


@login_required
@user_passes_test(_staff, login_url="login")
def worker_verification(request, worker_id):
    worker = get_object_or_404(WorkerProfile.objects.select_related("user"), id=worker_id)
    if request.method == "POST":
        action = request.POST.get("action", "").strip()
        note = request.POST.get("note", "").strip()
        if action == "approve":
            worker.is_verified = True
            worker.verification_status = "verified"
            worker.verified_at = timezone.now()
            worker.verification_note = note or "Approved by cooperative administrator."
            worker.save(update_fields=["is_verified", "verification_status", "verified_at", "verification_note"])
            messages.success(request, f"{worker.display_name} is now a verified Sahyog worker.")
            return redirect("cooperative_dashboard")
        if action == "reject":
            worker.is_verified = False
            worker.verification_status = "rejected"
            worker.verified_at = None
            worker.verification_note = note or "Verification was not approved. Please update your documents and resubmit."
            worker.save(update_fields=["is_verified", "verification_status", "verified_at", "verification_note"])
            messages.warning(request, f"Verification for {worker.display_name} was rejected.")
            return redirect("cooperative_dashboard")
        messages.error(request, "Please choose a valid verification action.")
    return render(request, "dashboard/worker_verification.html", {"worker": worker})


@login_required
@user_passes_test(_staff, login_url="login")
def verify_payment(request, payment_id):
    payment = get_object_or_404(Payment.objects.select_related("booking"), id=payment_id)
    if request.method != "POST":
        return redirect("cooperative_dashboard")
    payment.status = "verified"
    payment.verified_at = timezone.now()
    payment.verified_by = request.user
    payment.rejection_reason = ""
    payment.save(update_fields=["status", "verified_at", "verified_by", "rejection_reason"])
    invoice = Invoice.objects.filter(booking=payment.booking).first()
    if invoice:
        invoice.status = "paid"
        invoice.paid_at = timezone.now()
        invoice.save(update_fields=["status", "paid_at"])
    messages.success(request, f"Payment #{payment.id} verified and added to the cooperative ledger.")
    return redirect("cooperative_dashboard")


@login_required
@user_passes_test(_staff, login_url="login")
def reject_payment(request, payment_id):
    payment = get_object_or_404(Payment.objects.select_related("booking"), id=payment_id)
    if request.method != "POST":
        return redirect("cooperative_dashboard")
    payment.status = "rejected"
    payment.verified_at = None
    payment.verified_by = None
    payment.rejection_reason = request.POST.get("reason", "Payment could not be verified by the cooperative.").strip()
    payment.save(update_fields=["status", "verified_at", "verified_by", "rejection_reason"])
    messages.warning(request, f"Payment #{payment.id} was rejected. The customer can resubmit it.")
    return redirect("cooperative_dashboard")
