# Generated by Django 3.1.14 on 2023-04-11 15:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0012_imagetag"),
    ]

    operations = [
        migrations.CreateModel(
            name="ControlLocation",
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
                ("name", models.CharField(blank=True, max_length=100)),
                ("description", models.CharField(blank=True, max_length=100)),
                ("selected", models.BooleanField(default=False)),
            ],
            options={
                "abstract": False,
            },
        ),
    ]