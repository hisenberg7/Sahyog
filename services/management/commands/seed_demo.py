from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from accounts.models import UserProfile
from services.models import Service, WorkerProfile, WorkerWelfare


class Command(BaseCommand):
    help = "Create a small local Sahyog demo network for hackathon testing."

    def add_arguments(self, parser):
        parser.add_argument("--password", default="Demo@12345", help="Password for demo accounts")

    def handle(self, *args, **options):
        password = options["password"]
        workers = [
            ("rahul_demo", "Rahul", "Kumar", "Electrician", "ITI Electrician", 5, "28.6139", "77.2090", "499"),
            ("priya_demo", "Priya", "Sharma", "Plumber", "Certified Plumber", 4, "28.6200", "77.2150", "399"),
            ("aman_demo", "Aman", "Singh", "Carpenter", "ITI Carpenter", 7, "28.6050", "77.1980", "699"),
        ]
        for username, first, last, skill, cert, exp, lat, lng, price in workers:
            user, created = User.objects.get_or_create(username=username, defaults={"first_name": first, "last_name": last, "email": f"{username}@example.com"})
            if created:
                user.set_password(password)
                user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user, defaults={"role": "worker", "phone": "9999999999"})
            profile.role = "worker"
            profile.phone = profile.phone or "9999999999"
            profile.save()
            worker, _ = WorkerProfile.objects.get_or_create(user=user)
            worker.phone = profile.phone
            worker.skill = skill
            worker.certification = cert
            worker.experience = exp
            worker.address = "Demo service area, New Delhi"
            worker.latitude = float(lat)
            worker.longitude = float(lng)
            worker.rating = Decimal("4.8")
            worker.total_reviews = 24
            worker.is_verified = True
            worker.verification_status = "verified"
            worker.is_available = True
            worker.save()
            WorkerWelfare.objects.get_or_create(worker=worker, defaults={"enrolled": True, "monthly_contribution": Decimal("99"), "coverage_amount": Decimal("200000")})
            Service.objects.get_or_create(name=f"{skill} Home Service", worker=user, defaults={"category": skill.lower(), "description": f"Trusted {skill.lower()} support from a verified cooperative worker.", "base_price": Decimal(price), "experience": exp, "latitude": float(lat), "longitude": float(lng), "is_available": True})

        customer, created = User.objects.get_or_create(username="customer_demo", defaults={"first_name": "Demo", "last_name": "Customer", "email": "customer@example.com"})
        if created:
            customer.set_password(password)
            customer.save()
        customer_profile, _ = UserProfile.objects.get_or_create(user=customer, defaults={"role": "customer", "phone": "9999999998"})
        customer_profile.role = "customer"
        customer_profile.save()

        admin, created = User.objects.get_or_create(username="cooperative_admin", defaults={"first_name": "Cooperative", "last_name": "Admin", "email": "admin@example.com", "is_staff": True, "is_superuser": True})
        if created:
            admin.set_password(password)
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        self.stdout.write(self.style.SUCCESS("Demo data created."))
        self.stdout.write(f"Demo worker/customer password: {password}")
        self.stdout.write("Worker: rahul_demo / priya_demo / aman_demo")
        self.stdout.write("Customer: customer_demo")
        self.stdout.write("Cooperative admin: cooperative_admin")
