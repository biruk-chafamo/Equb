from django.test import TestCase
from .models import *
import datetime


class GeneralTest(TestCase):
    def setUp(self):
        if Equb.objects.filter(name='test equb'):
            Equb.objects.get(name='test equb').delete()
        sosi = Client.objects.get(user__username='sosina16')
        equb = Equb(name='test equb', creator=sosi, value=600, capacity=3, cycle=datetime.timedelta(seconds=90))
        equb.save()
        equb.notify_friends()
        BalanceManager(equb=equb).save()  # creating a balance manager instance for this equb
        # Bid(equb=equb).save()  # creating a bid instance for this equb
        HighestBid(equb=equb, round=1).save()
        clients = ['sosina16', 'zeleke']
        for cl in clients:
            client = Client.objects.get(user__username=cl)
            client.equbs.add(equb)
            # Profit(equb=equb, client=client).save()
