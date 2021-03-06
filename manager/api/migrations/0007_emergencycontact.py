# Generated by Django 3.0.7 on 2021-01-05 13:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0006_configfile"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmergencyContact",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "creation_timestamp",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Creation time"
                    ),
                ),
                (
                    "update_timestamp",
                    models.DateTimeField(auto_now=True, verbose_name="Last Updated"),
                ),
                ("subsystem", models.CharField(blank=True, max_length=100)),
                ("name", models.CharField(blank=True, max_length=100)),
                ("contact_info", models.CharField(blank=True, max_length=100)),
                ("email", models.EmailField(max_length=254)),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
