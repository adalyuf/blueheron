# Generated by Django 4.1.7 on 2023-03-25 19:36

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ranker", "0015_alter_domain_domain"),
    ]

    operations = [
        migrations.AlterField(
            model_name="message",
            name="order",
            field=models.IntegerField(default=100),
        ),
        migrations.AlterField(
            model_name="producttemplate",
            name="order",
            field=models.IntegerField(default=100),
        ),
    ]
