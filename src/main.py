from typing import Optional, TextIO
import subprocess
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import time
import signal
import datetime
import threading
import sys
import random

from server_config import pid_file, kill_file, load_config, Config
import backup

config: Config = {}

MAX_LINES = 10000


def setup_logger(log_dir, log_filename):
    # Create the log directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Define the log file handler with rotating behavior
    log_file = os.path.join(log_dir, log_filename)
    handler = TimedRotatingFileHandler(
        log_file, when="midnight", interval=1, backupCount=7
    )

    # Define the log message format with timestamps
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)

    # Add the handler to the logger
    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler(sys.stdout))

    return logger


logger: logging.Logger = None

killed = False


class Server:
    def __init__(self, process: subprocess.Popen, server_log: TextIO) -> None:
        self.server_log = server_log
        self.process = process
        self.killed = False
        self._cond = threading.Condition()
        self._thread = threading.Thread(target=self._pipe_reader)
        self._thread.start()

        signal.signal(signal.SIGTERM, self._on_kill)
        signal.signal(signal.SIGINT, self._on_kill)

    def _pipe_reader(self) -> None:
        logger.info('Started shutdown listener')
        while not self.killed:
            time.sleep(1)
            try:
                now = datetime.datetime.now().timestamp()
                with open(kill_file(), 'r') as kf:
                    line = kf.readline()
                    while line:
                        ts = float(line)
                        if ts >= now:
                            logger.info('Killed by stop.py')
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

    def wait_for_output(self, success_msg: str, timeout: float = 30) -> None:
        logger.info(f'Waiting for msg: {success_msg}')
        lines = 1
        output = ''
        wait_start: Optional[int] = None
        while success_msg not in output:
            if not self.server_alive() or self.killed:
                raise Exception('Killed or died while waiting')
            output = self.server_log.readline()
            if not output:
                if not wait_start:
                    wait_start = datetime.datetime.now().timestamp()
                else:
                    if datetime.datetime.now().timestamp() - wait_start > timeout:
                        if self.server_alive():
                            self.process.kill()
                        raise Exception(
                            f'Timed out while waiting for output: {success_msg}')
                time.sleep(1)
            else:
                wait_start = None
                lines += 1
                if lines >= MAX_LINES:
                    if self.server_alive():
                        self.process.kill()
                    raise Exception(
                        f'Exceeded {MAX_LINES} logs before finding desired output: "{success_msg}"')

    def send_command(self, command: str, success_msg: str):
        self.process.stdin.write(f'{command}\n')
        self.process.stdin.flush()
        self.wait_for_output(success_msg)

    def save_game(self) -> None:
        self.send_command('save-off', 'Turned off world auto-saving')
        self.send_command('save-all', 'Saved the world')
        backup.take_backup(config['save_path'], config['backup_path'])
        self.send_command('save-on', 'Turned on world auto-saving')


def start_game() -> subprocess.Popen:
    cmd = ' '.join(config['start_command'])
    logger.info(f'Starting server with: "{cmd}"')

    process = subprocess.Popen(
        config['start_command'],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    time.sleep(1)
    if process.poll() is not None:
        raise Exception('Failed to launch server')

    return process


def write_pid():
    with open(pid_file(), 'w') as out:
        out.write(str(os.getpid()))


def lifetime() -> bool:
    logger.info('Starting Minecraft')
    process = start_game()
    time.sleep(3)
    with open('logs/latest.log', 'r') as logs:
        minecraft = Server(process, logs)
        minecraft.wait_for_output('DedicatedServer]: Done', 180)
        logger.info('Minecraft started')

        try:
            last_save_time = datetime.datetime.now().timestamp()
            last_phrase_time = datetime.datetime.now().timestamp()

            while minecraft.should_run():
                minecraft.sleep(600)  # 10 minutes
                if not minecraft.should_run():
                    logger.info('Got stop command')
                    break

                if datetime.datetime.now().timestamp() - last_save_time >= config['backup_interval']:
                    last_save_time = datetime.datetime.now().timestamp()
                    logger.info('Saving game')
                    minecraft.save_game()
                    logger.info('Save complete')

                if datetime.datetime.now().timestamp() - last_phrase_time >= config['phrase_interval']:
                    if random.randrange(0, 100) < 30:
                        last_phrase_time = datetime.datetime.now().timestamp()
                        phrase = random.choice(config['phrases'])
                        minecraft.send_command(f'say {phrase}', '')

        except Exception:
            logger.exception('Got exception while running')
        finally:
            # Exit gracefully on kill/crash
            logger.info('Stopping')
            minecraft.stop()
            logger.info('Server stopped')

            return not minecraft.killed


def main():
    global config
    global logger

    config = load_config()
    os.chdir(config['server_path'])
    logger = setup_logger(os.path.join(config['server_path'], 'manager_logs'), 'manager.log')

    logger.info('Starting manager')
    write_pid()
    backup.init(config['backup_path'])
    logger.info('Manager initialized')

    while True:
        try:
            if killed or not lifetime():
                break
        except Exception:
            logger.exception('Manager failed. Retrying')

    logger.info('Manager exited normally')


if __name__ == '__main__':
    main()
