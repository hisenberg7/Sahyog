from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("services", "0005_booking_status_extended")]
    operations = [
        migrations.AddField(
            model_name="booking",
            name="expires_at",
            field=models.DateTimeField(blank=True, null=True, help_text="Pending request auto-expires after this time."),
        ),
    ]
