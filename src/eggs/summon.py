import datetime
import logging
import random
import time

from server import Server
from eggs.egg import Egg
from server_config import Config


class SummonEgg(Egg):
    def __init__(self, config: Config) -> None:
        super().__init__('Summoner', False)
        self._last_time = datetime.datetime.now().timestamp()
        self._interval = config['summon_interval']
        self._creatures = config['summon_options']
        self.logger = logging.getLogger(__name__)

    def _do_update(self, server: Server) -> None:
        if datetime.datetime.now().timestamp() - self._last_time >= self._interval:
            if self._creatures and random.randrange(0, 100) <= 40:
                self._last_time = datetime.datetime.now().timestamp()
                
                players = server.get_players()
                if players:
                    item = random.choices(
                        population=self._creatures,
                        weights=[item['weight']
                                for item in self._creatures],
                        k=1
                    )[0]
                    name = item['name']
                    qty = random.randrange(item['min_qty'], item['max_qty'] + 1)
                    player = random.choice(players)
                    server.send_command(f'say {player} better watch out...', '')
                    time.sleep(5)
                    for i in range(qty):
                        server.send_command(f'execute {player} ~ ~ ~ /summon {name}', '')
