# Generated by Django 5.2.4 on 2025-07-19 06:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bankapi', '0005_remove_userprofile_adhaar_remove_userprofile_pincode_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='balance',
            field=models.DecimalField(decimal_places=2, default=100000.0, max_digits=12),
        ),
    ]
