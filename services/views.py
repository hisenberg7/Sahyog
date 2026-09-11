import math
import json
import base64
import hashlib
import hmac
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import BookingForm, RatingForm, ServiceForm, WorkerProfileForm, WorkerWelfareForm
from .models import (
    BillingApproval,
    Booking,
    ExtraCharge,
    Invoice,
    Payment,
    Rating,
    Service,
    WorkerProfile,
    WorkerWelfare,
)

# Configurable matching constants — single source of truth, not hard-coded per call site.
NEARBY_RADIUS_KM = getattr(settings, "WORKER_MATCH_RADIUS_KM", 5.0)
AVERAGE_URBAN_SPEED_KMH = getattr(settings, "AVERAGE_URBAN_SPEED_KMH", 20.0)
DEFAULT_JOB_DURATION_MINUTES = getattr(settings, "DEFAULT_JOB_DURATION_MINUTES", 60)
# Statuses that make a worker genuinely busy for overlap checks (pending requests can still expire/be rejected).
BUSY_STATUSES = ("accepted", "on_the_way", "arrived", "in_progress")


def _eta_minutes(distance_km):
    """Approximate travel time at a configurable average urban speed. None in, None out — never a fake number."""
    if distance_km is None:
        return None
    return max(1, round((distance_km / AVERAGE_URBAN_SPEED_KMH) * 60))


def _worker_available_for_slot(worker_profile, sched_date, sched_time, exclude_booking_id=None):
    """Simple overlap check: is this worker free around the requested date/time?
    Uses a fixed job-duration window rather than a full duration model, per MVP scope."""
    if not worker_profile.is_available:
        return False
    window = timedelta(minutes=DEFAULT_JOB_DURATION_MINUTES)
    requested_dt = datetime.combine(sched_date, sched_time)
    conflicts = Booking.objects.filter(worker=worker_profile, scheduled_date=sched_date, status__in=BUSY_STATUSES)
    if exclude_booking_id:
        conflicts = conflicts.exclude(id=exclude_booking_id)
    for other in conflicts:
        other_dt = datetime.combine(other.scheduled_date, other.scheduled_time)
        if abs((requested_dt - other_dt).total_seconds()) < window.total_seconds():
            return False
    return True


def _distance_km(lat1, lon1, lat2, lon2):
    try:
        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    except (TypeError, ValueError):
        return None

    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = (
        math.sin(dp / 2) ** 2
        + math.cos(p1)
        * math.cos(p2)
        * math.sin(dl / 2) ** 2
    )

    return round(
        r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)),
        2,
    )


def _worker_score(worker, distance):
    rating = float(worker.rating or 0)
    availability = 1 if worker.is_available else 0
    verification = 1 if worker.is_verified else 0
    distance_component = max(0, 5 - (distance or 5))

    return round(
        min(
            100,
            verification * 45
            + availability * 20
            + rating * 5
            + distance_component * 2,
        ),
        1,
    )


def _fee(amount):
    return (
        Decimal(amount)
        * Decimal(str(getattr(settings, "PLATFORM_FEE_PERCENT", 5)))
        / Decimal("100")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def _emergency_fee():
    """Return the configured emergency fee without inventing a business amount."""
    return Decimal(str(getattr(settings, "SAHYOG_EMERGENCY_FEE", "0"))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def _recalculate_booking_total(booking):
    """Rebuild the customer payable amount from the approved billing breakdown."""
    base = Decimal(booking.base_amount or 0)
    emergency = Decimal(booking.emergency_fee or 0)
    approved_extras = (
        ExtraCharge.objects.filter(
            booking=booking,
            status="approved",
        )
        .values_list("total", flat=True)
    )
    extra_total = sum(
        (Decimal(value or 0) for value in approved_extras),
        Decimal("0"),
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    booking.approved_extra_amount = extra_total
    booking.amount = (
        base + emergency + extra_total
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    booking.save(
        update_fields=[
            "approved_extra_amount",
            "amount",
        ]
    )
    return booking.amount


def _ensure_invoice(booking):
    _recalculate_booking_total(booking)
    fee = _fee(booking.amount)

    invoice, created = Invoice.objects.get_or_create(
        booking=booking,
        defaults={
            "invoice_number": f"SAY-{timezone.now():%Y%m%d}-{booking.id:05d}",
            "subtotal": booking.amount,
            "platform_fee": fee,
            "worker_earnings": booking.amount - fee,
            "total": booking.amount,
        },
    )

    # An unpaid/unverified invoice must always reflect the current approved total.
    # Paid invoices are intentionally frozen so a later billing change cannot
    # silently alter an already-settled amount.
    if invoice.status != "paid":
        invoice.subtotal = booking.amount
        invoice.platform_fee = fee
        invoice.worker_earnings = booking.amount - fee
        invoice.total = booking.amount
        invoice.save(
            update_fields=[
                "subtotal",
                "platform_fee",
                "worker_earnings",
                "total",
            ]
        )

    return invoice


def _payment_locked(booking):
    payment = Payment.objects.filter(booking=booking).first()
    return bool(
        payment
        and payment.status == "verified"
    )


@login_required
def add_extra_charge(request, booking_id):
    """Worker proposes an itemized extra charge for customer approval."""
    booking = get_object_or_404(
        Booking.objects.select_related("worker", "customer", "service"),
        id=booking_id,
        worker__user=request.user,
    )

    if request.method != "POST":
        messages.error(request, "Invalid request.")
        return redirect("worker_dashboard")

    if booking.status not in ("accepted", "on_the_way", "arrived", "in_progress"):
        messages.error(
            request,
            "Extra charges can only be proposed for an active booking.",
        )
        return redirect("worker_dashboard")

    if _payment_locked(booking):
        messages.error(
            request,
            "This booking is already paid and its billing cannot be changed.",
        )
        return redirect("worker_dashboard")

    charge_type = request.POST.get("charge_type", "other").strip()
    description = request.POST.get("description", "").strip()
    quantity_raw = request.POST.get("quantity", "1").strip()
    unit_price_raw = request.POST.get("unit_price", "").strip()

    valid_types = {value for value, _label in ExtraCharge.CHARGE_TYPE_CHOICES}
    if charge_type not in valid_types:
        messages.error(request, "Please choose a valid charge type.")
        return redirect("worker_dashboard")

    if not description:
        messages.error(request, "Please provide a description for the extra charge.")
        return redirect("worker_dashboard")

    try:
        quantity = Decimal(quantity_raw)
        unit_price = Decimal(unit_price_raw)
    except Exception:
        messages.error(request, "Quantity and unit price must be valid numbers.")
        return redirect("worker_dashboard")

    if quantity <= 0 or unit_price <= 0:
        messages.error(request, "Quantity and unit price must be greater than zero.")
        return redirect("worker_dashboard")

    with transaction.atomic():
        ExtraCharge.objects.create(
            booking=booking,
            worker=booking.worker,
            charge_type=charge_type,
            description=description[:255],
            quantity=quantity,
            unit_price=unit_price,
            status="pending",
        )

    messages.success(
        request,
        "Extra charge sent to the customer for approval.",
    )
    return redirect("worker_dashboard")


@login_required
def respond_extra_charge(request, charge_id):
    """Customer approves or rejects one pending worker-proposed charge."""
    charge = get_object_or_404(
        ExtraCharge.objects.select_related("booking", "booking__customer"),
        id=charge_id,
    )
    booking = charge.booking

    if request.user != booking.customer:
        return redirect("home")

    if request.method != "POST":
        messages.error(request, "Invalid request.")
        return redirect("customer_dashboard")

    decision = request.POST.get("decision", "").strip().lower()
    note = request.POST.get("customer_note", "").strip()

    if decision not in ("approved", "rejected"):
        messages.error(request, "Please choose approve or reject.")
        return redirect("customer_dashboard")

    if charge.status != "pending":
        messages.info(request, "This extra charge has already been answered.")
        return redirect("customer_dashboard")

    if _payment_locked(booking):
        messages.error(
            request,
            "This booking is already paid and its billing cannot be changed.",
        )
        return redirect("customer_dashboard")

    with transaction.atomic():
        charge.status = decision
        charge.customer_note = note
        charge.responded_at = timezone.now()
        charge.save(
            update_fields=[
                "status",
                "customer_note",
                "responded_at",
                "total",
            ]
        )

        BillingApproval.objects.create(
            booking=booking,
            customer=request.user,
            decision=decision,
            note=note,
        )

        _recalculate_booking_total(booking)

        # Keep any existing unpaid/submitted payment aligned with the newly
        # approved final amount. A submitted payment will still need
        # cooperative verification for that final amount.
        payment = Payment.objects.filter(booking=booking).first()
        if payment and payment.status != "verified":
            payment.amount = booking.amount
            payment.save(update_fields=["amount"])

        invoice = Invoice.objects.filter(booking=booking).first()
        if invoice and invoice.status != "paid":
            _ensure_invoice(booking)

    messages.success(
        request,
        "Extra charge approved and added to the final bill."
        if decision == "approved"
        else "Extra charge rejected.",
    )
    return redirect("customer_dashboard")


@login_required
def add_service(request):
    if request.method == "POST":
        form = ServiceForm(request.POST)

        if form.is_valid():
            service = form.save(commit=False)
            service.worker = request.user
            service.save()

            messages.success(
                request,
                "Your service has been added successfully.",
            )

            return redirect("worker_dashboard")

    else:
        form = ServiceForm()

    return render(
        request,
        "services/add_service.html",
        {"form": form},
    )


@login_required
def my_services(request):
    services = (
        Service.objects
        .filter(worker=request.user)
        .order_by("-created_at")
    )

    return render(
        request,
        "services/my_services.html",
        {"services": services},
    )


@login_required
def edit_service(request, service_id):
    service = get_object_or_404(
        Service,
        id=service_id,
        worker=request.user,
    )

    if request.method == "POST":
        form = ServiceForm(
            request.POST,
            instance=service,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Your service has been updated successfully.",
            )

            return redirect("services:my_services")

    else:
        form = ServiceForm(instance=service)

    return render(
        request,
        "services/edit_service.html",
        {
            "form": form,
            "service": service,
        },
    )


@login_required
def delete_service(request, service_id):
    service = get_object_or_404(
        Service,
        id=service_id,
        worker=request.user,
    )

    if request.method == "POST":
        service.delete()

        messages.success(
            request,
            "Your service has been deleted.",
        )

        return redirect("services:my_services")

    return render(
        request,
        "services/delete_service.html",
        {"service": service},
    )


@login_required
def worker_profile(request):
    profile, _ = WorkerProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":
        form = WorkerProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
        )

        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user

            if "verification_document" in request.FILES:
                profile.verification_status = "under_review"
                profile.is_verified = False
                profile.verified_at = None
                profile.verification_note = (
                    "Document submitted for cooperative review."
                )

            profile.save()

            messages.success(
                request,
                "Profile saved successfully.",
            )

            return redirect("worker_dashboard")

    else:
        form = WorkerProfileForm(instance=profile)

    return render(
        request,
        "services/worker_profile.html",
        {
            "form": form,
            "profile": profile,
        },
    )


def service_list(request):
    services = list(
        Service.objects
        .filter(is_available=True)
        .select_related(
            "worker",
            "worker__workerprofile",
        )
        .order_by("-created_at")
    )

    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()

    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    booking_type = request.GET.get("booking_type", "now") if request.GET.get("booking_type") in ("now", "schedule") else "now"
    sched_date_raw = request.GET.get("sched_date", "").strip()
    sched_time_raw = request.GET.get("sched_time", "").strip()
    sched_date = sched_time = None
    schedule_error = None
    if booking_type == "schedule":
        try:
            sched_date = datetime.strptime(sched_date_raw, "%Y-%m-%d").date() if sched_date_raw else None
            sched_time = datetime.strptime(sched_time_raw, "%H:%M").time() if sched_time_raw else None
        except ValueError:
            sched_date = sched_time = None
        if sched_date and sched_date < timezone.localdate():
            schedule_error = "Please choose today or a future date."
            sched_date = sched_time = None
        elif sched_date and sched_time and sched_date == timezone.localdate() and datetime.combine(sched_date, sched_time) <= timezone.localtime().replace(tzinfo=None):
            schedule_error = "Please choose a time that hasn't already passed today."
            sched_date = sched_time = None

    if query:
        needle = query.lower()

        services = [
            s
            for s in services
            if (
                needle
                in f"{s.name} {s.description} {s.category}".lower()
                or needle
                in (
                    s.worker.workerprofile.skill
                    if hasattr(s.worker, "workerprofile")
                    else ""
                ).lower()
            )
        ]

    if category:
        services = [
            s for s in services
            if s.category == category
        ]

    location_selected = bool(lat and lng)
    no_workers_reason = None

    for service in services:
        profile = getattr(
            service.worker,
            "workerprofile",
            None,
        )

        service.distance_km = (
            _distance_km(
                lat,
                lng,
                profile.latitude,
                profile.longitude,
            )
            if (
                lat
                and lng
                and profile
            )
            else None
        )
        service.eta_minutes = _eta_minutes(service.distance_km) if booking_type == "now" else None

        service.matching_score = (
            _worker_score(
                profile,
                service.distance_km,
            )
            if profile
            else 0
        )

    if location_selected:
        # HARD backend 5 KM cutoff — workers beyond this are dropped, not just re-sorted.
        services = [
            s for s in services
            if s.distance_km is not None and s.distance_km <= NEARBY_RADIUS_KM
        ]
        if booking_type == "schedule" and sched_date and sched_time:
            services = [
                s for s in services
                if hasattr(s.worker, "workerprofile") and _worker_available_for_slot(s.worker.workerprofile, sched_date, sched_time)
            ]

    services.sort(
        key=lambda s: (
            not getattr(
                s.worker.workerprofile,
                "is_verified",
                False,
            ),
            not getattr(
                s.worker.workerprofile,
                "is_available",
                False,
            ),
            s.distance_km is None,
            (
                s.distance_km
                if s.distance_km is not None
                else 9999
            ),
            -s.matching_score,
        )
    )

    map_markers = []

    if lat and lng:
        for service in services:
            profile = getattr(
                service.worker,
                "workerprofile",
                None,
            )

            if (
                profile
                and profile.latitude is not None
                and profile.longitude is not None
            ):
                map_markers.append(
                    {
                        "name": profile.display_name,
                        "lat": profile.latitude,
                        "lng": profile.longitude,
                        "service": service.name,
                        "distance": service.distance_km,
                        "verified": profile.is_verified,
                    }
                )

    if not services:
        if not location_selected:
            no_workers_reason = "no_location"
        elif booking_type == "schedule":
            no_workers_reason = "none_available_at_time"
        else:
            no_workers_reason = "none_within_radius"

    return render(
        request,
        "services/service_list.html",
        {
            "services": services,
            "query": query,
            "category": category,
            "categories": Service.CATEGORY_CHOICES,
            "user_lat": lat,
            "user_lng": lng,
            "map_markers_json": json.dumps(
                map_markers
            ),
            "booking_type": booking_type,
            "sched_date": sched_date_raw,
            "sched_time": sched_time_raw,
            "schedule_error": schedule_error,
            "no_workers_reason": no_workers_reason,
            "radius_km": NEARBY_RADIUS_KM,
        },
    )


@login_required
def create_booking(request, service_id):
    service = get_object_or_404(
        Service,
        id=service_id,
        is_available=True,
    )

    if not service.worker:
        messages.error(
            request,
            "This service currently has no worker assigned.",
        )

        return redirect("services:service_list")

    worker_profile = getattr(
        service.worker,
        "workerprofile",
        None,
    )

    if not worker_profile:
        messages.error(
            request,
            "The worker profile is not available.",
        )

        return redirect("services:service_list")

    if not worker_profile.is_verified:
        messages.warning(
            request,
            "This provider is not verified yet. Please choose a verified worker.",
        )

        return redirect("services:service_list")

    emergency = request.GET.get("emergency") == "1"

    initial_lat = request.GET.get("lat", "")
    initial_lng = request.GET.get("lng", "")

    preview_distance = (
        _distance_km(
            initial_lat,
            initial_lng,
            worker_profile.latitude,
            worker_profile.longitude,
        )
        if (
            initial_lat
            and initial_lng
        )
        else None
    )

    preview_eta = _eta_minutes(preview_distance)

    if request.method == "POST":
        booking_type = request.POST.get("booking_type") if request.POST.get("booking_type") in ("now", "schedule") else "now"
        form = BookingForm(request.POST)

        if form.is_valid():
            booking = form.save(
                commit=False
            )

            # Re-check worker state at submission time — GET-time checks are not enough,
            # since verification/availability can change between viewing and submitting.
            worker_profile.refresh_from_db()
            if not worker_profile.is_verified:
                messages.error(request, "This worker is no longer verified. Please choose another worker.")
                return redirect("services:service_list")
            if not worker_profile.is_available:
                messages.error(request, "This worker is currently unavailable. Please choose another worker.")
                return redirect("services:service_list")

            distance_km = _distance_km(
                booking.latitude,
                booking.longitude,
                worker_profile.latitude,
                worker_profile.longitude,
            )
            if distance_km is None:
                messages.error(request, "We couldn't verify the worker's location. Please try again.")
                return render(request, "services/create_booking.html", {
                    "form": form, "service": service, "worker_profile": worker_profile, "is_emergency": emergency,
                    "preview_distance": preview_distance, "preview_eta": preview_eta,
                    "customer_lat": initial_lat, "customer_lng": initial_lng, "booking_type": booking_type,
                })
            if distance_km > NEARBY_RADIUS_KM:
                messages.error(request, f"This worker is outside the {NEARBY_RADIUS_KM:g} km service area for your selected location. Please choose a nearer worker.")
                return redirect(f"{reverse('services:service_list')}?lat={initial_lat}&lng={initial_lng}&category={service.category}")

            if booking_type == "now":
                # Present bookings always use the current date/time server-side — never trust a future date
                # the client might have supplied, so "Book Now" can't accidentally become a scheduled booking.
                booking.scheduled_date = timezone.localdate()
                booking.scheduled_time = timezone.localtime().time()
            else:
                if booking.scheduled_date < timezone.localdate() or (
                    booking.scheduled_date == timezone.localdate() and booking.scheduled_time <= timezone.localtime().time()
                ):
                    messages.error(request, "Please choose a future date and time for a scheduled booking.")
                    return render(request, "services/create_booking.html", {
                        "form": form, "service": service, "worker_profile": worker_profile, "is_emergency": emergency,
                        "preview_distance": preview_distance, "preview_eta": preview_eta,
                        "customer_lat": initial_lat, "customer_lng": initial_lng, "booking_type": booking_type,
                    })
                if not _worker_available_for_slot(worker_profile, booking.scheduled_date, booking.scheduled_time):
                    messages.error(request, "This worker already has a booking around that time. Please choose another time or worker.")
                    return redirect(f"{reverse('services:service_list')}?lat={initial_lat}&lng={initial_lng}&category={service.category}&booking_type=schedule")

            booking.customer = request.user
            booking.worker = worker_profile
            booking.service = service
            booking.base_amount = Decimal(service.base_price or 0)
            booking.emergency_fee = _emergency_fee() if emergency else Decimal("0.00")
            booking.approved_extra_amount = Decimal("0.00")
            booking.amount = (
                booking.base_amount + booking.emergency_fee
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            booking.status = "pending"
            booking.is_emergency = emergency
            booking.booking_type = booking_type
            booking.expires_at = (
                timezone.now()
                + timedelta(seconds=60)
            )

            booking.distance_km = distance_km

            booking.matching_score = _worker_score(
                worker_profile,
                booking.distance_km,
            )

            booking.save()

            messages.success(
                request,
                (
                    "Emergency request sent with priority."
                    if emergency
                    else "Your booking request has been sent successfully."
                ),
            )

            return redirect(
                "customer_dashboard"
            )

    else:
        booking_type = request.GET.get("booking_type") if request.GET.get("booking_type") in ("now", "schedule") else "now"
        form = BookingForm(
            initial={
                "latitude": initial_lat,
                "longitude": initial_lng,
                "scheduled_date": request.GET.get("sched_date") or timezone.localdate(),
                "scheduled_time": request.GET.get("sched_time") or timezone.localtime().time().strftime("%H:%M"),
            }
        )

    return render(
        request,
        "services/create_booking.html",
        {
            "form": form,
            "service": service,
            "worker_profile": worker_profile,
            "is_emergency": emergency,
            "preview_distance": preview_distance,
            "preview_eta": preview_eta,
            "customer_lat": initial_lat,
            "customer_lng": initial_lng,
            "booking_type": booking_type,
            "radius_km": NEARBY_RADIUS_KM,
        },
    )


def _razorpay_credentials():
    """Read Razorpay credentials from Django settings or the environment."""
    key_id = str(
        getattr(settings, "RAZORPAY_KEY_ID", os.getenv("RAZORPAY_KEY_ID", ""))
        or ""
    ).strip()
    key_secret = str(
        getattr(settings, "RAZORPAY_KEY_SECRET", os.getenv("RAZORPAY_KEY_SECRET", ""))
        or ""
    ).strip()
    return key_id, key_secret


def _razorpay_request(method, path, payload=None):
    """Make a server-side Razorpay API request without exposing secrets."""
    key_id, key_secret = _razorpay_credentials()
    if not key_id or not key_secret:
        raise RuntimeError("Razorpay API credentials are not configured.")

    credentials = base64.b64encode(
        f"{key_id}:{key_secret}".encode("utf-8")
    ).decode("ascii")

    body = None
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    if payload is not None:
        body = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        f"https://api.razorpay.com{path}",
        data=body,
        headers=headers,
        method=method.upper(),
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8"))
            message = detail.get("error", {}).get("description") or detail.get("error", {}).get("reason")
        except Exception:
            message = None
        raise RuntimeError(message or f"Razorpay API returned HTTP {exc.code}.") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("Could not connect to Razorpay. Please try again.") from exc


def _create_razorpay_order(booking):
    """Create one Razorpay order for the booking's current final payable amount."""
    amount_paise = int(
        (Decimal(booking.amount) * Decimal("100")).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    )

    if amount_paise <= 0:
        raise RuntimeError("The payment amount must be greater than zero.")

    order = _razorpay_request(
        "POST",
        "/v1/orders",
        {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"sahyog_booking_{booking.id}",
            "notes": {
                "booking_id": str(booking.id),
                "service": str(booking.service.name)[:100],
            },
        },
    )

    order_id = order.get("id")
    if not order_id:
        raise RuntimeError("Razorpay did not return an order ID.")

    return order_id


def _verify_razorpay_signature(order_id, payment_id, signature):
    """Verify the Checkout signature using the server-side API secret."""
    _key_id, key_secret = _razorpay_credentials()
    if not key_secret:
        raise RuntimeError("Razorpay API secret is not configured.")

    generated = hmac.new(
        key_secret.encode("utf-8"),
        f"{order_id}|{payment_id}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(generated, signature or "")


def _fetch_razorpay_payment(payment_id):
    return _razorpay_request(
        "GET",
        f"/v1/payments/{payment_id}",
    )


def _fetch_razorpay_order(order_id):
    return _razorpay_request(
        "GET",
        f"/v1/orders/{order_id}",
    )


@login_required
def payment_page(request, booking_id):
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        customer=request.user,
    )

    if booking.status != "completed":
        messages.error(
            request,
            "Payment is available after the job is completed.",
        )
        return redirect("customer_dashboard")

    _recalculate_booking_total(booking)

    payment, _ = Payment.objects.get_or_create(
        booking=booking,
        defaults={
            "amount": booking.amount,
            "payment_method": "upi",
            "status": "pending",
        },
    )

    if payment.status != "verified":
        payment.amount = booking.amount
        payment.save(update_fields=["amount"])

    key_id, key_secret = _razorpay_credentials()
    razorpay_order_id = payment.razorpay_order_id

    if request.method == "POST":
        method = request.POST.get("payment_method", "razorpay").strip().lower()

        if method == "cash":
            if payment.status == "verified":
                messages.info(request, "This payment has already been verified.")
                return redirect("customer_dashboard")

            payment.payment_method = "cash"
            payment.upi_transaction_id = ""
            payment.amount = booking.amount
            payment.status = "submitted"
            payment.rejection_reason = ""
            payment.save(
                update_fields=[
                    "payment_method",
                    "upi_transaction_id",
                    "amount",
                    "status",
                    "rejection_reason",
                ]
            )

            _ensure_invoice(booking)

            messages.success(
                request,
                "Cash payment recorded. The cooperative will confirm collection.",
            )
            return redirect("customer_dashboard")

        if method != "razorpay":
            messages.error(request, "Please choose a valid payment method.")
            return redirect("services:payment", booking_id=booking.id)

        payment_id = request.POST.get("razorpay_payment_id", "").strip()
        returned_order_id = request.POST.get("razorpay_order_id", "").strip()
        signature = request.POST.get("razorpay_signature", "").strip()

        if not payment_id or not returned_order_id or not signature:
            messages.error(
                request,
                "Razorpay payment details were incomplete. Please try again.",
            )
            return redirect("services:payment", booking_id=booking.id)

        if not payment.razorpay_order_id:
            messages.error(
                request,
                "No Razorpay order is associated with this booking. Please retry the payment.",
            )
            return redirect("services:payment", booking_id=booking.id)

        if returned_order_id != payment.razorpay_order_id:
            messages.error(
                request,
                "Razorpay order verification failed. Please retry the payment.",
            )
            return redirect("services:payment", booking_id=booking.id)

        try:
            if not _verify_razorpay_signature(
                payment.razorpay_order_id,
                payment_id,
                signature,
            ):
                messages.error(
                    request,
                    "Razorpay signature verification failed. The payment was not accepted.",
                )
                return redirect("services:payment", booking_id=booking.id)

            gateway_payment = _fetch_razorpay_payment(payment_id)
            gateway_order_id = str(gateway_payment.get("order_id") or "")
            gateway_amount = int(gateway_payment.get("amount") or 0)
            expected_amount = int(
                (Decimal(booking.amount) * Decimal("100")).quantize(
                    Decimal("1"),
                    rounding=ROUND_HALF_UP,
                )
            )
            gateway_currency = str(gateway_payment.get("currency") or "").upper()
            gateway_status = str(gateway_payment.get("status") or "").lower()

            if gateway_order_id != payment.razorpay_order_id:
                raise RuntimeError("Razorpay payment does not belong to this order.")

            if gateway_amount != expected_amount:
                raise RuntimeError("Razorpay payment amount does not match the final booking amount.")

            if gateway_currency != "INR":
                raise RuntimeError("Razorpay payment currency is not INR.")

            if gateway_status != "captured":
                raise RuntimeError(
                    f"Razorpay payment is not captured yet (status: {gateway_status or 'unknown'})."
                )

        except RuntimeError as exc:
            messages.error(request, str(exc))
            return redirect("services:payment", booking_id=booking.id)

        payment.payment_method = "razorpay"
        payment.upi_transaction_id = ""
        payment.razorpay_payment_id = payment_id
        payment.razorpay_order_id = payment.razorpay_order_id
        payment.amount = booking.amount
        payment.status = "verified"
        payment.rejection_reason = ""
        payment.verified_at = timezone.now()
        payment.verified_by = None
        payment.save(
            update_fields=[
                "payment_method",
                "upi_transaction_id",
                "razorpay_payment_id",
                "razorpay_order_id",
                "amount",
                "status",
                "rejection_reason",
                "verified_at",
                "verified_by",
            ]
        )

        _ensure_invoice(booking)

        messages.success(
            request,
            "Razorpay payment verified successfully.",
        )
        return redirect("customer_dashboard")

    if not key_id or not key_secret:
        messages.error(
            request,
            "Razorpay is not configured. Please add the Razorpay test API keys to the server environment.",
        )
    elif payment.status != "verified":
        try:
            recreate_order = not razorpay_order_id

            if razorpay_order_id:
                existing_order = _fetch_razorpay_order(razorpay_order_id)
                existing_amount = int(existing_order.get("amount") or 0)
                current_amount = int(
                    (Decimal(booking.amount) * Decimal("100")).quantize(
                        Decimal("1"),
                        rounding=ROUND_HALF_UP,
                    )
                )
                existing_status = str(existing_order.get("status") or "").lower()

                # Never reuse an order whose amount no longer matches the
                # final billing total, or an order that has already been paid.
                recreate_order = (
                    existing_amount != current_amount
                    or existing_status == "paid"
                )

            if recreate_order:
                razorpay_order_id = _create_razorpay_order(booking)
                payment.razorpay_order_id = razorpay_order_id
                payment.amount = booking.amount
                payment.payment_method = "razorpay"
                payment.status = "pending"
                payment.rejection_reason = ""
                payment.save(
                    update_fields=[
                        "razorpay_order_id",
                        "amount",
                        "payment_method",
                        "status",
                        "rejection_reason",
                    ]
                )
        except RuntimeError as exc:
            razorpay_order_id = ""
            messages.error(request, f"Razorpay order creation failed: {exc}")

    return render(
        request,
        "services/payment.html",
        {
            "booking": booking,
            "payment": payment,
            "razorpay_key_id": key_id,
            "razorpay_order_id": razorpay_order_id,
        },
    )


@login_required
def rate_booking(request, booking_id):
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        customer=request.user,
    )

    if booking.status != "completed":
        messages.error(
            request,
            "You can rate a service only after the job is completed.",
        )

        return redirect(
            "customer_dashboard"
        )

    if Rating.objects.filter(
        booking=booking
    ).exists():
        messages.info(
            request,
            "You have already rated this service.",
        )

        return redirect(
            "customer_dashboard"
        )

    if request.method == "POST":
        form = RatingForm(request.POST)

        if form.is_valid():
            rating = form.save(
                commit=False
            )

            rating.booking = booking
            rating.save()

            worker = booking.worker

            ratings = Rating.objects.filter(
                booking__worker=worker
            )

            worker.total_reviews = ratings.count()

            worker.rating = round(
                sum(
                    r.rating
                    for r in ratings
                )
                / worker.total_reviews,
                2,
            )

            worker.save(
                update_fields=[
                    "rating",
                    "total_reviews",
                ]
            )

            messages.success(
                request,
                "Thank you! Your rating and feedback have been submitted.",
            )

            return redirect(
                "customer_dashboard"
            )

    else:
        form = RatingForm()

    return render(
        request,
        "services/rate_booking.html",
        {
            "booking": booking,
            "form": form,
        },
    )


def _booking_action(
    request,
    booking_id,
    from_status,
    to_status,
    success_message,
):
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        worker__user=request.user,
    )

    if request.method != "POST":
        messages.error(
            request,
            "Invalid request.",
        )

        return redirect(
            "worker_dashboard"
        )

    valid_from = (
        (from_status,)
        if isinstance(from_status, str)
        else from_status
    )

    if booking.status not in valid_from:
        messages.error(
            request,
            "This booking is not in the correct state for this action.",
        )

        return redirect(
            "worker_dashboard"
        )

    booking.status = to_status

    booking.save(
        update_fields=[
            "status"
        ]
    )

    messages.success(
        request,
        success_message,
    )

    return redirect(
        "worker_dashboard"
    )


@login_required
def accept_booking(request, booking_id):
    return _booking_action(
        request,
        booking_id,
        "pending",
        "accepted",
        "Booking accepted successfully.",
    )


@login_required
def reject_booking(request, booking_id):
    return _booking_action(
        request,
        booking_id,
        "pending",
        "cancelled",
        "Booking rejected.",
    )


@login_required
def on_the_way(request, booking_id):
    return _booking_action(
        request,
        booking_id,
        "accepted",
        "on_the_way",
        "You're on the way to the customer.",
    )


@login_required
def mark_arrived(request, booking_id):
    return _booking_action(
        request,
        booking_id,
        "on_the_way",
        "arrived",
        "Marked as arrived.",
    )


@login_required
def start_job(request, booking_id):
    return _booking_action(
        request,
        booking_id,
        ("accepted", "arrived"),
        "in_progress",
        "Job started successfully.",
    )


@login_required
def complete_job(request, booking_id):
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        worker__user=request.user,
    )

    if (
        request.method != "POST"
        or booking.status != "in_progress"
    ):
        messages.error(
            request,
            "Only jobs in progress can be completed.",
        )

        return redirect(
            "worker_dashboard"
        )

    with transaction.atomic():
        booking.status = "completed"

        booking.save(
            update_fields=[
                "status"
            ]
        )

        _ensure_invoice(booking)

    messages.success(
        request,
        "Job completed. Invoice generated and payment is now available to the customer.",
    )

    return redirect(
        "worker_dashboard"
    )



# ==========================================================
# WORKER CASH COLLECTION
# ==========================================================

@login_required
def confirm_cash_received(request, booking_id):
    """
    Worker confirms that the customer has physically paid the
    final cash amount. Only the assigned worker can confirm it.
    """
    booking = get_object_or_404(
        Booking.objects.select_related("customer", "service", "worker"),
        id=booking_id,
        worker__user=request.user,
    )

    if request.method != "POST":
        messages.error(request, "Invalid request.")
        return redirect("worker_dashboard")

    payment = Payment.objects.filter(booking=booking).first()

    if not payment or payment.payment_method != "cash":
        messages.error(request, "This booking is not marked for cash payment.")
        return redirect("worker_dashboard")

    if payment.status == "verified":
        messages.info(request, "Cash payment has already been confirmed.")
        return redirect("worker_dashboard")

    if payment.status != "submitted":
        messages.error(
            request,
            "Cash collection is not pending for this booking.",
        )
        return redirect("worker_dashboard")

    with transaction.atomic():
        payment.amount = booking.amount
        payment.status = "verified"
        payment.rejection_reason = ""
        payment.verified_at = timezone.now()
        payment.verified_by = request.user
        payment.save(
            update_fields=[
                "amount",
                "status",
                "rejection_reason",
                "verified_at",
                "verified_by",
            ]
        )

        invoice = _ensure_invoice(booking)
        if invoice.status != "paid":
            invoice.status = "paid"
            invoice.paid_at = timezone.now()
            invoice.save(update_fields=["status", "paid_at"])

    messages.success(
        request,
        f"Cash received successfully. ₹{booking.amount} payment is now verified.",
    )
    return redirect("worker_dashboard")

# ==========================================================
# LIVE WORKER LOCATION API
# ==========================================================

@login_required
def update_worker_location(request, booking_id):
    """
    Worker browser sends GPS coordinates here.

    Only the worker assigned to this booking can update it.
    Location is accepted only for active travel/job states.
    """

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        worker__user=request.user,
    )

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "message": "POST request required.",
            },
            status=405,
        )

    if booking.status not in (
        "on_the_way",
        "arrived",
        "in_progress",
    ):
        return JsonResponse(
            {
                "success": False,
                "message": "Location tracking is not active for this booking.",
            },
            status=400,
        )

    try:
        latitude = float(
            request.POST.get("latitude")
        )
        longitude = float(
            request.POST.get("longitude")
        )
    except (
        TypeError,
        ValueError,
    ):
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid GPS coordinates.",
            },
            status=400,
        )

    if not (
        -90 <= latitude <= 90
        and -180 <= longitude <= 180
    ):
        return JsonResponse(
            {
                "success": False,
                "message": "GPS coordinates are out of range.",
            },
            status=400,
        )

    booking.live_latitude = latitude
    booking.live_longitude = longitude
    booking.location_updated_at = timezone.now()

    booking.save(
        update_fields=[
            "live_latitude",
            "live_longitude",
            "location_updated_at",
        ]
    )

    distance_to_customer = _distance_km(
        latitude,
        longitude,
        booking.latitude,
        booking.longitude,
    )

    eta_minutes = (
        max(
            1,
            round(
                (distance_to_customer / AVERAGE_URBAN_SPEED_KMH) * 60
            ),
        )
        if distance_to_customer is not None
        else None
    )

    return JsonResponse(
        {
            "success": True,
            "latitude": latitude,
            "longitude": longitude,
            "distance_km": distance_to_customer,
            "eta_minutes": eta_minutes,
            "updated_at": booking.location_updated_at.isoformat(),
        }
    )


@login_required
def worker_location_api(request, booking_id):
    """
    Customer reads the latest worker location.
    Only the booking customer, assigned worker or staff
    can access this endpoint.
    """

    booking = get_object_or_404(
        Booking.objects.select_related(
            "worker",
            "worker__user",
            "customer",
        ),
        id=booking_id,
    )

    allowed = (
        request.user == booking.customer
        or request.user == booking.worker.user
        or request.user.is_staff
    )

    if not allowed:
        return JsonResponse(
            {
                "success": False,
                "message": "You are not allowed to view this location.",
            },
            status=403,
        )

    active = booking.status in (
        "on_the_way",
        "arrived",
        "in_progress",
    )

    distance_to_customer = None
    eta_minutes = None

    if (
        booking.live_latitude is not None
        and booking.live_longitude is not None
        and booking.latitude is not None
        and booking.longitude is not None
    ):
        distance_to_customer = _distance_km(
            booking.live_latitude,
            booking.live_longitude,
            booking.latitude,
            booking.longitude,
        )

        if distance_to_customer is not None:
            eta_minutes = max(
                1,
                round(
                    (distance_to_customer / AVERAGE_URBAN_SPEED_KMH) * 60
                ),
            )

    return JsonResponse(
        {
            "success": True,
            "active": active,
            "status": booking.status,
            "latitude": booking.live_latitude,
            "longitude": booking.live_longitude,
            "customer_latitude": booking.latitude,
            "customer_longitude": booking.longitude,
            "distance_km": distance_to_customer,
            "eta_minutes": eta_minutes,
            "location_updated_at": (
                booking.location_updated_at.isoformat()
                if booking.location_updated_at
                else None
            ),
        }
    )


@login_required
def invoice_page(request, booking_id):
    booking = get_object_or_404(
        Booking,
        id=booking_id,
    )

    if (
        request.user != booking.customer
        and request.user != booking.worker.user
        and not request.user.is_staff
    ):
        return redirect("home")

    invoice = _ensure_invoice(
        booking
    )

    payment = Payment.objects.filter(
        booking=booking
    ).first()

    return render(
        request,
        "services/invoice.html",
        {
            "booking": booking,
            "invoice": invoice,
            "payment": payment,
        },
    )


@login_required
def welfare_page(request):
    if not hasattr(
        request.user,
        "workerprofile",
    ):
        messages.info(
            request,
            "Worker welfare is available for worker accounts.",
        )

        return redirect("home")

    worker = request.user.workerprofile

    welfare, _ = WorkerWelfare.objects.get_or_create(
        worker=worker
    )

    if request.method == "POST":
        form = WorkerWelfareForm(
            request.POST,
            instance=welfare,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Your welfare preferences have been updated.",
            )

            return redirect(
                "services:welfare"
            )

    else:
        form = WorkerWelfareForm(
            instance=welfare
        )

    return render(
        request,
        "services/welfare.html",
        {
            "profile": worker,
            "welfare": welfare,
            "form": form,
        },
    )