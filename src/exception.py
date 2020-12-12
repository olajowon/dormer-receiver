# Created by zhouwang on 2020/8/27.


class MetricContentError(Exception):
    def __init__(self, message):
        self.message = message
