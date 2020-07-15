from background_task import background
from .models import *
import datetime
import logging


@background()
def update_client_accounts(equb_name):
    equb = Equb.objects.get(name=equb_name)
    all_members = equb.clients.all()
    received = equb.balance_manager.received.all()
    not_received = all_members.difference(received)
    logging.warning(f'{not_received.count()} not rec')
    logging.warning('updating winner account')
    equb.balance_manager.update_winner_account()
    logging.warning('finished updating winner account')

    # at this point, the winner is added into the received group so money wont be collected from this individual

    logging.warning('collecting money')
    equb.balance_manager.collect_money()
    logging.warning('collected money')

    # logging.warning('resetting bid')
    # equb.bid.reset_bid()  # Once winner is selected and money collected, bidding resets
    # logging.warning('bid reset')
    if equb.balance_manager.finished_rounds < equb.capacity:
        update_client_accounts(equb_name, schedule=datetime.datetime.now()+equb.cycle)