# Generated by Django 4.2.17 on 2025-02-11 13:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userApp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='status',
            field=models.BooleanField(default=True),
        ),
    ]
