# Created by zhouwang on 2020/9/24.

import sys
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(PROJECT_DIR, 'venv')
ACTION = sys.argv[1]
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else '*'
PGID = os.getpgid(os.getpid())


def start():
    print('#### start\n')
    status = os.system(f'source {VENV_DIR}/bin/activate && cd {PROJECT_DIR} && '
                       f'pip install -r {PROJECT_DIR}/requirements.txt && '
                       f'cp ./etc/supervisord.d/* /etc/supervisord.d/ && '
                       f'supervisorctl update dormer-receiver && '
                       f'supervisorctl start dormer-receiver:{PORT}')
    print('#### start %s\n' % ('successful' if status == 0 else 'failure'))


def stop():
    print('#### stop\n')
    status = os.system(f'supervisorctl stop dormer-receiver:{PORT}')
    print('#### stop %s\n' % ('successful' if status == 0 else 'failure'))


def restart():
    print('#### restart\n')
    status = os.system(f'source {VENV_DIR}/bin/activate && cd {PROJECT_DIR} && '
                       f'pip install -r {PROJECT_DIR}/requirements.txt && '
                       f'cp ./etc/supervisord.d/* /etc/supervisord.d/ && '
                       f'supervisorctl update dormer-receiver && '
                       f'supervisorctl restart dormer-receiver:{PORT}')
    print('#### restart %s\n' % ('successful' if status == 0 else 'failure'))


def pip():
    print('#### pip\n')
    status = os.system(f'source {VENV_DIR}/bin/activate && '
                       f'pip install -r {PROJECT_DIR}/requirements.txt')
    print('#### pip %s\n' % ('successful' if status == 0 else 'failure'))


def init():
    if not os.path.isdir(VENV_DIR):
        os.system(f'cd {PROJECT_DIR} && python3 -m venv venv')


if __name__ == '__main__':
    init()

    if ACTION == 'start':
        start()
    elif ACTION == 'stop':
        stop()
    elif ACTION == 'restart':
        restart()
    elif ACTION == 'pip':
        pip()
