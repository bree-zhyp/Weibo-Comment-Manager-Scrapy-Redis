# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
# -*- coding: utf-8 -*-
import datetime
import json
import os.path
import time


class JsonWriterPipeline(object):
    """
    写入json文件的pipline
    """

    def __init__(self):
        self.file = None
        if not os.path.exists('../output'):
            os.mkdir('../output')

    def process_item(self, item, spider):
        """
        处理item
        """
        if not self.file:
            now = datetime.datetime.now()
            file_name = spider.name + "_" + now.strftime("%Y%m%d%H%M%S") + '.jsonl'
            self.file = open(f'../output/{file_name}', 'wt', encoding='utf-8')
        item['crawl_time'] = int(time.time())
        line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(line)
        self.file.flush()
        return item


from scrapy_redis.connection import get_redis

class RedisPipeline:
    """
    将数据写入到Redis的Pipeline
    """

    def process_item(self, item, spider):
        """
        处理item，将数据写入到Redis
        """
        redis_conn = get_redis(host='127.0.0.1', port=6381, db=0)
        redis_key = f"{spider.name}:items"
        redis_conn.lpush(redis_key, json.dumps(dict(item), ensure_ascii=False))
        return item
