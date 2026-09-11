from django.urls import path

from . import views


app_name = "services"


urlpatterns = [
    path(
        "",
        views.service_list,
        name="service_list",
    ),

    path(
        "book/<int:service_id>/",
        views.create_booking,
        name="create_booking",
    ),

    path(
        "payment/<int:booking_id>/",
        views.payment_page,
        name="payment",
    ),

    path(
        "rate/<int:booking_id>/",
        views.rate_booking,
        name="rate_booking",
    ),

    path(
        "invoice/<int:booking_id>/",
        views.invoice_page,
        name="invoice",
    ),

    path(
        "welfare/",
        views.welfare_page,
        name="welfare",
    ),

    # ------------------------------------------------------
    # DYNAMIC BILLING / EXTRA CHARGES
    # ------------------------------------------------------

    path(
        "booking/<int:booking_id>/extra-charge/add/",
        views.add_extra_charge,
        name="add_extra_charge",
    ),

    path(
        "extra-charge/<int:charge_id>/respond/",
        views.respond_extra_charge,
        name="respond_extra_charge",
    ),

    # ------------------------------------------------------
    # BOOKING STATUS
    # ------------------------------------------------------

    path(
        "booking/<int:booking_id>/accept/",
        views.accept_booking,
        name="accept_booking",
    ),

    path(
        "booking/<int:booking_id>/reject/",
        views.reject_booking,
        name="reject_booking",
    ),

    path(
        "booking/<int:booking_id>/on-the-way/",
        views.on_the_way,
        name="on_the_way",
    ),

    path(
        "booking/<int:booking_id>/arrived/",
        views.mark_arrived,
        name="mark_arrived",
    ),

    path(
        "booking/<int:booking_id>/start/",
        views.start_job,
        name="start_job",
    ),

    path(
        "booking/<int:booking_id>/complete/",
        views.complete_job,
        name="complete_job",
    ),

    # ------------------------------------------------------
    # CASH COLLECTION
    # ------------------------------------------------------

    path(
        "booking/<int:booking_id>/cash-received/",
        views.confirm_cash_received,
        name="confirm_cash_received",
    ),

    # ------------------------------------------------------
    # LIVE WORKER LOCATION
    # ------------------------------------------------------

    path(
        "booking/<int:booking_id>/location/update/",
        views.update_worker_location,
        name="update_worker_location",
    ),

    path(
        "booking/<int:booking_id>/location/",
        views.worker_location_api,
        name="worker_location_api",
    ),

    # ------------------------------------------------------
    # WORKER SERVICES
    # ------------------------------------------------------

    path(
        "add/",
        views.add_service,
        name="add_service",
    ),

    path(
        "my-services/",
        views.my_services,
        name="my_services",
    ),

    path(
        "edit/<int:service_id>/",
        views.edit_service,
        name="edit_service",
    ),

    path(
        "delete/<int:service_id>/",
        views.delete_service,
        name="delete_service",
    ),

    path(
        "profile/",
        views.worker_profile,
        name="worker_profile",
    ),
]