from typing import TypedDict, List
import os
import json
import shutil
import datetime

METADATA_FILE = 'backups.json'
SAVE_COUNT = 5
DAY_ROLL_COUNT = 5

class BackupMetadata(TypedDict):
    path: str  # local to dir
    time: int

class BackupDay(TypedDict):
    path: str  # local to BACKUP_PATH
    time: int
    backups: List[BackupMetadata]

class Registry(TypedDict):
    backups: List[BackupDay]


DEFAULT_REGISTRY: Registry = {
    'backups': []
}

_registry: Registry = DEFAULT_REGISTRY


def _get_current_date_index() -> int:
    START_DATE = datetime.date(2023, 9, 6)
    today = datetime.date.today()
    return (today - START_DATE).days
    

def _find_or_create_day_backup(backup_path: str) -> BackupDay:
    global _registry

    index = _get_current_date_index()
    for day in _registry['backups']:
        if day['time'] == index:
            return day
    day: BackupDay = {
        'backups': [],
        'path': datetime.date.today().strftime("%Y-%m-%d"),
        'time': index
    }
    _registry['backups'].append(day)
    path = os.path.join(backup_path, day['path'])
    if not os.path.isdir(path):
        os.mkdir(path)
    return day


def take_backup(save_path: str, backup_path: str):
    day = _find_or_create_day_backup(backup_path)
    now = datetime.datetime.now()
    backup: BackupMetadata = {
        'path': now.time().strftime('%H-%M'),
        'time': int(now.timestamp())
    }
    day['backups'].append(backup)
    day_path = os.path.join(backup_path, day['path'])
    backup_dir = os.path.join(day_path, backup['path'])
    if not os.path.isdir(backup_dir):
        os.mkdir(backup_dir)
    dst_path = os.path.join(backup_dir, os.path.basename(save_path))
    shutil.copytree(save_path, dst_path, dirs_exist_ok=True)

    prune_and_save(backup_path)


def prune_and_save(backup_path: str):
    global _registry

    # Prune days first
    _registry['backups'] = sorted(_registry['backups'], key=lambda b: b['time'], reverse=True)
    for day in _registry['backups'][DAY_ROLL_COUNT:]:
        shutil.rmtree(os.path.join(backup_path, day['path']))
    _registry['backups'] = _registry['backups'][0:DAY_ROLL_COUNT]

    # Prune backups in each day
    for day in _registry['backups']:
        day['backups'] = sorted(day['backups'], key=lambda b: b['time'], reverse=True)
        for backup in day['backups'][SAVE_COUNT:]:
            path = os.path.join(backup_path, day['path'])
            shutil.rmtree(os.path.join(path, backup['path']))
        day['backups'] = day['backups'][0:SAVE_COUNT]

    # Write metadata
    with open(os.path.join(backup_path, METADATA_FILE), 'w') as out:
        out.write(json.dumps(_registry, indent=4))


def init(backup_path: str):
    if not os.path.isdir(backup_path):
        os.mkdir(backup_path)
    
    try:
        global _registry
        with open(os.path.join(backup_path, METADATA_FILE), 'r') as input:
            _registry = json.loads(input.read())
    except Exception:
        _registry = DEFAULT_REGISTRY
