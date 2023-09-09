import psutil
import subprocess

from common import read_pid
    

def check_alive(pid: int) -> bool:
    return psutil.pid_exists(pid)
    

def main():
    pid = read_pid()
    print(pid)
    if not check_alive(pid):
        print('Not alive')
        subprocess.Popen(
            ['python', 'manager.py'],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL
        )
    else:
        print('Alive')


if __name__ == '__main__':
    main()
