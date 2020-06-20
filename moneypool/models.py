from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.utils import timezone
import datetime
import random


class Client(models.Model):
    user = models.OneToOneField(to=User, on_delete=models.CASCADE)
    equbs = models.ManyToManyField("Equb", blank=True, related_name='clients')
    friends = models.ManyToManyField("self", blank=True)
    bank_account = models.DecimalField(max_digits=13, decimal_places=2)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=4.5)

    def __str__(self):
        return str(self.user.username)


class Equb(models.Model):
    name = models.CharField(max_length=150, unique=True, null=True)
    value = models.DecimalField(max_digits=13, decimal_places=2)
    capacity = models.IntegerField()
    cycle = models.DurationField(default=datetime.timedelta(days=1))

    def __str__(self):
        return str(self.name)

    # def select_winner(self):
    #     all_members = self.clients.all()
    #     received = self.received.all()
    #     not_received = all_members.difference(received)
    #     winner = random.choice(not_received)
    #     self.received.add(winner)
    #     return winner
    #
    # def update_winner_account(self):
    #     amount = self.value
    #     winner = self.select_winner()
    #     winner.bank_account += amount
    #     winner.save()
    #
    # def collect_money(self):
    #     all_members = self.clients.all()
    #     capacity = self.capacity
    #     amount = self.value
    #     deduction = amount / capacity
    #     for member in all_members:
    #         member.bank_account -= deduction
    #         member.save()


# class Member(models.Model):
#     client = models.OneToOneField(to=Client, on_delete=models.CASCADE)
#     received = models.BooleanField(default=False)


class BalanceManager(models.Model):
    equb = models.OneToOneField(to=Equb, on_delete=models.CASCADE, related_name='balance_manager')
    received = models.ManyToManyField(Client, blank=True, related_name='received_equb_managers')
    last_managed = models.DateTimeField(null=True, blank=True)
    finished_rounds = models.IntegerField(blank=True, default=0)
    started = models.BooleanField(default=False)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.equb.name) + ' balance manager'

    def __select_winner(self):
        equb = self.equb
        all_members = equb.clients.all()
        received = self.received.all()
        not_received = all_members.difference(received)
        if not_received:
            winner = random.choice(not_received)
            self.received.add(winner)
            return winner
        else:
            return None

    def update_winner_account(self):
        equb = self.equb
        amount = equb.value
        winner = self.__select_winner()
        if winner:
            winner.bank_account += amount
            winner.save()

    def collect_money(self):
        equb = self.equb
        all_members = equb.clients.all()
        capacity = equb.capacity
        amount = equb.value
        deduction = amount / capacity
        if equb.capacity > self.finished_rounds:
            for member in all_members:
                member.bank_account -= deduction
                member.save()
            self.__update_finished_rounds()
        self.__update_last_managed()

    def __update_last_managed(self):
        self.last_managed = timezone.now()
        self.save()

    def __update_finished_rounds(self):
        self.finished_rounds += 1
        self.save()

