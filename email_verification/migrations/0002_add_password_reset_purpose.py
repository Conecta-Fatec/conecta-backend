from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("email_verification", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="emailverification",
            name="purpose",
            field=models.CharField(
                choices=[
                    ("register", "Cadastro"),
                    ("password_reset", "Recuperação de senha"),
                ],
                default="register",
                max_length=20,
            ),
        ),
    ]
