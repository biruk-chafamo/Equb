
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from django.template.loader import render_to_string
from .models import *
import logging


class BidConsumer(WebsocketConsumer):

    def connect(self):
        client = Client.objects.get(user=self.scope['user'])
        self.equbs = client.equbs.filter(balance_manager__started=True)

        for equb in self.equbs:
            async_to_sync(self.channel_layer.group_add)(
                str(equb.id),
                self.channel_name
            )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        for equb in self.equbs:
            async_to_sync(self.channel_layer.group_discard)(
                str(equb.id),
                self.channel_name
            )

    # Receive bid_amount from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        client = Client.objects.get(user=self.scope['user'])
        bid_amount = float(text_data_json['bid_amount'])
        equb_id = int(text_data_json['equb_id'])
        equb = Equb.objects.get(pk=equb_id)
        bid = Bid.new_bid(client, equb, bid_amount)

        if bid.is_highest_bid():
            bid.make_highest_bid()
            async_to_sync(self.channel_layer.group_send)(
                str(equb_id),
                {
                    'type': 'send_bid_amount',
                    'equb_id': equb_id,
                    'bid_amount': bid_amount
                }
            )

    # Receive bid_amount from room group
    def send_bid_amount(self, event):
        bid_amount = event['bid_amount']
        equb_id = event['equb_id']

        # Send bid_amount to WebSocket
        self.send(text_data=json.dumps({
            'bid_amount': bid_amount,
            'equb_id': equb_id
        }))


class LiveEqubConsumer(WebsocketConsumer):

    def connect(self):
        client = Client.objects.get(user=self.scope['user'])
        live_equb_id = self.scope['url_route']['kwargs']['equb_id']
        self.equb = client.equbs.get(pk=live_equb_id)

        async_to_sync(self.channel_layer.group_add)(
            str(live_equb_id),
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            str(self.equb.id),
            self.channel_name
        )

    # Receive bid_amount from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        client = Client.objects.get(user=self.scope['user'])

        if text_data_json['bid_amount']:
            bid_amount = float(text_data_json['bid_amount'])
            bid = Bid.new_bid(client, self.equb, bid_amount)
            if bid.is_highest_bid():
                bid.make_highest_bid()

        graph_data = []
        bid_length = len(self.equb.bids.all())
        for idx, bid in enumerate(self.equb.bids.all()):
            graph_data.append([bid_length - idx, int(bid.amount)])

        async_to_sync(self.channel_layer.group_send)(
            str(self.equb.id),
            {
                'type': 'send_equb_data',
                'graph_data': graph_data,
            }
        )

    # Receive bid_amount from room group
    def send_equb_data(self, event):
        graph_data = event['graph_data']
        highest_bid_amount = float(self.equb.get_highest_bid())

        # Send bid_amount to WebSocket
        self.send(text_data=json.dumps({
            'highest_bid_amount': highest_bid_amount,
            'graph_data': graph_data,
        }))