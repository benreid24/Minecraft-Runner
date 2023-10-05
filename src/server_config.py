from typing import TypedDict, List, Optional
import os
import json
import logging


class RandomItem(TypedDict):
    name: str
    weight: float
    min_qty: int
    max_qty: int


class SummonCreature(TypedDict):
    name: str
    weight: float
    min_qty: int
    max_qty: int


class Effect(TypedDict):
    name: str
    weight: float
    level: int
    duration: int
    message: Optional[str]


class Config(TypedDict):
    server_path: str
    start_command: List[str]
    save_path: str  # Computed
    
    backup_path: str
    backup_interval: int

    phrase_interval: int
    phrases: List[str]

    random_items: List[RandomItem]
    random_item_interval: int

    summon_interval: int
    summon_options: List[SummonCreature]

    effect_interval: int
    effect_options: List[Effect]

    creeper_interval: int


DEFAULT_CONFIG: Config = {
    'server_path': '/galacticraft',
    'start_command': ['java', '-Xmx8G', '-Dfml.queryResult=confirm', '-jar', 'forge_server.jar', 'nogui'],

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
        'I don\'t even want to be around anymore',
        'Did you know that Void is short for Sir George Lord of the Void Ponyo Tzatziki Juan Pablo Pitter Pats Reid?'
    ],

    'random_item_interval': 30 * 60,
    'random_items': [
        {
            'name': 'minecraft:fish',
            'weight': 15,
            'min_qty': 1,
            'max_qty': 4
        },
        {
            'name': 'minecraft:rotten_flesh',
            'weight': 15,
            'min_qty': 1,
            'max_qty': 4
        },
        {
            'name': 'minecraft:grass',
            'weight': 15,
            'min_qty': 1,
            'max_qty': 1
        },
        {
            'name': 'minecraft:string',
            'weight': 15,
            'min_qty': 1,
            'max_qty': 4
        },
        {
            'name': 'minecraft:beetroot',
            'weight': 15,
            'min_qty': 1,
            'max_qty': 4
        },
        {
            'name': 'minecraft:poisonous_potato',
            'weight': 15,
            'min_qty': 1,
            'max_qty': 1
        },
        {
            'name': 'minecraft:egg',
            'weight': 15,
            'min_qty': 1,
            'max_qty': 4
        },
        {
            'name': 'minecraft:diamond',
            'weight': 1,
            'min_qty': 1,
            'max_qty': 4
        },
    ],

    'summon_interval': 2400,
    'summon_options': [
        {
            'name': 'chicken',
            'weight': 15,
            'min_qty': 1,
            'max_qty': 5
        },
        {
            'name': 'ocelot',
            'weight': 20,
            'min_qty': 1,
            'max_qty': 2
        },
        {
            'name': 'cow',
            'weight': 20,
            'min_qty': 1,
            'max_qty': 1
        },
        {
            'name': 'zombie',
            'weight': 20,
            'min_qty': 2,
            'max_qty': 7
        },
        {
            'name': 'skeleton',
            'weight': 20,
            'min_qty': 2,
            'max_qty': 6
        },
        {
            'name': 'zombie',
            'weight': 1,
            'min_qty': 12,
            'max_qty': 20
        },
    ],

    'effect_interval': 1200,
    'effect_options': [
        {
            'name': 'levitation',
            'weight': 10,
            'duration': 4,
            'level': 1
        },
        {
            'name': 'glowing',
            'weight': 20,
            'duration': 30,
            'level': 1,
        },
        {
            'name': 'slowness',
            'weight': 20,
            'duration': 10,
            'level': 3,
            'message': '{player} suddenly gained weight'
        },
        {
            'name': 'nausea',
            'weight': 30,
            'duration': 15,
            'level': 255,
            'message': '{player} must have eaten something bad'
        },
        {
            'name': 'blindness',
            'weight': 10,
            'duration': 4,
            'level': 1,
            'message': 'Someone tell {player} to open their eyes!'
        },
    ],

    'creeper_interval': 3600
}


def merge_configs(existing: Config) -> None:
    for key, value in DEFAULT_CONFIG.items():
        if isinstance(value, dict) and key in existing and isinstance(DEFAULT_CONFIG[key], dict):
            merge_configs(existing[key], value)
        else:
            if key not in existing:
                existing[key] = value


def config_dir() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')


def pid_file() -> str:
    return os.path.join(config_dir(), 'pid.txt')


def kill_file() -> str:
    return os.path.join(config_dir(), 'kill.txt')


def write_config(config: Config) -> None:
    config_path = os.path.join(config_dir(), 'config.json')
    with open(config_path, 'w') as cfg:
        cfg.write(json.dumps(config, indent=4))


def load_config(logger: Optional[logging.Logger] = None) -> Config:
    if not logger:
        logger = logging.getLogger(__name__)
    config_path = os.path.join(config_dir(), 'config.json')

    if not os.path.isfile(config_path):
        write_config(DEFAULT_CONFIG)
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

            merge_configs(config)
            write_config(config)
            return config
        except Exception:
            logger.exception('Bad config, failed to load server properties')
            raise


if __name__ == '__main__':
    load_config()
