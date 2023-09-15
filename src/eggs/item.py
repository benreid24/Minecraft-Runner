import datetime
import logging
import random

from server import Server
from eggs.egg import Egg
from server_config import Config


class ItemEgg(Egg):
    def __init__(self, config: Config) -> None:
        super().__init__('ItemGiver', False)
        self._last_time = datetime.datetime.now().timestamp()
        self._interval = config['random_item_interval']
        self._items = config['random_items']
        self.logger = logging.getLogger(__name__)

    def _do_update(self, server: Server) -> None:
        if datetime.datetime.now().timestamp() - self._last_time >= self._interval:
            if self._items and random.randrange(0, 100) <= 70:
                players = server.get_players()
                if players:
                    self._last_time = datetime.datetime.now().timestamp()
                    item = random.choices(
                        population=self._items,
                        weights=[item['weight']
                                for item in self._items],
                        k=1
                    )[0]
                    name = item['name']
                    qty = random.randrange(
                        item['min_qty'], item['max_qty'] + 1)
                    player = random.choice(players)
                    server.send_command(
                        f'tell {player} Keep this between us baby', '')
                    server.send_command(
                        f'give {player} {name} {qty}', '')
