# Created by zhouwang on 2020/8/26.

import threading
import time
import configure
import os
import logging
logger = logging.getLogger('base')


class MatchList:
    _instance = None
    blacklist = []
    whitelist = []

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            MatchList._instance = object.__new__(cls)
            MatchList._instance.update()
        return MatchList._instance

    def update(self):
        if os.path.isfile(configure.whitelist_path):
            white_conf = open(configure.whitelist_path)
            self.whitelist = [l.strip() for l in white_conf.readlines()]
        else:
            self.whitelist = []

        if os.path.isfile(configure.blacklist_path):
            black_conf = open(configure.blacklist_path)
            self.blacklist = [l.strip() for l in black_conf.readlines()]
        else:
            self.blacklist = []


class MatchListThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        MatchList().update()

    def run(self):
        logger.info('matchlist running')
        while True:
            time.sleep(60)
            MatchList().update()
        logger.info('matchlist-%d exit')
