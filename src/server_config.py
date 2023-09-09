from typing import TypedDict, List, Optional
import os
import json
import logging


class Config(TypedDict):
    server_path: str
    start_command: List[str]
    save_path: str  # Computed
    
    backup_path: str
    backup_interval: int

    phrase_interval: int
    phrases: List[str]


DEFAULT_CONFIG: Config = {
    'server_path': '/galacticraft',
    'start_command': ['java', '-Xmx8G', '-Dfml.queryResult=confirm', '-jar', 'forge-server.jar', 'nogui'],

    'backup_path': '/home/ben/Dropbox/Galacticraft/Backups',
    'backup_interval': 20 * 60,

    'phrase_interval': 40 * 60,
    'phrases': [
        'A horse is a horse of course of course',
        'PP Lemon Lover 69',
        'KABA',
        'Make the tent big enough',
        'Don\'t do acid Jood',
        'But the salad',
        'Who calls Earth sauce water?',
        'This is the most advanced space game',
        '"I see" said the blind carpenter as he picked up his hammer and saw',
        'Alt+F4 for diamonds',
        'BED',
        'Criticality detected. Reactor meltdown imminent. Evacuate to a safe distance',
        'From the spice mines of Emperor Charizard',
        'If you love Corncob TV shows, it\'s time to tell Spectrum, "No."',
        'I don\'t even want to be around anymore'
    ]
}


def config_dir() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')


def pid_file() -> str:
    return os.path.join(config_dir(), 'pid.txt')


def kill_file() -> str:
    return os.path.join(config_dir(), 'kill.txt')


def load_config(logger: Optional[logging.Logger] = None) -> Config:
    if not logger:
        logger = logging.getLogger(__name__)
    config_path = os.path.join(config_dir(), 'config.json')

    if not os.path.isfile(config_path):
        with open(config_path, 'w') as cfg:
            cfg.write(json.dumps(DEFAULT_CONFIG, indent=4))
        return DEFAULT_CONFIG
    
    with open(config_path, 'r') as cfg:
        config: Config = json.loads(cfg.read())
        try:
            with open(os.path.join(config['server_path'], 'server.properties')) as props:
                items = props.read().split('\n')
                for item in items:
                    if 'level-name' in item:
                        config['save_path'] = os.path.join(config['server_path'], item.split('=')[1])
                        break
                return config
        except Exception:
            logger.exception('Bad config, failed to load server properties')
            raise


if __name__ == '__main__':
    load_config()
