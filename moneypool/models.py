from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.utils import timezone
from . import MyUtils
import datetime
import random
import logging
import decimal


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
    creator = models.ForeignKey(to=Client, on_delete=models.SET_NULL, null=True, related_name='created_equbs')
    creation_date = models.DateTimeField(default=timezone.now)
    private = models.BooleanField(default=False)

    def __str__(self):
        return str(self.name)

    def get_cycle(self):
        return MyUtils.print_time(self.cycle)

    def get_highest_bid(self):
        current_round = self.balance_manager.finished_rounds + 1
        highest_bid = self.highest_bids.get(round=current_round)
        if highest_bid.bid:
            return highest_bid.bid.amount
        else:
            return 0

    def notify_friends(self):  # should only be called if self.private == True
        rec = EqubRecommendation(sender=self.creator, equb=self)
        rec.save()
        for friend in self.creator.friends.all():
            rec.receivers.add(friend)


class BalanceManager(models.Model):
    equb = models.OneToOneField(to=Equb, on_delete=models.CASCADE, related_name='balance_manager')
    received = models.ManyToManyField(Client, blank=True, related_name='received_equb_managers')
    last_managed = models.DateTimeField(null=True, blank=True)
    finished_rounds = models.IntegerField(blank=True, default=0)
    started = models.BooleanField(default=False)  # set to true when equb fills up to capacity
    ended = models.BooleanField(default=False)  # when all rounds are completed
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.equb.name) + ' balance manager'

    def check_received(self, client):
        received = self.received.all()
        if client in received:
            return True
        else:
            return False

    def percent_completed(self):
        return round((self.finished_rounds / self.equb.capacity) * 100, 2)  # percent of people who have received equb

    def percent_joined(self):
        return round((self.equb.clients.count() / self.equb.capacity) * 100, 2)  # how full the equb is in percentage

    def current_spots(self):
        return self.equb.capacity - self.equb.clients.count()

    def time_delta(self):  # time till next round
        cycle = self.equb.cycle
        next_round_time = self.start_date + (self.finished_rounds + 1) * cycle
        delta = next_round_time - datetime.datetime.now()
        return delta

    # if delta is less than {limit}% of equb cycle, then next round is approaching
    def next_round_approaching(self, limit):
        delta = self.time_delta()
        if (delta / self.equb.cycle) * 100 < limit:
            return True

    def print_delta(self):
        if self.started and not self.ended:
            delta = self.time_delta()
            if delta.days < 0 or delta.seconds < 0:
                return 'In Progress'
            else:
                return MyUtils.print_time(delta)
        else:
            return 'not started'

    def select_winner(self):
        """
        Selects highest bidder as winner.
        If there is no bid, winner is randomly selected from
        those who haven't received their equbs yet
        """
        current_round = self.finished_rounds + 1
        highest_bid = self.equb.highest_bids.get(round=current_round)
        all_members = self.equb.clients.all()
        received = self.received.all()
        not_received = all_members.difference(received)
        if not_received:
            if highest_bid.bid:
                winner = highest_bid.bid.client
            else:
                winner = random.choice(not_received)
            self.received.add(winner)
            return winner

    def update_winner_account(self):
        """
        adds the total value of equb to winners account minus the percentage
        of this amount equal to what was bid
        """
        equb = self.equb
        current_round = self.finished_rounds + 1
        highest_bid = equb.highest_bids.get(round=current_round) # this is in percentage
        if highest_bid.bid:
            bid_amount = highest_bid.bid.amount
        else:
            bid_amount = 0
        deductible_portion = equb.value * decimal.Decimal(1 - 1 / equb.capacity)
        # if there is no bid, deductible_portion = deducted_award
        deducted_award = deductible_portion * decimal.Decimal(1 - bid_amount / 100)
        non_deductible_award = equb.value / equb.capacity
        award = non_deductible_award + deducted_award

        winner = self.select_winner()
        if winner:
            winner.bank_account += award  # amount = equb value if highest bid = 0
            winner.save()
            logging.warning(f'{winner.user.username} award {award}')

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
        current_round = self.finished_rounds + 1
        highest_bid = equb.highest_bids.get(round=current_round)   # this is in percentage, eg 4%

        if highest_bid.bid:
            bid_amount = highest_bid.bid.amount
        else:
            bid_amount = 0

        # winner's contribution = 0 if there is no bid
        winners_contribution = equb.value * decimal.Decimal((1 - 1 / capacity)) * decimal.Decimal((bid_amount / 100))

        received_deduction = equb.value / capacity
        if not_received:
            not_received_deduction = (equb.value / capacity) - (winners_contribution / not_received.count())
        else:
            not_received_deduction = 0

        if capacity > self.finished_rounds:  # ensures equb is not finished
            logging.warning(f'collect, not rec: {not_received_deduction} rec: {received_deduction}')
            for member in not_received:
                member.bank_account -= not_received_deduction
                member.save()
                logging.warning(f'not rec {member.user.username} ')
            # the winner is in this list because select_winner adds winner to received list
            for member in self.received.all():
                member.bank_account -= received_deduction
                member.save()
                logging.warning(f' rec {member.user.username} ')

            # marks the "self.eneded" field to True when all members have received their equb
            if capacity == self.finished_rounds + 1:
                self.ended = True  # terminating manager

            self.finished_rounds += 1  # updating finished rounds

            for outbid in OutBid.objects.filter(equb=self.equb):  # outbids from the previous round are irrelevant
                outbid.make_irrelevant()

            self.last_managed = timezone.now()  # updating last managed time
            self.save()
            HighestBid(equb=equb, round=self.finished_rounds + 1).save()


class Bid(models.Model):
    equb = models.ForeignKey(to=Equb, on_delete=models.CASCADE, related_name='bids')
    client = models.ForeignKey(to=Client, on_delete=models.CASCADE, related_name='sent_bids', null=True)
    amount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    round = models.PositiveIntegerField()
    date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-amount']

    def get_round(self):
        return str(self.round)

    def __str__(self):
        return str(self.client.user.username) + ' to ' + str(self.equb.name) + ' round ' + str(self.round)


class HighestBid(models.Model):
    equb = models.ForeignKey(to=Equb, on_delete=models.CASCADE, related_name='highest_bids')
    bid = models.OneToOneField(to=Bid, on_delete=models.SET_NULL, null=True, blank=True)
    round = models.PositiveIntegerField()




# class Bid(models.Model):
#     equb = models.OneToOneField(to=Equb, on_delete=models.CASCADE, related_name='bid')
#     started = models.BooleanField(default=False, )
#     highest_bid = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True)
#     highest_bidder = models.ForeignKey(to=Client, on_delete=models.CASCADE, blank=True, null=True)
#     all_bids = JSONField(default=dict, blank=True, null=True)
#
#     def __str__(self):
#         return str(self.equb.name) + ' bidding'
#
#     def select_winner(self):
#         """
#         Selects highest bidder as winner.
#         If there is no bid, winner is randomly selected from
#         those who haven't received their equbs yet
#         """
#
#         equb = self.equb
#         all_members = equb.clients.all()
#         received = equb.balance_manager.received.all()
#         not_received = all_members.difference(received)
#         if not_received:
#             if equb.bid.started is True and equb.bid.highest_bidder not in received:
#                 winner = equb.bid.highest_bidder
#             else:
#                 winner = random.choice(not_received)
#             equb.balance_manager.received.add(winner)
#             return winner
#
#     def reset_bid(self):
#         """
#         Must be called after each cycle of equb to reset bid
#         """
#         self.started = False
#         self.highest_bid = 0
#         self.highest_bidder = None
#         self.all_bids = {}
#         self.save()
#
#         # making all outbid notifications irrelevant because new round has started
#         for outbid in OutBid.objects.filter(equb=self.equb):
#             outbid.make_irrelevant()


class Profit(models.Model):
    client = models.ForeignKey(to=Client,  on_delete=models.CASCADE, related_name='profit')
    equb = models.ForeignKey(to=Equb, on_delete=models.SET_NULL, null=True, related_name='equb')
    amount = models.DecimalField(max_digits=15, decimal_places=3, default=0)

    def __str__(self):
        return str(self.client.user.username) + ' bidding' ' profit from ' + str(self.equb.name) + ' bidding'


# ......................The section below consists of Informational models such as requests ......................


class Request(models.Model):
    equb = models.ForeignKey(to=Equb, on_delete=models.CASCADE, related_name='%(class)ss')
    sender = models.ForeignKey(to=Client, on_delete=models.CASCADE, blank=True, related_name='sent_%(class)ss')
    receiver = models.ForeignKey(to=Client, blank=True, on_delete=models.CASCADE, related_name='received_%(class)ss')
    accepted = models.BooleanField(default=False)
    relevant = models.BooleanField(default=True)
    date = models.DateTimeField(default=timezone.now)

    # def __str__(self):
    #     return '%(class)s' + f' from {self.sender.user.username} to {self.receiver.user.username} '

    def make_irrelevant(self):
        self.relevant = False
        self.save()

    def accept_request(self):
        self.accepted = True
        self.save()

    class Meta:
        abstract = True
        ordering = ['-date']


class FriendRequest(Request):
    equb = None

    def request_message(self):
        message = f"{self.sender.user.username} has sent you a friend request"
        return message


class EqubInvite(Request):

    def request_message(self):
        message = f"{self.sender} invites you to {self.equb.name}"
        return message


class EqubRecommendation(Request):  # instantiated only once per equb when an equb is first created
    receiver = None
    receivers = models.ManyToManyField(to=Client, related_name='received_equbrecommendations')

    def notify_creator(self, acceptor_client):
        message = f"{acceptor_client.user.username} has joined {self.equb.name}"
        return message


class SplitEqub(Request):
    receiver = None
    receivers = models.ManyToManyField(to=Client, related_name='received_splitequbs')

    def request_message(self):
        message = f"{self.sender} wants to split {self.equb.name} with you"
        return message


class OutBid(Request):  # this is a Request subclass because sender outbids, and receiver gets outbid
    """
    Outbids are created in the add_bid view when one equb member outbids another.
    All outbids are made irrelevant by the balance manager when a new equb round starts.
    """
    accepted = None


    def sender_message(self):
        message = f"you outbid {self.receiver.user.username} in {self.equb.name}"
        return message

    def receiver_message(self):
        message = f"{self.sender.user.username} outbid you in {self.equb.name}"
        return message
#
#
# class SplitEqub(models.Model):
#     pass
#
#
# class OutBid(models.Model):
#     winner = models.ForeignKey(to=Client, on_delete=models.CASCADE, related_name='winner')
#     loser = models.ForeignKey(to=Client, on_delete=models.CASCADE, related_name='loser')
#     date = models.DateTimeField()
#
#
# class EqubCreation(models.Model):
#     creator = models.OneToOneField(to=Client, on_delete=models.CASCADE)
#     equb = models.OneToOneField(to=Equb, on_delete=models.CASCADE)
#     date = models.DateTimeField()
#
#
# class RoundStarted(models.Model):
#     pass
#
#
# class Information(models.Model):
#     affected = models.ManyToManyField(to=Client, related_name='information')
#     catagory = models.TextField(choices=[('bid', 'bid'), ('equb_invitation', 'equb_invitation'),
#                                          ('equb_creation', 'equb_creation'), ('friendship', 'friendship'),
#                                          ('friendship_status', 'friendship_status'), ('equb_round', 'equb_round'),
#                                          ('equb_invitation_status', 'equb_invitation_status'),
#                                          ])
#     action = models.TextField(choices=[('deny', 'deny'), ('accept', 'accept')])





