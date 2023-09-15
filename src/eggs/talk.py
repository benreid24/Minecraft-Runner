import datetime
import logging
import random

from server import Server
from eggs.egg import Egg
from server_config import Config


class TalkEgg(Egg):
    def __init__(self, config: Config) -> None:
        super().__init__('Talker', False)
        self._last_time = datetime.datetime.now().timestamp()
        self._interval = config['random_item_interval']
        self._phrases = config['phrases']
        self.logger = logging.getLogger(__name__)

    def _do_update(self, server: Server) -> None:
        if datetime.datetime.now().timestamp() - self._last_time >= self._interval:
            if self._phrases and random.randrange(0, 100) < 40:
                self._last_time = datetime.datetime.now().timestamp()
                phrase = random.choice(self._phrases)
                server.send_command(f'say {phrase}', '')
