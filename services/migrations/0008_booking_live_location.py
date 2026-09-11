from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0007_payment_cash_method"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="live_latitude",
            field=models.FloatField(
                blank=True,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="booking",
            name="live_longitude",
            field=models.FloatField(
                blank=True,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="booking",
            name="location_updated_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
            ),
        ),
    ]