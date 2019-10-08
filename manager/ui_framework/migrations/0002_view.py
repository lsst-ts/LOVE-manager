# Generated by Django 2.2.6 on 2019-10-08 15:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ui_framework', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='View',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creation_timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Creation time')),
                ('update_timestamp', models.DateTimeField(auto_now=True, verbose_name='Last Updated')),
                ('name', models.CharField(max_length=20)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]