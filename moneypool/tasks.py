from background_task import background
from .models import *
import logging


@background()
def update_client_accounts(equb_name):
    equb = Equb.objects.get(name=equb_name)
    logging.warning('collecting money')
    equb.balance_manager.collect_money()
    logging.warning('collected money')
    logging.warning('updating winner account')
    equb.balance_manager.update_winner_account()
    logging.warning('finished updating winner account')