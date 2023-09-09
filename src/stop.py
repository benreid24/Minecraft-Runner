from datetime import datetime

from server_config import kill_file


def main():
    with open(kill_file(), 'w') as kf:
        kf.writelines([
            str(datetime.now().timestamp() + 10)
        ])


if __name__ == '__main__':
    main()
