# Generated by Django 3.0.7 on 2020-06-19 22:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('moneypool', '0007_auto_20200618_1653'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='equb',
            name='end_date',
        ),
        migrations.RemoveField(
            model_name='equb',
            name='received',
        ),
        migrations.RemoveField(
            model_name='equb',
            name='start_date',
        ),
        migrations.RemoveField(
            model_name='equb',
            name='started',
        ),
        migrations.CreateModel(
            name='BalanceManager',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_managed', models.DateTimeField(blank=True, null=True)),
                ('finished_rounds', models.IntegerField(blank=True, default=0)),
                ('started', models.BooleanField(default=False)),
                ('start_date', models.DateTimeField(blank=True, null=True)),
                ('end_date', models.DateTimeField(blank=True, null=True)),
                ('equb', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='account_manager', to='moneypool.Equb')),
                ('received', models.ManyToManyField(blank=True, related_name='received_equb_managers', to='moneypool.Client')),
            ],
        ),
    ]
