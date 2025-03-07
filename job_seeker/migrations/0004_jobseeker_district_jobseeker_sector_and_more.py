# Generated by Django 4.2.17 on 2025-03-07 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('job_seeker', '0003_jobseeker_registration_fee_jobseeker_renewal_fee'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobseeker',
            name='District',
            field=models.CharField(default='', max_length=30),
        ),
        migrations.AddField(
            model_name='jobseeker',
            name='sector',
            field=models.CharField(blank=True, default='', max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='jobseeker',
            name='education_level',
            field=models.CharField(choices=[('none', 'No Formal Education'), ('primary', 'Primary Education'), ('ordinary_level', 'Ordinary Level'), ('secondary', 'Secondary Education'), ('vocational', 'Vocational Training'), ('bachelor', "Bachelor's Degree"), ('master', "Master's Degree"), ('phd', 'PhD')], default='none', max_length=20),
        ),
    ]
