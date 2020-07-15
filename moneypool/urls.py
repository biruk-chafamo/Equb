from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = "moneypool"

urlpatterns = [
    path('', views.index, name='index'),
    path('log_in', views.log_in, name='log_in'),
    path('log_out', views.log_out, name='log_out'),
    path('sign_up', views.sign_up, name='sign_up'),
    path('create_client', views.create_client, name='create_client'),
    path('home', views.home, name='home'),
    path('search_equb', views.search_equb, name='search_equb'),
    path('my_equbs', views.my_equbs, name='my_equbs'),
    # path('<equb_name>/add_bid', views.add_bid, name='add_bid'),
    path('add_bid', views.add_bid, name='add_bid'),
    path('<equb_name>/join_equb', views.join_equb, name='join_equb'),
    path('accept_invite', views.accept_invite, name='accept_invite'),
    path('create_equb', views.create_equb, name='create_equb'),
    path('<equb_name>/begin_equb', views.begin_equb, name='begin_equb'),
    path('invite', views.invite, name='invite'),
    path('pin_equb', views.pin_equb, name='pin_equb'),
]