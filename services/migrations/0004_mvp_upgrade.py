from django.db import migrations, models
import django.db.models.deletion


def seed_welfare(apps, schema_editor):
    WorkerProfile = apps.get_model("services", "WorkerProfile")
    WorkerWelfare = apps.get_model("services", "WorkerWelfare")
    for worker in WorkerProfile.objects.all():
        WorkerWelfare.objects.get_or_create(worker=worker)

class Migration(migrations.Migration):
    dependencies=[("services","0003_payment_payment_method_payment_payment_screenshot_and_more")]
    operations=[
        migrations.AddField(model_name="workerprofile",name="verification_document",field=models.FileField(blank=True,null=True,upload_to="verification/")),
        migrations.AddField(model_name="workerprofile",name="verification_status",field=models.CharField(choices=[("pending","Not Submitted"),("under_review","Under Review"),("verified","Verified"),("rejected","Rejected")],default="pending",max_length=20)),
        migrations.AddField(model_name="workerprofile",name="verification_note",field=models.TextField(blank=True,default="")),
        migrations.AddField(model_name="workerprofile",name="verified_at",field=models.DateTimeField(blank=True,null=True)),
        migrations.AddField(model_name="workerprofile",name="insurance_status",field=models.CharField(choices=[("not_enrolled","Not Enrolled"),("pending","Pending"),("active","Active"),("expired","Expired")],default="not_enrolled",max_length=20)),
        migrations.AddField(model_name="workerprofile",name="insurance_provider",field=models.CharField(blank=True,default="",max_length=120)),
        migrations.AddField(model_name="workerprofile",name="insurance_policy_number",field=models.CharField(blank=True,default="",max_length=120)),
        migrations.AddField(model_name="workerprofile",name="insurance_valid_until",field=models.DateField(blank=True,null=True)),
        migrations.AddField(model_name="booking",name="is_emergency",field=models.BooleanField(default=False)),
        migrations.AddField(model_name="booking",name="distance_km",field=models.FloatField(blank=True,null=True)),
        migrations.AddField(model_name="booking",name="matching_score",field=models.FloatField(blank=True,null=True)),
        migrations.AddField(model_name="payment",name="rejection_reason",field=models.TextField(blank=True,default="")),
        migrations.AddField(model_name="payment",name="verified_at",field=models.DateTimeField(blank=True,null=True)),
        migrations.AddField(model_name="payment",name="verified_by",field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="verified_payments",to="auth.user")),
        migrations.CreateModel(name="WorkerWelfare",fields=[("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),("enrolled",models.BooleanField(default=False)),("plan_name",models.CharField(blank=True,default="Community Protection Plan",max_length=120)),("monthly_contribution",models.DecimalField(decimal_places=2,default=0,max_digits=10)),("coverage_amount",models.DecimalField(decimal_places=2,default=0,max_digits=12)),("emergency_support",models.BooleanField(default=True)),("notes",models.TextField(blank=True,default="")),("updated_at",models.DateTimeField(auto_now=True)),("worker",models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,related_name="welfare",to="services.workerprofile"))]),
        migrations.CreateModel(name="Invoice",fields=[("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),("invoice_number",models.CharField(max_length=40,unique=True)),("subtotal",models.DecimalField(decimal_places=2,max_digits=10)),("platform_fee",models.DecimalField(decimal_places=2,default=0,max_digits=10)),("worker_earnings",models.DecimalField(decimal_places=2,max_digits=10)),("total",models.DecimalField(decimal_places=2,max_digits=10)),("status",models.CharField(choices=[("issued","Issued"),("paid","Paid"),("void","Void")],default="issued",max_length=20)),("issued_at",models.DateTimeField(auto_now_add=True)),("paid_at",models.DateTimeField(blank=True,null=True)),("booking",models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,related_name="invoice",to="services.booking"))]),
        migrations.CreateModel(name="DemandForecast",fields=[("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),("category",models.CharField(max_length=50)),("forecast_date",models.DateField()),("predicted_bookings",models.FloatField(default=0)),("confidence",models.FloatField(default=0)),("model_name",models.CharField(default="Moving Average",max_length=80)),("generated_at",models.DateTimeField(auto_now=True))]),
        migrations.AlterUniqueTogether(name="demandforecast",unique_together={("category","forecast_date")}),
        migrations.RunPython(seed_welfare,migrations.RunPython.noop),
    ]
