# Generated by Django 4.1.7 on 2023-03-09 16:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("owl", "0003_alter_domain_cost"),
    ]

    operations = [
        migrations.CreateModel(
            name="KeywordFile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("filename", models.CharField(max_length=200)),
                ("filepath", models.CharField(max_length=800)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("primary", models.BooleanField(default=False)),
                (
                    "domain_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="owl.domain"
                    ),
                ),
            ],
        ),
    ]
