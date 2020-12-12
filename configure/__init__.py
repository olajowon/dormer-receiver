# Created by zhouwang on 2020/9/23.
import os
import configparser

path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'env')

try:
    env = open(path, 'r+').read().strip()
except Exception as e:
    print(e)
    env = 'development'


project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

whitelist_path = os.path.join(project_path, 'conf', 'whitelist.txt')
blacklist_path = os.path.join(project_path, 'conf', 'blacklist.txt')

cf = configparser.ConfigParser()
cf.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), '%s.ini' % env))

redis = {
    'host': cf.get('redis', 'host'),
    'port': cf.get('redis', 'port'),
    'db': cf.get('redis', 'db'),
    'password': cf.get('redis', 'password'),
}

elasticsearch = {
    'hosts': [{'host': hp.split(':')[0], 'port': hp.split(':')[1]}
              for hp in cf.get('elasticsearch', 'hosts').split(',')],
    'index': cf.get('elasticsearch', 'index')
}

tdengine = {
    'host': cf.get('tdengine', 'host'),
    'user': cf.get('tdengine', 'user'),
    'password': cf.get('tdengine', 'password'),
    'database': cf.get('tdengine', 'database')
}


logging = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s [%(module)s:%(funcName)s:%(lineno)s] [%(threadName)s:%(thread)d] '
                      '%(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'base': {
            'level': 'DEBUG',
            'class': 'concurrent_log_handler.ConcurrentRotatingFileHandler',
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 50,
            'delay': True,
            'filename': '/var/log/dormer-receiver/base-%d.log',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'base': {
            'handlers': ['base'],
            'level': cf.get('logger', 'level'),
        },
    }
}

