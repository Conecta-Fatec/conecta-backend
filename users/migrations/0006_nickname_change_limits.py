from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0005_alter_friendship_options_alter_customuser_bio_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="nickname_changes_count",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="customuser",
            name="nickname_change_window_started_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
