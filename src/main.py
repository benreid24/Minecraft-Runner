from typing import List
import subprocess
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import time
import datetime
import sys
import random

from server_config import pid_file, load_config, Config
import backup
from server import Server, CommandTimeout, was_killed

from eggs.egg import Egg
from eggs.autosave import AutosaveEgg
from eggs.item import ItemEgg
from eggs.talk import TalkEgg

config: Config = {}


def setup_logging(log_dir, log_filename):
    # Create the log directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

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

    logging.basicConfig(
        handlers=[
            handler,
            logging.StreamHandler(sys.stdout)
        ],
        level=logging.INFO
    )


logger: logging.Logger = None

killed = False


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
        minecraft = Server(config, process, logs)
        minecraft.wait_for_output('DedicatedServer]: Done', timeout=180)
        logger.info('Minecraft started')

        all_eggs: List[Egg] = [
            AutosaveEgg(config),
            ItemEgg(config),
            TalkEgg(config)
        ]

        try:
            while minecraft.should_run():
                minecraft.sleep(5)  # 5 minutes
                if not minecraft.should_run():
                    logger.info('Got stop command')
                    break

                for egg in all_eggs:
                    egg.update(minecraft)

        except Exception:
            logger.exception('Got exception while running')
        finally:
            # Exit gracefully on kill/crash
            logger.info('Stopping')
            if minecraft.server_alive():
                try:
                    logger.info('Performing final save')
                    minecraft.send_command('save-all', '')
                except:
                    pass
            minecraft.stop()
            logger.info('Server stopped')

            return not minecraft.killed


def main():
    global config
    global logger

    config = load_config()
    os.chdir(config['server_path'])
    setup_logging(os.path.join(config['server_path'], 'manager_logs'), 'manager.log')
    logger = logging.getLogger(__name__)

    logger.info('Starting manager')
    write_pid()
    backup.init(config['backup_path'])
    logger.info('Manager initialized')

    while True:
        try:
            if was_killed() or not lifetime():
                break
        except Exception:
            logger.exception('Manager failed. Retrying')

    logger.info('Manager exited normally')


if __name__ == '__main__':
    main()
