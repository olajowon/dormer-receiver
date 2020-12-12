# Created by zhouwang on 2020/8/26.
from elasticsearch.helpers import bulk as es_bulk
from . import db, matchlist
from .exception import MetricContentError
import configure
import threading
import hashlib
import time
import re
import traceback
import logging
logger = logging.getLogger('base')


def storage_process(queue):
    threads = []
    
    # 创建匹配规则列表的线程
    t = matchlist.MatchListThread()
    threads.append(t)

    # 创建真正处理存储的线程
    logger.info('storage running')
    for i in range(4):
        t = StorageThread(i, queue)
        threads.append(t)

    for t in threads:
        t.setDaemon(True)
        t.start()

    while True:
        for t in threads:
            if not t.is_alive():
                exit(1)
        else:
            time.sleep(1)
    logger.info('storage exit')

#n = 0
class StorageThread(threading.Thread):
    def __init__(self, thread_id, queue):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.queue = queue
        self.redis = db.Redis()
        self.es = db.Elasticsearch()
        self.es_index = configure.elasticsearch['index']
        self.matchlist = matchlist.MatchList()
        self.td_engine = db.TDengine()
        self.td_engine_cursor = self.td_engine.cursor()

    def run(self):
        logger.info('storage-%d running' % self.thread_id)
        while True:
            if self.queue.empty() is False:
                content = self.queue.get()
                if content:
                    try:
                        lines = content.decode().split('\n')
                    except Exception as e:
                        logger.debug('storage-%d, %s, %s' % (self.thread_id, line, str(e)))
                        continue

                    for line in lines:
                        if not line:
                            continue
            
                        try:
                            metric, datapoint = self.clean_metric_line(line)
                            self.handle_metric_index(metric)
                            self.write_metric_datapoint(metric, datapoint)
                        except MetricContentError as e:
                            if line.startswith('app'):
                                logger.debug('storage-%d, %s, %s' % (self.thread_id, line, str(e)))
                        except Exception as _:
                            print(self.thread_id, 'error')
                            logger.error('storage-%d, %s, %s' % (self.thread_id, line, traceback.format_exc()))
            else:
                time.sleep(1)

    def clean_metric_line(self, line):
        try:
            metric, dp_value, dp_ts = line.strip().split()
            dp_value, dp_ts = float(dp_value), float(dp_ts)
        except:
            raise MetricContentError('指标格式不正确 指标名 值 时间戳')

        if metric.find(';') > -1:
            metric_path, metric_tag = metric.split(';', 1)
            metric_tag = metric_tag.replace('=', ':')
        else:
            metric_path, metric_tag = metric, ''

        for idx, node in enumerate(metric_path.split('.')):
            if not node:
                raise MetricContentError('指标路径节点[%d]不允许为空' % idx)

            if not re.match('^[0-9a-zA-Z_-]*$', node):
                raise MetricContentError('指标路径节点[%d]只允许0-9a-zA-Z_-组成' % idx)

            if idx == 0 and not re.match('^[a-zA-Z]', node):
                raise MetricContentError('指标名必须字母开头')

        if metric_tag:
            tags = {}
            for idx, kv in enumerate(metric_tag.split(';')):
                if not kv:
                    raise MetricContentError('指标Tag[%d]不允许为空' % idx)
                try:
                    k, v = kv.split(':')
                except:
                    raise MetricContentError('指标Tag[%d]格式不正确' % idx)

                if not re.match('^[a-z]*$', k):
                    raise MetricContentError('指标Tag键只允许小写字母组成')

                if not re.match('^[0-9a-zA-Z_-]*$', v):
                    raise MetricContentError('指标Tag值只允许0-9a-zA-Z_-组成')

                if k in tags:
                    raise MetricContentError('指标Tag不允许重复的键[%s]' % k)
                tags[k] = v

            metric_tag = ';'.join(['%s:%s' % (k, v) for k,v in sorted(tags.items())])
            metric = ';'.join((metric_path, metric_tag))

        try:
            dp_value = float(dp_value)
        except:
            raise MetricContentError('指标值必须是数字')

        try:
            dp_ts = int(dp_ts)//60*60
        except:
            raise MetricContentError('指标时间戳必须是数字')

        if dp_ts <= time.time() - (86400 * 100):
            raise MetricContentError('只允许100天以内的时间戳')

        if self.matchlist.blacklist:
            for b in self.matchlist.blacklist:
                if re.search(b, metric):
                    raise MetricContentError('指标已被列入黑名单')

        if self.matchlist.whitelist:
            for w in self.matchlist.whitelist:
                if re.search(w, metric):
                    break
            else:
                raise MetricContentError('指标不在白名单内')
        return metric, (dp_ts, dp_value)

    def handle_metric_index(self, metric):
        metric_index_is_exist = self.check_metric_index_is_exist(metric)
        if not metric_index_is_exist:
            self.create_metric_index_to_es(metric)
            self.create_metric_index_to_redis(metric)

    def create_metric_index_to_es(self, metric):
        metric_node_list = metric.split('.')
        actions = []
        for i in range(0, len(metric_node_list)):
            if i:
                name = '.'.join(metric_node_list[:i+1])
                parent = '.'.join(metric_node_list[:i])
            else:
                name, parent = metric_node_list[i], ''

            node = metric_node_list[i]
            leaf = 0
            tag = {}
            if name == metric:
                leaf = 1
                if name.find(';') > -1:
                    tag = {kv.split(':')[0]: kv.split(':')[1] for kv in name.split(';')[1:]}

            body = {'query': {'term': {'name': name}}}
            res = self.es.search(index='metric', doc_type='_doc', body=body)

            if not res.get('hits', {}).get('hits'):
                action = {
                    '_index': self.es_index,
                    '_id': name,
                    '_source': {
                        'name': name,
                        'hash': hashlib.md5(name.encode(encoding='utf-8')).hexdigest(),
                        'alias': '',
                        'path': name.split(';')[0] if tag else name,
                        'parent': parent,
                        'text': node,
                        'leaf': leaf,
                        'tag': tag
                    }
                }
                actions.append(action)

        if actions:
            es_bulk(self.es, actions)

    def create_metric_index_to_redis(self, metric):
        for retry in range(3):
            try:
                self.redis.set(metric, 1)
            except Exception as e:
                if retry == 2:
                    raise e
            else:
                break

    def check_metric_index_is_exist(self, metric):
        for retry in range(3):
            try:
                return bool(self.redis.get(metric))
            except Exception as e:
                if retry == 2:
                    raise e

    def write_metric_datapoint(self, metric, datapoint):
        # global n
        tab_name = 't_%s' % hashlib.md5(metric.encode(encoding='utf-8')).hexdigest()
        sql = 'INSERT INTO %s USING metric_datapoints TAGS ("%s") VALUES (%d000, %s);' % (
            tab_name,
            metric,
            *datapoint
        )

        for retry in range(3):
            try:
                self.td_engine_cursor.execute(sql)
            except Exception as e:
                if retry == 2:
                    raise e
            else:
                break
        # global n
        # n += 1
        # if n >= 20000:
        #     print(time.time())
