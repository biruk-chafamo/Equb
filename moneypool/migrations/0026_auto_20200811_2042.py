# Generated by Django 3.0.7 on 2020-08-11 20:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('moneypool', '0025_auto_20200727_1810'),
    ]

    operations = [
        migrations.AlterField(
            model_name='outbid',
            name='receiver',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='received_outbids', to='moneypool.Client'),
        ),
        migrations.AlterField(
            model_name='outbid',
            name='receiver_bid',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='received_outbids_bids', to='moneypool.Bid'),
        ),
        migrations.AlterField(
            model_name='outbid',
            name='sender_bid',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sent_outbids_bids', to='moneypool.Bid'),
        ),
    ]
