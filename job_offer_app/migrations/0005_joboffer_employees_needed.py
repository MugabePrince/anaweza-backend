# Generated by Django 4.2.17 on 2025-03-03 07:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('job_offer_app', '0004_alter_joboffer_benefits_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='joboffer',
            name='employees_needed',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
