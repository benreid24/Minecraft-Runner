import datetime
import logging
import random
import time

from server import Server
from eggs.egg import Egg
from server_config import Config


class EffectEgg(Egg):
    def __init__(self, config: Config) -> None:
        super().__init__('EffectGiver', False)
        self._last_time = datetime.datetime.now().timestamp()
        self._interval = config['effect_interval']
        self._effects = config['effect_options']
        self.logger = logging.getLogger(__name__)

    def _do_update(self, server: Server) -> None:
        if datetime.datetime.now().timestamp() - self._last_time >= self._interval:
            if self._effects and random.randrange(0, 100) <= 40:
                players = server.get_players()
                if players:
                    self._last_time = datetime.datetime.now().timestamp()
                    item = random.choices(
                        population=self._effects,
                        weights=[item['weight']
                                for item in self._effects],
                        k=1
                    )[0]
                    name = item['name']
                    duration = item['duration']
                    level = item['level']
                    player = random.choice(players)
                    if 'message' in item:
                        msg = item['message'].format(player=player)
                        server.send_command(f'say {msg}', '')
                    server.send_command(f'effect {player} {name} {duration} {level}', '')
