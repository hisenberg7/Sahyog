from django.contrib import admin
from django.utils import timezone
from .models import Booking, Payment, Rating, Service, WorkerProfile, WorkerWelfare, Invoice, DemandForecast

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display=("name","category","worker","base_price","experience","is_available")
    list_filter=("category","is_available")
    search_fields=("name","description","worker__username")

@admin.register(WorkerProfile)
class WorkerProfileAdmin(admin.ModelAdmin):
    list_display=("user","skill","experience","rating","verification_status","is_verified","is_available")
    list_filter=("verification_status","is_verified","is_available","insurance_status")
    search_fields=("user__username","user__first_name","user__last_name","phone","skill")
    actions=("approve_workers","reject_workers")
    @admin.action(description="Approve selected workers")
    def approve_workers(self,request,queryset):
        queryset.update(is_verified=True,verification_status="verified",verified_at=timezone.now(),verification_note="Approved by cooperative admin.")
    @admin.action(description="Reject selected workers")
    def reject_workers(self,request,queryset):
        queryset.update(is_verified=False,verification_status="rejected",verified_at=None,verification_note="Rejected by cooperative admin. Please update your documents.")

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display=("id","customer","worker","service","scheduled_date","status","is_emergency","amount")
    list_filter=("status","is_emergency","scheduled_date")
    search_fields=("customer__username","worker__user__username","service__name","address")

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display=("id","booking","amount","payment_method","status","upi_transaction_id","created_at")
    list_filter=("status","payment_method")
    search_fields=("upi_transaction_id","booking__customer__username","booking__service__name")
    readonly_fields=("booking","amount","payment_method","upi_transaction_id","payment_screenshot","razorpay_order_id","razorpay_payment_id","created_at")
    actions=("verify_payments","reject_payments")
    @admin.action(description="Verify selected payments")
    def verify_payments(self,request,queryset): queryset.update(status="verified",verified_at=timezone.now(),verified_by=request.user,rejection_reason="")
    @admin.action(description="Reject selected payments")
    def reject_payments(self,request,queryset): queryset.update(status="rejected",verified_at=None,verified_by=None,rejection_reason="Rejected during cooperative review.")

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display=("id","booking","rating","created_at")
    list_filter=("rating",)
    search_fields=("booking__customer__username","booking__service__name","comment")

@admin.register(WorkerWelfare)
class WorkerWelfareAdmin(admin.ModelAdmin):
    list_display=("worker","enrolled","plan_name","monthly_contribution","coverage_amount")
    list_filter=("enrolled","emergency_support")
    search_fields=("worker__user__username","plan_name","insurance_provider")

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display=("invoice_number","booking","subtotal","platform_fee","worker_earnings","status","issued_at")
    list_filter=("status",)
    search_fields=("invoice_number","booking__customer__username")

@admin.register(DemandForecast)
class DemandForecastAdmin(admin.ModelAdmin):
    list_display=("category","forecast_date","predicted_bookings","confidence","model_name","generated_at")
    list_filter=("category","forecast_date")
