from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0006_nickname_change_limits"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="last_password_changed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
