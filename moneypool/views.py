from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.urls import reverse
from .forms import *
from .tasks import *
from django.utils import timezone
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def index(request):
    # return render(request, 'moneypool/index.html')
    return HttpResponseRedirect(reverse('moneypool:log_in'))


def sign_up(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)
            return HttpResponseRedirect(reverse('moneypool:create_client'))
    form = UserCreationForm()
    return render(request, 'moneypool/sign_up.html', {'form': form})


def create_client(request):
    if request.method == 'POST':
        client = Client(user=request.user, bank_account=float(request.POST['bank_account']))
        client.save()
        return HttpResponseRedirect(reverse('moneypool:home'))
    else:
        return render(request, 'moneypool/bank_account.html')


def log_in(request):
    if request.method == 'POST':
        user = authenticate(username=request.POST['username'], password=request.POST['password'])
        if user:
            login(request, user)
            return HttpResponseRedirect(reverse('moneypool:home'))  # change this to home and add notifications
        else:
            return HttpResponseRedirect(reverse('moneypool:log_in'))
    else:
        return render(request, 'moneypool/new_log_in.html')


def log_out(request):
    logout(request)
    return HttpResponseRedirect(reverse('moneypool:index'))


@login_required
def home(request):
    client = request.user.client

    recs = client.received_equbrecommendations.all()
    equb_recs = [rec.equb for rec in recs if rec.relevant is True]

    invitations = client.received_equbinvites.filter(relevant=True)
    # equb_invites = [invitation.equb for invitation in invitations if invitation.relevant is True]

    friend_requests = client.received_friendrequests.all()

    active_equbs = client.equbs.filter(balance_manager__started=True, balance_manager__ended=False)
    approaching_equbs = [equb for equb in active_equbs if equb.balance_manager.next_round_approaching(20)]

    received_outbids = client.received_outbids.all()
    sent_outbids = client.sent_outbids.all()
    outbids = received_outbids | sent_outbids
    outbids.order_by('-date')
    data = []
    import math
    if request.session.get('pinnedEqubID', None):
        pinned_equb = Equb.objects.get(pk=request.session['pinnedEqubID'])
        c = len(pinned_equb.bids.all())
        for idx, bid in enumerate(pinned_equb.bids.all()):
            data.append([c - idx, int(bid.amount)])
    else:
        if active_equbs:
            c = len(active_equbs[0].bids.all())
            for idx, bid in enumerate(active_equbs[0].bids.all()):
                data.append([c - idx, int(bid.amount)])

    context = {
        "pending": client.equbs.filter(balance_manager__started=False),
        "active_equbs": active_equbs,
        "current_tab": "home_tab",
        'client': client,
        'username': client.user.username,
        'invitations': invitations,
        'outbids': outbids,
        'sent_outbids': sent_outbids,
        'received_outbids': received_outbids,
        'friend_requests': friend_requests,
        'approaching_equbs': approaching_equbs,
        'equb_recs': equb_recs,
        'data': data[::-1],
     }
    return render(request, 'moneypool/new_home.html', context)


@login_required
def my_equbs(request):
    client = request.user.client
    if request.method == 'POST':
        equb_name = request.POST['equb_name']
        return HttpResponseRedirect(reverse('moneypool:add_bid', args=[equb_name]))
    else:
        pending_equbs = client.equbs.filter(balance_manager__started=False, balance_manager__ended=False)

        inactive_equbs = client.equbs.filter(balance_manager__started=True, balance_manager__ended=True)

        active_equbs = client.equbs.filter(balance_manager__started=True, balance_manager__ended=False)
        received_equbs = [equb for equb in active_equbs if client in equb.balance_manager.received.all()]
        unreceived_equbs = [equb for equb in active_equbs if client not in equb.balance_manager.received.all()]

        context = {
            'client': client,
            'pending_equbs': pending_equbs,
            'inactive_equbs': inactive_equbs,
            'received_equbs': received_equbs,
            'unreceived_equbs': unreceived_equbs,
            'active_equbs': active_equbs,
            "current_tab": "my_equbs_tab",
        }

        return render(request, 'moneypool/new_my_equbs.html', context)


# @login_required
# def add_bid(request):
#     client = request.user.client
#     equb = Equb.objects.get(name=request.POST['equb_name'])
#     bid = equb.bid
#     if request.method == 'POST':
#         bid_amount = float(request.POST['bid_amount'])
#         if not bid.started:
#             bid.started = True
#         bid.all_bids[str(request.user.username)] = bid_amount  # registering the bid with username
#         highest_bid = bid.highest_bid
#         if highest_bid < bid_amount:
#             if highest_bid != 0:  # meaning a bid has been made prior to the current bid
#                 OutBid(sender=client, receiver=bid.highest_bidder, equb=equb).save()
#             bid.highest_bid = bid_amount
#             bid.highest_bidder = client
#         bid.save()
#         return HttpResponseRedirect(reverse('moneypool:my_equbs'))
#     else:
#         return HttpResponseRedirect(reverse('moneypool:my_equbs'))


@login_required
def add_bid(request):
    client = request.user.client
    if request.method == 'POST':
        logging.warning(f"this is request {request.POST} {request.POST['equb_id']} {request.POST['bid_amount']}")
        equb = Equb.objects.get(pk=int(request.POST['equb_id']))
        new_amount = decimal.Decimal(request.POST['bid_amount'])
        current_round = equb.balance_manager.finished_rounds + 1
        new_bid = Bid(equb=equb, client=client, round=current_round, amount=new_amount)
        new_bid.save()
        highest_bid = HighestBid.objects.get(equb=equb, round=current_round)
        logging.warning(highest_bid.bid)
        if not highest_bid.bid:  # if there was no prior highest bid
            highest_bid.bid = new_bid
            highest_bid.save()

        elif highest_bid.bid and new_amount > highest_bid.bid.amount:  # if new bid > previous bid
            OutBid(sender=client, receiver=highest_bid.bid.client, equb=equb).save()
            highest_bid.bid = new_bid
            highest_bid.save()

        return JsonResponse({'highest_bid_amount': highest_bid.bid.amount})
    else:
        return HttpResponseRedirect(reverse('moneypool:my_equbs'))


@login_required
def create_equb(request):
    if request.method == 'POST':
        equb = Equb(name=request.POST['name'], cycle=request.POST['cycle'],
                    value=request.POST['value'], capacity=request.POST['capacity'],
                    creator=request.user.client, private=request.POST['private'] == 'True')
        equb.save()

        # these objects be;ow must always be created with each equb
        BalanceManager(equb=equb).save()  # creating a balance manager instance for this equb
        # Bid(equb=equb).save()  # creating a bid instance for this equb
        HighestBid(equb=equb, round=1).save()
        Profit(equb=equb, client=request.user.client).save()

        # notify friends of this equb by creating recommendation instances
        if not equb.private:
            equb.notify_friends()

        # adding the newly created equb to client's list of equbs
        request.user.client.equbs.add(equb)
        return HttpResponseRedirect(reverse('moneypool:my_equbs'))
    else:
        return render(request, 'moneypool/new_create_equb.html', context={"current_tab": "create_tab"})


@login_required
def search_equb(request):
    if request.method == 'GET':
        equbs = Equb.objects.filter(name__contains=request.GET['equb_name'], balance_manager__started=False)
        return render(request, 'moneypool/search_results.html', {'equbs': equbs})
    else:
        return render(request, 'moneypool/search_equb.html')


@login_required
def join_equb(request, equb_name):
    client = request.user.client
    equb = Equb.objects.get(name=equb_name)
    client.equbs.add(equb)
    Profit(equb=equb, client=client).save()
    if equb.clients.all().count() >= equb.capacity:
        return HttpResponseRedirect(reverse('moneypool:begin_equb', args=[equb_name]))
    else:
        return HttpResponseRedirect(reverse('moneypool:home'))


def accept_invite(request):
    if request.method == 'POST':
        client = request.user.client
        equb_id = request.POST.get("equb_id")
        equb = Equb.objects.get(pk=equb_id)
        client.equbs.add(equb)
        Profit(equb=equb, client=client).save()
        if equb.clients.all().count() >= equb.capacity:
            equb.balance_manager.started = True
            start_date = timezone.now()
            end_date = start_date + (equb.capacity * equb.cycle)
            equb.balance_manager.start_date, equb.balance_manager.end_date = start_date, end_date
            equb.balance_manager.save()

            for rec in equb.equbrecommendations.all():
                rec.make_irrelevant()

            # starting the "task" of updating client accounts
            # improvement: schedule all tasks at once
            update_client_accounts(equb.name, schedule=(start_date + equb.cycle))
        equb_invites = EqubInvite.objects.filter(receiver=client, equb=equb)
        for invitation in equb_invites:
            invitation.accept_request()
            invitation.make_irrelevant()
        logging.warning(f'{equb_id} accepted')
        response = {'status': 200}
        return JsonResponse(response)
    elif request.method == 'GET':
        response = {'status': 200}
        return JsonResponse(response)
    else:
        return HttpResponseRedirect(reverse('moneypool:home'))


# ..............include in balance manager model.................
@login_required
def begin_equb(request, equb_name):
    equb = Equb.objects.get(name=equb_name)
    equb.balance_manager.started = True
    start_date = timezone.now()
    end_date = start_date + (equb.capacity * equb.cycle)
    equb.balance_manager.start_date, equb.balance_manager.end_date = start_date, end_date
    equb.balance_manager.save()

    for rec in equb.equbrecommendations.all():
        rec.make_irrelevant()

    # starting the "task" of updating client accounts
    # improvement: schedule all tasks at once
    update_client_accounts(equb_name, schedule=(start_date + equb.cycle))
    return HttpResponseRedirect(reverse('moneypool:home'))


@login_required
def invite(request):
    if request.method == 'POST':
        sender = request.user.client
        equb_id = request.POST.get("equb_id")
        equb = Equb.objects.get(pk=equb_id)

        for username in request.POST.getlist('invited[]'):
            receiver = Client.objects.get(user__username=username)
            EqubInvite(sender=sender, equb=equb, receiver=receiver).save()

        logging.warning(f'{equb_id} {sender.user.username}')
        response = {'status': 200}
        return JsonResponse(response)
    elif request.method == 'GET':
        response = {'status': 200}
        return JsonResponse(response)
    else:
        return HttpResponseRedirect(reverse('moneypool:home'))


@login_required
def pin_equb(request):
    if request.method == 'POST':
        request.session['pinnedEqubID'] = request.POST.get('pinnedEqub')
        logging.warning(request.session['pinnedEqubID'])
        equb = Equb.objects.get(pk=request.session['pinnedEqubID'])

        data = []
        c = len(equb.bids.all())
        for idx, bid in enumerate(equb.bids.all()):
            data.append([c - idx, int(bid.amount)])
        logging.warning(data)
        return JsonResponse({'data': data})