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
            return HttpResponseRedirect(reverse('moneypool:home'))
        else:
            return HttpResponseRedirect(reverse('moneypool:log_in'))
    else:
        return render(request, 'moneypool/new_log_in.html')


def log_out(request):
    logout(request)
    return HttpResponseRedirect(reverse('moneypool:index'))


@login_required
def home(request):
    user = request.user
    client = user.client
    equb_count = client.equbs.all().count()
    return render(request, 'moneypool/new_home.html', {'username': user.username, 'equb_count': equb_count})


# @login_required
# def home(request):
#     user = request.user
#     client = user.client
#     equbs = client.equbs.all()
#     return render(request, 'moneypool/trial.html', {'username': user.username, 'equbs': equbs})


@login_required
def my_equbs(request):
    client = Client.objects.get(user=request.user)
    if request.method == 'POST':
        equb_name = request.POST['equb_name']
        return HttpResponseRedirect(reverse('moneypool:add_bid', args=[equb_name]))
    else:
        equbs = client.equbs.all()
        pending_equbs = []
        inactive_equbs = []
        active_equbs = []
        received_equbs = []
        unreceived_equbs = []
        for equb in equbs:
            # use the database instead of appending to list (to improve)
            if not equb.balance_manager.started:
                pending_equbs.append(equb)
            elif equb.balance_manager.started and not equb.balance_manager.ended:
                if client in equb.balance_manager.received.all():
                    received_equbs.append(equb)
                else:
                    unreceived_equbs.append(equb)
                active_equbs.append(equb)
            elif equb.balance_manager.started and equb.balance_manager.ended:
                inactive_equbs.append(equb)

        # received_equb_managers = client.received_equb_managers.all()
        # received_equbs = [manager.equb for manager in received_equb_managers]
        context = {
            'client': client,
            'pending_equbs': pending_equbs,
            'inactive_equbs': inactive_equbs,
            'received_equbs': received_equbs,
            'unreceived_equbs': unreceived_equbs,
            'active_equbs': active_equbs
        }
        return render(request, 'moneypool/new_my_equbs.html', context)


@login_required
def add_bid(request):
    client = Client.objects.get(user=request.user)
    equb = Equb.objects.get(name=request.POST['equb_name'])
    if request.method == 'POST':
        bid_amount = float(request.POST['bid_amount'])
        if not equb.bid.started:
            equb.bid.started = True
        equb.bid.all_bids[str(request.user.username)] = bid_amount  # registering the bid with username
        highest_bid = equb.bid.highest_bid
        if highest_bid < bid_amount:
            equb.bid.highest_bid = bid_amount
            equb.bid.highest_bidder = client
        equb.bid.save()
        return HttpResponseRedirect(reverse('moneypool:my_equbs'))
    else:
        return render(request, 'moneypool/bid.html', {'equb': equb, 'bid': equb.bid})


# def add_bid(request):
#
#     if request.method == 'POST':
#         client = Client.objects.get(user=request.user)
#         equb = Equb.objects.get(name=request.POST['equb_name'])
#         bid_amount = float(request.POST['bid_amount'])
#         if not equb.bid.started:
#             equb.bid.started = True
#         equb.bid.all_bids[str(request.user.username)] = bid_amount  # registering the bid with username
#         highest_bid = equb.bid.highest_bid
#         if highest_bid < bid_amount:
#             equb.bid.highest_bid = bid_amount
#             equb.bid.highest_bidder = client
#         equb.bid.save()
#         return HttpResponseRedirect(reverse('moneypool:my_equbs'))


@login_required
def create_equb(request):
    if request.method == 'POST':
        equb = Equb(name = request.POST['name'], cycle = request.POST['cycle'], value = request.POST['value'], capacity = request.POST['capacity'])
        equb.save()
        BalanceManager(equb=equb).save()  # creating a balance manager instance for this equb
        Bid(equb=equb).save()  # creating a bid instance for this equb
        Profit(equb=equb, client=request.user.client)
        request.user.client.equbs.add(equb)
        return HttpResponseRedirect(reverse('moneypool:home'))
    else:
        form = CreateEqubForm()
        return render(request, 'moneypool/new_create_equb.html')


@login_required
def search_equb(request):
    if request.method == 'GET':
        equbs = Equb.objects.filter(name__contains=request.GET['equb_name'], balance_manager__started=False)
        return render(request, 'moneypool/search_results.html', {'equbs': equbs})
    else:
        return render(request, 'moneypool/search_equb.html')


@login_required
def join_equb(request, equb_name):
    client = Client.objects.get(user=request.user)
    equb = Equb.objects.get(name=equb_name)
    client.equbs.add(equb)
    if equb.clients.all().count() >= equb.capacity:
        return HttpResponseRedirect(reverse('moneypool:begin_equb', args=[equb_name]))
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

    # starting the "task" of updating client accounts
    update_client_accounts(equb_name, schedule=equb.cycle.seconds, repeat=equb.cycle.seconds, repeat_until=end_date+timezone.timedelta(seconds=2))
    return HttpResponseRedirect(reverse('moneypool:home'))