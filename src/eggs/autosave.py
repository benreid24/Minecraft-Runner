import datetime
import logging

from server import Server
from eggs.egg import Egg
from server_config import Config


class AutosaveEgg(Egg):
    def __init__(self, config: Config) -> None:
        super().__init__('Autosave', False)
        self._last_time = datetime.datetime.now().timestamp()
        self._interval = config['backup_interval']
        self.logger = logging.getLogger(__name__)

    def _do_update(self, server: Server) -> None:
        if datetime.datetime.now().timestamp() - self._last_time >= self._interval:
            self._last_time = datetime.datetime.now().timestamp()
            self.logger.info('Saving game')
            server.save_game()
            self.logger.info('Save complete')
