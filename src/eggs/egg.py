import logging

from server import Server


class Egg:
    def __init__(self, name: str, is_critical: bool) -> None:
        self.name = name
        self.is_critical = is_critical
        self.logger = logging.getLogger(__name__)

    def update(self, server: Server) -> None:
        try:
            self._do_update(server)
        except Exception:
            self.logger.exception(f'Egg "{self.name}" failed')
            if not server.server_alive() or self.is_critical:
                raise
            else:
                server.send_command('save-all', '')
                server.send_command('save-on', '')

    def _do_update(self, server: Server) -> None:
        raise NotImplementedError('_do_update must be implemented')
