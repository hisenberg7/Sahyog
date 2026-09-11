from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from dashboard.views import (
    cooperative_dashboard, customer_bookings, customer_dashboard, home, reject_payment,
    verify_payment, worker_dashboard, worker_verification,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("", home, name="home"),
    path("accounts/", include("accounts.urls")),
    path("dashboard/customer/", customer_dashboard, name="customer_dashboard"),
    path("dashboard/customer/bookings/", customer_bookings, name="customer_bookings"),
    path("dashboard/worker/", worker_dashboard, name="worker_dashboard"),
    path("dashboard/cooperative/", cooperative_dashboard, name="cooperative_dashboard"),
    path("dashboard/cooperative/worker/<int:worker_id>/", worker_verification, name="worker_verification"),
    path("dashboard/cooperative/payment/<int:payment_id>/verify/", verify_payment, name="verify_payment"),
    path("dashboard/cooperative/payment/<int:payment_id>/reject/", reject_payment, name="reject_payment"),
    path("services/", include("services.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
