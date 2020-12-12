# Created by zhouwang on 2020/8/25.
import redis
import configure
import elasticsearch
import taos
import threading


def lock(func):
    func.__lock__ = threading.Lock()

    def _w(*args, **kwargs):
        with func.__lock__:
            return func(*args, **kwargs)
    return _w


class Redis:
    # _instance = None
    # @lock
    # def __new__(cls, *args, **kwargs):
    #     if not cls._instance:
    #         pool = redis.ConnectionPool(**configure.redis)
    #         connect = redis.Redis(connection_pool=pool)
    #         Redis._instance = connect
    #     return Redis._instance

    def __new__(cls, *args, **kwargs):
        return redis.Redis(**configure.redis)


class Elasticsearch:
    _instance = None

    @lock
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            connect = elasticsearch.Elasticsearch(**configure.elasticsearch)
            Elasticsearch._instance = connect
        return Elasticsearch._instance


class TDengine:
    # _instance = None
    # @lock
    # def __new__(cls, *args, **kwargs):
    #     if not cls._instance:
    #         connect = taos.connect(**configure.td)
    #         TDengine._instance = connect
    #     return TDengine._instance

    def __new__(cls, *args, **kwargs):
        return taos.connect(**configure.tdengine)
