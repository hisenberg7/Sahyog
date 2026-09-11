from django.urls import path

from .views import (
    google_callback,
    google_login,
    login_view,
    logout_view,
    register,
    verify_email_otp,
    resend_email_otp,
)


urlpatterns = [

    path(
        "register/",
        register,
        name="register"
    ),

    path(
        "login/",
        login_view,
        name="login"
    ),

    path(
        "logout/",
        logout_view,
        name="logout"
    ),

    # Google Login
    path(
        "google/login/",
        google_login,
        name="google_login"
    ),

    path(
        "google/callback/",
        google_callback,
        name="google_callback"
    ),

    # Email OTP
    path(
        "verify-email-otp/",
        verify_email_otp,
        name="verify_email_otp"
    ),

    path(
        "resend-email-otp/",
        resend_email_otp,
        name="resend_email_otp"
    ),

]