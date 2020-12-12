# Created by zhouwang on 2020/9/24.

from src import receive, storage
import multiprocessing
import configure
import sys
import os
import signal
import logging
import logging.config
logger = logging.getLogger('base')

ADDR = '0.0.0.0'
PORT = int(sys.argv[1])


def run():
    queue = multiprocessing.Queue()
    receive_process = multiprocessing.Process(target=receive.receive_process, args=(queue, ADDR, PORT))
    storage_process = multiprocessing.Process(target=storage.storage_process, args=(queue,))

    processes = (receive_process, storage_process)
    for p in processes:
        p.daemon = True
        p.start()

    for p in processes:
        p.join()

    # while True:
    #     for p in processes:
    #         if not p.is_alive():
    #             exit()
    #     time.sleep(1)


def init():
    # 配置 LOG
    config = configure.logging
    config['handlers']['base']['filename'] = config['handlers']['base']['filename'] % PORT
    logging.config.dictConfig(config)

    # 保存 PID
    open('/var/run/dormer-receiver-%d.pid' % PORT, 'w').write(str(os.getpid()))
    logger.info('pid' + str(os.getpid()) + 'ppid' + str(os.getpgid(os.getpid())))

    # 设置退出信号
    def sig_handler(*args):
        logger.info('清理进程组：%s' % os.getpgid(os.getpid()))
        os.killpg(os.getpgid(os.getpid()), signal.SIGKILL)
    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGCHLD, sig_handler)


if __name__ == '__main__':
    init()
    run()
