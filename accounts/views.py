from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from datetime import timedelta
import secrets

import requests

from .forms import RegistrationForm
from .models import UserProfile


# ============================================================
# EMAIL OTP HELPERS
# ============================================================

def _generate_email_otp():
    """
    Generate a secure 6-digit OTP.
    """
    return f"{secrets.randbelow(1000000):06d}"


def _send_email_otp(request, email):
    """
    Generate and send a 6-digit OTP to the user's email.
    OTP remains valid for 5 minutes.
    """

    otp = _generate_email_otp()

    request.session["email_otp"] = otp
    request.session["email_otp_email"] = email
    request.session["email_otp_expires"] = (
        timezone.now() + timedelta(minutes=5)
    ).isoformat()
    request.session["email_otp_attempts"] = 0

    send_mail(
        subject="Sahyog Email Verification OTP",
        message=(
            f"Hello,\n\n"
            f"Your Sahyog verification OTP is: {otp}\n\n"
            f"This OTP is valid for 5 minutes.\n\n"
            f"If you did not request this OTP, please ignore this email.\n\n"
            f"Regards,\n"
            f"Sahyog Team"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

    return otp


def _clear_email_otp(request):
    """
    Remove OTP information from the session.
    """
    request.session.pop("email_otp", None)
    request.session.pop("email_otp_email", None)
    request.session.pop("email_otp_expires", None)
    request.session.pop("email_otp_attempts", None)


# ============================================================
# REGISTRATION
# ============================================================

def register(request):

    if request.method == "POST":

        form = RegistrationForm(request.POST)

        if form.is_valid():

            email = form.cleaned_data.get("email", "").strip().lower()

            # Check whether this email already belongs to an account.
            if User.objects.filter(email__iexact=email).exists():
                messages.error(
                    request,
                    "An account with this email already exists. Please login instead."
                )
                return render(
                    request,
                    "accounts/register.html",
                    {"form": form},
                )

            try:
                # Send OTP before creating the account.
                _send_email_otp(request, email)

                # Store registration form data temporarily in session.
                request.session["pending_registration"] = request.POST.dict()

                messages.success(
                    request,
                    f"A verification OTP has been sent to {email}."
                )

                return redirect("verify_email_otp")

            except Exception:
                messages.error(
                    request,
                    "We could not send the verification email right now. Please try again."
                )

    else:
        form = RegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )


# ============================================================
# EMAIL OTP VERIFICATION
# ============================================================

def verify_email_otp(request):

    pending_registration = request.session.get(
        "pending_registration"
    )

    otp_email = request.session.get(
        "email_otp_email"
    )

    saved_otp = request.session.get(
        "email_otp"
    )

    expires_at = request.session.get(
        "email_otp_expires"
    )

    if not pending_registration or not otp_email or not saved_otp:
        messages.error(
            request,
            "No active email verification found. Please register again."
        )
        return redirect("register")

    # Check OTP expiry.
    if expires_at:
        try:
            expiry_time = timezone.datetime.fromisoformat(
                expires_at
            )

            if timezone.is_naive(expiry_time):
                expiry_time = timezone.make_aware(
                    expiry_time
                )

            if timezone.now() > expiry_time:
                _clear_email_otp(request)
                request.session.pop(
                    "pending_registration",
                    None
                )

                messages.error(
                    request,
                    "Your OTP has expired. Please register again."
                )

                return redirect("register")

        except (ValueError, TypeError):
            _clear_email_otp(request)
            request.session.pop(
                "pending_registration",
                None
            )

            messages.error(
                request,
                "OTP verification expired. Please register again."
            )

            return redirect("register")

    if request.method == "POST":

        attempts = request.session.get("email_otp_attempts", 0)
        if attempts >= 5:
            _clear_email_otp(request)
            request.session.pop("pending_registration", None)
            messages.error(request, "Too many incorrect attempts. Please register again to receive a new OTP.")
            return redirect("register")

        entered_otp = request.POST.get(
            "otp",
            ""
        ).strip()

        if not entered_otp.isdigit() or len(entered_otp) != 6:
            messages.error(
                request,
                "Please enter a valid 6-digit OTP."
            )

            return render(
                request,
                "accounts/verify_email_otp.html",
                {
                    "email": otp_email,
                },
            )

        if secrets.compare_digest(
            entered_otp,
            str(saved_otp)
        ):

            # Re-check email before creating account.
            if User.objects.filter(
                email__iexact=otp_email
            ).exists():

                _clear_email_otp(request)
                request.session.pop(
                    "pending_registration",
                    None
                )

                messages.error(
                    request,
                    "An account with this email already exists. Please login instead."
                )

                return redirect("login")

            # Rebuild and validate the registration form
            # from the session data.
            form = RegistrationForm(
                pending_registration
            )

            if not form.is_valid():
                _clear_email_otp(request)
                request.session.pop(
                    "pending_registration",
                    None
                )

                messages.error(
                    request,
                    "Registration data expired or is invalid. Please register again."
                )

                return redirect("register")

            # Create the actual Django user only AFTER OTP verification.
            user = form.save()

            # Mark email as verified.
            try:
                profile = user.profile
                profile.email_verified = True
                profile.save(
                    update_fields=["email_verified"]
                )
            except Exception:
                UserProfile.objects.update_or_create(
                    user=user,
                    defaults={
                        "role": "customer",
                        "phone": "",
                        "email_verified": True,
                    },
                )

            # Clean OTP/session data.
            _clear_email_otp(request)
            request.session.pop(
                "pending_registration",
                None
            )

            # Login after successful verification.
            login(request, user)

            messages.success(
                request,
                "Your email has been verified and your Sahyog account has been created successfully."
            )

            try:
                role = user.profile.role
            except Exception:
                role = "customer"

            return redirect(
                "worker_dashboard"
                if role == "worker"
                else "customer_dashboard"
            )

        request.session["email_otp_attempts"] = attempts + 1
        messages.error(
            request,
            f"Incorrect OTP. Please try again. ({4 - attempts} attempt(s) remaining)"
        )

    return render(
        request,
        "accounts/verify_email_otp.html",
        {
            "email": otp_email,
        },
    )


# ============================================================
# RESEND EMAIL OTP
# ============================================================

def resend_email_otp(request):

    pending_registration = request.session.get(
        "pending_registration"
    )

    if not pending_registration:
        messages.error(
            request,
            "Your registration session has expired. Please register again."
        )
        return redirect("register")

    email = (
        pending_registration.get(
            "email",
            ""
        )
        .strip()
        .lower()
    )

    if not email:
        messages.error(
            request,
            "Email address not found. Please register again."
        )
        return redirect("register")

    try:
        _send_email_otp(
            request,
            email
        )

        messages.success(
            request,
            f"A new OTP has been sent to {email}."
        )

    except Exception:
        messages.error(
            request,
            "Could not send a new OTP right now. Please try again."
        )

    return redirect("verify_email_otp")


# ============================================================
# NORMAL USERNAME + PASSWORD LOGIN
# ============================================================

def login_view(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:

            login(
                request,
                user
            )

            messages.success(
                request,
                f"Welcome back, {user.first_name or user.username}!"
            )

            try:
                role = user.profile.role
            except Exception:
                role = "customer"

            if role == "worker":
                return redirect(
                    "worker_dashboard"
                )

            return redirect(
                "customer_dashboard"
            )

        messages.error(
            request,
            "Invalid username or password."
        )

    return render(
        request,
        "accounts/login.html",
        {
            "google_enabled": bool(
                settings.GOOGLE_CLIENT_ID
                and settings.GOOGLE_CLIENT_SECRET
            )
        },
    )


# ============================================================
# GOOGLE OAUTH
# ============================================================

GOOGLE_AUTH_URL = (
    "https://accounts.google.com/o/oauth2/v2/auth"
)

GOOGLE_TOKEN_URL = (
    "https://oauth2.googleapis.com/token"
)

GOOGLE_USERINFO_URL = (
    "https://www.googleapis.com/oauth2/v3/userinfo"
)


def _google_redirect_uri(request):

    return (
        settings.GOOGLE_OAUTH_REDIRECT_URI
        or request.build_absolute_uri(
            reverse("google_callback")
        )
    )


def google_login(request):

    if not (
        settings.GOOGLE_CLIENT_ID
        and settings.GOOGLE_CLIENT_SECRET
    ):

        messages.error(
            request,
            "Google login is not configured on this server yet. Please use username and password."
        )

        return redirect("login")

    state = secrets.token_urlsafe(24)

    request.session[
        "google_oauth_state"
    ] = state

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": _google_redirect_uri(request),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
    }

    query = "&".join(
        f"{k}={requests.utils.quote(str(v))}"
        for k, v in params.items()
    )

    return redirect(
        f"{GOOGLE_AUTH_URL}?{query}"
    )


def google_callback(request):

    if not (
        settings.GOOGLE_CLIENT_ID
        and settings.GOOGLE_CLIENT_SECRET
    ):

        messages.error(
            request,
            "Google login is not configured on this server."
        )

        return redirect("login")

    error = request.GET.get(
        "error"
    )

    if error:

        messages.error(
            request,
            "Google login was cancelled."
        )

        return redirect("login")

    state = request.GET.get(
        "state",
        ""
    )

    if (
        not state
        or state
        != request.session.pop(
            "google_oauth_state",
            None
        )
    ):

        messages.error(
            request,
            "Google login session expired. Please try again."
        )

        return redirect("login")

    code = request.GET.get(
        "code"
    )

    if not code:

        messages.error(
            request,
            "Google did not return an authorization code."
        )

        return redirect("login")

    try:

        token_resp = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": _google_redirect_uri(request),
                "grant_type": "authorization_code",
            },
            timeout=10,
        )

        token_resp.raise_for_status()

        access_token = token_resp.json().get(
            "access_token"
        )

        userinfo_resp = requests.get(
            GOOGLE_USERINFO_URL,
            headers={
                "Authorization":
                f"Bearer {access_token}"
            },
            timeout=10,
        )

        userinfo_resp.raise_for_status()

        info = userinfo_resp.json()

    except requests.RequestException:

        messages.error(
            request,
            "Could not complete Google login right now. Please use username and password."
        )

        return redirect("login")

    email = (
        info.get(
            "email",
            ""
        )
        .strip()
        .lower()
    )

    if not email:

        messages.error(
            request,
            "Google did not share an email address. Please use username and password."
        )

        return redirect("login")

    user = User.objects.filter(
        email=email
    ).first()

    if not user:

        base_username = (
            email.split("@")[0]
            or "sahyoguser"
        )[:24]

        username = base_username

        suffix = 1

        while User.objects.filter(
            username=username
        ).exists():

            username = (
                f"{base_username}{suffix}"
            )

            suffix += 1

        user = User.objects.create(
            username=username,
            email=email,
            first_name=info.get(
                "given_name",
                ""
            )[:30],
            last_name=info.get(
                "family_name",
                ""
            )[:30],
        )

        user.set_unusable_password()

        user.save()

        UserProfile.objects.get_or_create(
            user=user,
            defaults={
                "role": "customer",
                "phone": "",
                "email_verified": True,
            },
        )

    else:

        # Existing Google/verified email accounts
        # remain usable without another OTP.
        try:
            profile = user.profile

            if not profile.email_verified:
                profile.email_verified = True
                profile.save(
                    update_fields=[
                        "email_verified"
                    ]
                )

        except Exception:
            pass

    login(
        request,
        user,
        backend="django.contrib.auth.backends.ModelBackend"
    )

    messages.success(
        request,
        f"Welcome, {user.first_name or user.username}!"
    )

    try:
        role = user.profile.role
    except Exception:
        role = "customer"

    return redirect(
        "worker_dashboard"
        if role == "worker"
        else "customer_dashboard"
    )


# ============================================================
# LOGOUT
# ============================================================

def logout_view(request):

    logout(request)

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect("home")