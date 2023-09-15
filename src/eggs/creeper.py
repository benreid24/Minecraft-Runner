import datetime
import random

from server import Server
from eggs.egg import Egg
from server_config import Config


class CreeperEgg(Egg):
    def __init__(self, config: Config) -> None:
        super().__init__('CreeperSound', False)
        self._last_time = datetime.datetime.now().timestamp()
        self._interval = 0 # config['creeper_interval']

    def _do_update(self, server: Server) -> None:
        if datetime.datetime.now().timestamp() - self._last_time >= self._interval:
            if random.randrange(0, 100) <= 20:
                self._last_time = datetime.datetime.now().timestamp()
                server.send_command('execute @a ~ ~ ~-3 /playsound entity.creeper.primed hostile @s ~ ~ ~-3 1 0.5', '')
