# Generated by Django 3.0.7 on 2020-06-20 22:25

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('moneypool', '0009_auto_20200619_2234'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bid',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('started', models.BooleanField(default=False)),
                ('highest_bid', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('all_bids', django.contrib.postgres.fields.jsonb.JSONField(blank=True)),
                ('equb', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='bid', to='moneypool.Equb')),
                ('highest_bidder', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='moneypool.Client')),
            ],
        ),
    ]
