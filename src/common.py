from config import pid_file


def read_pid() -> int:
    try:
        with open(pid_file(), 'r') as input:
            return int(input.read())
    except Exception:
        return -1
