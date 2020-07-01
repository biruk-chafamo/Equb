from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.utils import timezone
import datetime
import random
import logging


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

    def get_cycle(self):
        return MyUtils().print_time(self.cycle)


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

    def percent_completed(self):
        return round((self.finished_rounds / self.equb.capacity) * 100, 2)  # percent of people who have received equb

    def percent_joined(self):
        return round((self.equb.clients.count() / self.equb.capacity) * 100, 2)  # how full the equb is in percentage

    def current_spots(self):
        return self.equb.capacity - self.equb.clients.count()

    def till_next_round(self):
        if self.started and not self.ended:
            cycle = self.equb.cycle
            next_round_time = self.start_date + (self.finished_rounds + 1) * cycle
            delta = next_round_time - datetime.datetime.now()
            return MyUtils().print_time(delta)
        else:
            return 'not started'

    def update_winner_account(self):
        """
        adds the total value of equb to winners account minus the percentage
        of this amount equal to what was bid
        """
        equb = self.equb
        highest_bid = self.equb.bid.highest_bid  # this is in percentage

        # if there's no bid, winner gets full equb minus his share, because money is not collected from him
        full_amount = self.equb.value * int(1 - 1 / equb.capacity)
        award = round(full_amount * int(1 - highest_bid / 100), 2)  # award is full amount minus the bid portion

        winner = self.equb.bid.select_winner()
        if winner:
            winner.bank_account += award  # amount = equb value if highest bid = 0
            winner.save()
            logging.warning(f'{winner.user.username} full {full_amount} award {award}')

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

        # if no bid, member's account, except winner's, is deducted by received_deduction amount
        received_deduction = round(amount / capacity, 2)
        if not_received.count() > 0:
            not_received_deduction = round((amount * int(1 - highest_bid / 100)) / not_received.count(), 2)

        if capacity > self.finished_rounds:  # ensures equb is not finished
            logging.warning(f'collect, not rec: {not_received_deduction} rec: {received_deduction}')
            for member in not_received:
                member.bank_account -= not_received_deduction
                member.save()
                logging.warning(f'not rec {member.user.username} ')
            for member in self.received.all():
                member.bank_account -= received_deduction
                member.save()
                logging.warning(f' rec {member.user.username} ')

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


class Profit(models.Model):
    client = models.ForeignKey(to=Client,  on_delete=models.CASCADE, related_name='profit')
    equb = models.ForeignKey(to=Equb, on_delete=models.CASCADE, related_name='equb')
    amount = models.DecimalField(max_digits=15, decimal_places=3, default=0)

    def __str__(self):
        return str(self.client.user.username) + ' bidding' ' profit from ' + str(self.equb.name) + ' bidding'


class MyUtils(object):

    def print_time(self, time_obj):
        time = time_obj.seconds
        days = time_obj.days
        if days <= 0:
            if time // 60 < 1:  # less than a minute
                return f'{time} secs'
            if time // 3600 < 1:  # less than an hour
                mins = time // 60
                secs = time % 60
                return f'{mins} min{"s" if mins > 1 else ""} {str(secs) + " sec" if secs else ""}{"s" if secs > 1 else ""}'
            if time // 3600 // 24 < 1:  # less than a day
                hrs = time // 3600
                mins = time % 60
                return f'{hrs} hr{"s" if hrs > 1 else ""} {str(mins) + " min" if mins else ""}{"s" if mins > 1 else ""}'
        else:
            return f' {days} day' + f'{"s" if days > 1 else ""}'