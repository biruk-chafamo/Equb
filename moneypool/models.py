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


class BalanceManager(models.Model):
    equb = models.OneToOneField(to=Equb, on_delete=models.CASCADE, related_name='balance_manager')
    received = models.ManyToManyField(Client, blank=True, related_name='received_equb_managers')
    last_managed = models.DateTimeField(null=True, blank=True)
    finished_rounds = models.IntegerField(blank=True, default=0)
    started = models.BooleanField(default=False)
    ended = models.BooleanField(default=False)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.equb.name) + ' balance manager'

    def update_winner_account(self):
        """
        adds the total value of equb to winners account minus the percentage
        of this amount equal to what was bid
        """
        equb = self.equb
        highest_bid = self.equb.bid.highest_bid  # this is in percentage
        amount = equb.value * (1 - highest_bid / 100)  # amount to award highest bidder
        winner = self.equb.bid.select_winner()
        if winner:
            winner.bank_account += amount  # amount = equb value if highest bid = 0
            winner.save()

    def collect_money(self):

        """
        deducts the correct amount from equb members.
        Distributes the highest bid to those who haven't
        received their equbs yet. Those who received their
        equb won't benefit from the bid.
        """

        equb = self.equb
        all_members = equb.clients.all()
        not_received = all_members.difference(self.received.all())
        capacity = equb.capacity
        highest_bid = self.equb.bid.highest_bid   # this is in percentage, eg 4%
        amount = equb.value

        received_deduction = amount / capacity
        not_received_deduction = (amount * (1 - highest_bid / 100)) / not_received.count()

        if capacity > self.finished_rounds:  # ensures equb is not finished
            for member in not_received:
                member.bank_account -= not_received_deduction
                member.save()
            for member in self.received.all():
                member.bank_account -= received_deduction
                member.save()

            # marks the "self.eneded" field to True when all members have received their equb
            if capacity == self.finished_rounds + 1:
                self.__terminate_manager()

            self.__update_finished_rounds()
            self.__update_last_managed()

    def __update_last_managed(self):
        self.last_managed = timezone.now()
        self.save()

    def __update_finished_rounds(self):
        self.finished_rounds += 1
        self.save()

    def __terminate_manager(self):
        self.ended = True
        self.save()


class Bid(models.Model):
    equb = models.OneToOneField(to=Equb, on_delete=models.CASCADE, related_name='bid')
    started = models.BooleanField(default=False, )
    highest_bid = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True)
    highest_bidder = models.ForeignKey(to=Client, on_delete=models.CASCADE, blank=True, null=True)
    all_bids = JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return str(self.equb.name) + ' bidding'

    def select_winner(self):
        """
        Selects highest bidder as winner.
        If there is no bid, winner is randomly selected from
        those who haven't received their equbs yet
        """

        equb = self.equb
        all_members = equb.clients.all()
        received = equb.balance_manager.received.all()
        not_received = all_members.difference(received)
        if not_received:
            if equb.bid.started is True and equb.bid.highest_bidder not in received:
                winner = equb.bid.highest_bidder
            else:
                winner = random.choice(not_received)
            equb.balance_manager.received.add(winner)
            return winner

    def reset_bid(self):
        """
        Must be called after each cycle of equb to reset bid
        """
        self.started = False
        self.highest_bid = 0
        self.highest_bidder = None
        self.all_bids = {}
        self.save()