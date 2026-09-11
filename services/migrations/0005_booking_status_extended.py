from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("services", "0004_mvp_upgrade")]
    operations = [
        migrations.AlterField(
            model_name="booking",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"), ("accepted", "Accepted"),
                    ("on_the_way", "On the Way"), ("arrived", "Arrived"),
                    ("in_progress", "In Progress"), ("completed", "Completed"),
                    ("cancelled", "Cancelled"),
                ],
                default="pending", max_length=20,
            ),
        ),
    ]
