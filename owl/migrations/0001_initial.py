# Generated by Django 4.1.7 on 2023-03-08 20:45

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Domains",
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
                ("domain", models.CharField(max_length=200)),
                ("keywords", models.BigIntegerField()),
                ("traffic", models.BigIntegerField()),
                ("cost", models.BigIntegerField()),
                ("rank", models.IntegerField()),
            ],
        ),
    ]
