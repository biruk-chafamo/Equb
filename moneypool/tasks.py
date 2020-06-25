from background_task import background
from .models import *
import logging


@background()
def update_client_accounts(equb_name):
    equb = Equb.objects.get(name=equb_name)

    logging.warning('updating winner account')
    equb.balance_manager.update_winner_account()
    logging.warning('finished updating winner account')

    logging.warning('collecting money')
    equb.balance_manager.collect_money()
    logging.warning('collected money')

    equb.reset_bid()  # Once winner is selected and money collected, bidding resets
