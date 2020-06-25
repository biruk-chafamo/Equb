# Generated by Django 3.0.7 on 2020-06-20 22:31

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('moneypool', '0010_bid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bid',
            name='all_bids',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='bid',
            name='highest_bid',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=5),
        ),
    ]
