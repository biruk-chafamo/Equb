from django.contrib import admin
from .models import *
admin.site.register(Client)
admin.site.register(Equb)
admin.site.register(BalanceManager)
admin.site.register(Bid)
admin.site.register(HighestBid)
admin.site.register(Profit)
admin.site.register(FriendRequest)
admin.site.register(EqubInvite)
admin.site.register(SplitEqub)
admin.site.register(EqubRecommendation)
admin.site.register(OutBid)