# Generated by Django 4.2.17 on 2025-02-19 07:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jobCategoryApp', '0001_initial'),
        ('job_offer_app', '0002_joboffer_offer_type_alter_joboffer_company_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='joboffer',
            name='job_category',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='job_category', to='jobCategoryApp.jobcategory'),
        ),
        migrations.AlterField(
            model_name='joboffer',
            name='experience_level',
            field=models.CharField(choices=[('entry', 'Entry Level'), ('intermidiate', 'Intermediate'), ('mid', 'Mid Level'), ('senior or executive', 'Senior or Executive Level')], max_length=20),
        ),
        migrations.AlterField(
            model_name='joboffer',
            name='job_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_type', to='jobCategoryApp.jobtype'),
        ),
        migrations.AlterField(
            model_name='joboffer',
            name='offer_type',
            field=models.CharField(choices=[('company', 'Company'), ('individual', 'Individual'), ('government', 'Government'), ('non-government organization', 'Non-Government Organization')], default='individual', max_length=50),
        ),
    ]
