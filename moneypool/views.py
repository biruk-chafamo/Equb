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


def index(request):
    return render(request, 'moneypool/index.html')


def sign_up(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(username=username, password=password)
            login(request, user)
            return HttpResponseRedirect(reverse('moneypool:create_client', args=[request.user.id]))
    else:
        form = UserCreationForm()
        return render(request, 'moneypool/sign_up.html', {'form': form})


def create_client(request, user_id):
    user = User.objects.get(id=user_id)
    if request.method == 'POST':
        client = Client.objects.create(user=user, bank_account=request.POST['bank_account'])
        return HttpResponseRedirect(reverse('moneypool:home'))
    else:
        return render(request, 'moneypool/bank_account.html', {'user_id': user_id})


def log_in(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect(reverse('moneypool:home'))
            else:
                return HttpResponseRedirect(reverse('moneypool:log_in'))
        else:
            return render(request, 'moneypool/log_in.html', {'form': form})
    else:
        form = AuthenticationForm()
        return render(request, 'moneypool/log_in.html', {'form': form})


def log_out(request):
    logout(request)
    return HttpResponseRedirect(reverse('moneypool:index'))


@login_required
def home(request):
    user = request.user
    client = user.client
    equb_count = client.equbs.all().count()
    return render(request, 'moneypool/home.html', {'username': user.username, 'equb_count': equb_count})


@login_required
def my_equbs(request):
    user = request.user
    client = Client.objects.get(user=user)
    equbs = client.equbs.all()
    received_equb_managers = client.received_equb_managers.all()
    received_equbs = [manager.equb for manager in received_equb_managers]
    return render(request, 'moneypool/my_equbs.html', {'equbs': equbs, 'received_equbs': received_equbs})


@login_required
def create_equb(request):
    if request.method == 'POST':
        form = CreateEqubForm(data=request.POST)
        if form.is_valid():
            equb = form.save()
            BalanceManager(equb=equb).save()  # creating a balance manager instance for this equ
            request.user.client.equbs.add(equb)
            return HttpResponseRedirect(reverse('moneypool:home'))
        else:
            return HttpResponseRedirect(reverse('moneypool:home'))
    else:
        form = CreateEqubForm()
        return render(request, 'moneypool/create_equb.html', {'form': form})


@login_required
def search_equb(request):
    if request.method == 'POST':
        equbs = Equb.objects.filter(name__contains=request.POST['equb_name'], balance_manager__started=False)
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


@login_required
def begin_equb(request, equb_name):
    equb = Equb.objects.get(name=equb_name)
    equb.balance_manager.started = True
    start_date = timezone.now()
    end_date = start_date + (equb.capacity * equb.cycle)
    equb.balance_manager.start_date, equb.balance_manager.end_date = start_date, end_date
    equb.balance_manager.save()

    # starting the "task" of updating client accounts
    update_client_accounts(equb_name, schedule=timezone.now(), repeat=equb.cycle.seconds, repeat_until=end_date+timezone.timedelta(seconds=2))
    return HttpResponseRedirect(reverse('moneypool:home'))