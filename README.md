# 准备
## ES
    {
        "name": "metric",
        "data": {
            "settings": {
                "index": {
                    "number_of_shards": 3,
                    "number_of_replicas": 1
                }
            },
            "mappings": {
                "properties": {
                    "name": {
                        "type": "keyword"
                    },
                    "hash": {
                        "type": "keyword"
                    },
                    "alias": {
                        "type": "keyword"
                    },
                    "path": {
                        "type": "keyword"
                    },
                    "parent": {
                        "type": "keyword"
                    },
                    "text": {
                        "type": "keyword"
                    },
                    "leaf": {
                        "type": "integer"
                    },
                    "tag": {
                        "type": "object"
                    }
                }
            }
        }
    }


## TDengine
### 创建数据库
    CREATE DATABASE dormer KEEP 1095 DAYS 10 BLOCKS 4;

### 创建超级表
    CREATE TABLE metric_datapoints (ts timestamp, value float) TAGS (metric_name binary(1024));


# 运行
## 本地开发
### 创建环境文件
	cd dormer-receiver
	echo development > env

### 修改配置文件
    cd configure
    cp example.ini development.ini # 与env同名
    vim development.ini

### 创建日志目录
	mkdir /var/log/dormer-receiver

### 启动服务
	python3 app.py 2003


## 生产运行
### yum
    yum install supervisor
    systemctl start supervisord.service

### 创建环境文件
	cd dormer-receiver
	echo production > env

### 修改配置文件
    cd configure
    cp example.ini production.ini # 与env同名
    vim production.ini

### 创建日志目录
	mkdir /var/log/dormer-receiver

### 启动、停止、重启服务
	python3 server.py start|stop|restart [port]

