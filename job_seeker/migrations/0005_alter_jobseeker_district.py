# Generated by Django 4.2.17 on 2025-03-07 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('job_seeker', '0004_jobseeker_district_jobseeker_sector_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobseeker',
            name='District',
            field=models.CharField(blank=True, default='', max_length=30, null=True),
        ),
    ]
