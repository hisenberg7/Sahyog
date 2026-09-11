from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("services", "0006_booking_expires_at")]
    operations = [
        migrations.AlterField(
            model_name="payment",
            name="payment_method",
            field=models.CharField(choices=[("upi", "UPI / Online"), ("cash", "Cash")], default="upi", max_length=20),
        ),
    ]
