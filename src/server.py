from typing import Optional, TextIO, List
import subprocess
import time
import signal
import datetime
import threading
import logging

from server_config import kill_file, Config
import backup

MAX_LINES = 10000

killed = False


def was_killed() -> None:
    return killed


class CommandTimeout(Exception):
    pass


class Server:
    def __init__(self, config: Config, process: subprocess.Popen, server_log: TextIO) -> None:
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.server_log = server_log
        self.process = process
        self.killed = False
        self._cond = threading.Condition()
        self._thread = threading.Thread(target=self._pipe_reader)
        self._thread.start()

        signal.signal(signal.SIGTERM, self._on_kill)
        signal.signal(signal.SIGINT, self._on_kill)

    def _pipe_reader(self) -> None:
        self.logger.info('Started shutdown listener')
        while not self.killed:
            time.sleep(1)
            try:
                now = datetime.datetime.now().timestamp()
                with open(kill_file(), 'r') as kf:
                    line = kf.readline()
                    while line:
                        ts = float(line)
                        if ts >= now:
                            self.logger.info('Killed by stop.py')
                            self._do_kill()
                            break
                        line = kf.readline()
            except Exception:
                continue

    def _do_kill(self) -> None:
        global killed
        killed = True
        self.killed = True
        self._cond.acquire()
        self._cond.notify_all()
        self._cond.release()

    def _on_kill(self, _1, _2) -> None:
        self._do_kill()

    def sleep(self, secs: float) -> None:
        self._cond.acquire()
        self._cond.wait(secs)
        self._cond.release()

    def stop(self) -> None:
        self.killed = True
        self._thread.join()
        if self.server_alive():
            self.process.stdin.write('stop\n')
            self.process.stdin.flush()
        self.process.wait()

    def server_alive(self) -> bool:
        return self.process.poll() is None

    def should_run(self) -> bool:
        return not self.killed and self.server_alive()

    def wait_for_output(self, success_msg: str, timeout: float = 30, return_next_line: bool = False) -> str:
        self.logger.info(f'Waiting for msg: {success_msg}')
        lines = 1
        output = ''
        wait_start: Optional[int] = None
        found = False
        while return_next_line or success_msg not in output:
            if not self.server_alive() or self.killed:
                raise Exception('Killed or died while waiting')
            output = self.server_log.readline()
            if not output:
                if not wait_start:
                    wait_start = datetime.datetime.now().timestamp()
                else:
                    if datetime.datetime.now().timestamp() - wait_start > timeout:
                        raise CommandTimeout(
                            f'Timed out while waiting for output: {success_msg}'
                        )
                time.sleep(1)
            else:
                if found:
                    return output
                if success_msg in output:
                    found = True
                wait_start = None
                lines += 1
                if lines >= MAX_LINES:
                    if self.server_alive():
                        self.process.kill()
                    raise Exception(
                        f'Exceeded {MAX_LINES} logs before finding desired output: "{success_msg}"')
        return output

    def send_command(self, command: str, success_msg: str, return_next_line: bool = False) -> str:
        self.logger.info(f'Running command: {command}')
        self.process.stdin.write(f'{command}\n')
        self.process.stdin.flush()
        return self.wait_for_output(success_msg, return_next_line=return_next_line)

    def save_game(self) -> None:
        self.send_command('save-off', 'Turned off world auto-saving')
        self.send_command('save-all', 'Saved the world')
        backup.take_backup(self.config['save_path'], self.config['backup_path'])
        self.send_command('save-on', 'Turned on world auto-saving')

    def get_players(self) -> List[str]:
        MARKER = 'DedicatedServer]:'

        output = self.send_command('list', ' players online:', True)
        si = output.find(MARKER)
        if si < 0:
            self.logger.error(f'Failed to find player list in output: {output}')
            return []

        line = output[si+len(MARKER):]
        players = [s.strip() for s in line.split(' ')]
        return [p for p in players if p]
