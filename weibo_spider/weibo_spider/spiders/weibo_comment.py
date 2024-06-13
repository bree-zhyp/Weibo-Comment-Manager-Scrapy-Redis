#!/usr/bin/env python
# encoding: utf-8

import datetime
import json
import re
from scrapy import Spider, Request
import dateutil.parser
from scrapy_redis.spiders import RedisSpider
import redis
from redis.exceptions import ResponseError
from rediscluster import RedisCluster

class TweetSpiderByKeyword(RedisSpider):
    """
    关键词搜索采集
    """
    name = "weibo_comment"
    # base_url = "https://s.weibo.com/"
    redis_key="weibo_comment:start_urls"


    def __init__(self, *args, **kwargs):
        # super(RedisSpider, self).__init__(*args, **kwargs)
        super(TweetSpiderByKeyword, self).__init__(*args, **kwargs)

        # Redis 集群的启动节点
        startup_nodes = [
            {"host": "127.0.0.1", "port": "6379"},  
            {"host": "127.0.0.1", "port": "6380"},
            {"host": "127.0.0.1", "port": "6381"},
        ]

        # 创建 RedisCluster 实例
        self.rc = RedisCluster(startup_nodes=startup_nodes, decode_responses=True)

    def add_urls_to_redis(self):
        """
        将待爬取的 URL 添加到 Redis 队列中
        """

        # 清空 Redis 队列
        try:
            self.rc.delete('weibo_comment:start_urls')
        except redis.exceptions.ResponseError as e:
            if "MOVED" in str(e):
                # 处理MOVED错误的代码，例如重试或记录日志
                pass
            else:
                raise e

        # 这里 keywords 可替换成实际待采集的数据
        self.keywords = ['美景']
        # 这里的时间可替换成实际需要的时间段
        start_time = datetime.datetime(year=2024, month=6, day=10, hour=0)
        end_time = datetime.datetime(year=2024, month=6, day=11, hour=23)
        # 是否按照小时进行切分，数据量更大; 对于非热门关键词**不需要**按照小时切分

        is_split_by_hour = True
        urls = []
        for keyword in self.keywords:
            if not is_split_by_hour:
                _start_time = start_time.strftime("%Y-%m-%d-%H")
                _end_time = end_time.strftime("%Y-%m-%d-%H")
                url = f"https://s.weibo.com/weibo?q={keyword}&timescope=custom%3A{_start_time}%3A{_end_time}&page=1"
                urls.append(url)
            else:
                time_cur = start_time
                while time_cur < end_time:
                    _start_time = time_cur.strftime("%Y-%m-%d-%H")
                    _end_time = (time_cur + datetime.timedelta(hours=1)).strftime("%Y-%m-%d-%H")
                    url = f"https://s.weibo.com/weibo?q={keyword}&timescope=custom%3A{_start_time}%3A{_end_time}&page=1"
                    urls.append(url)
                    time_cur = time_cur + datetime.timedelta(hours=1)

        # 将 URL 添加到 Redis 队列中
        for url in urls:
            self.rc.rpush('weibo_comment:start_urls', url)

        # 获取队列中的所有元素
        start_urls = self.rc.lrange('weibo_comment:start_urls', 0, -1)
        print("URLs in Redis Queue:")
        for url in start_urls:
            print(url)


    def start_requests(self):
        """
        爬虫入口
        """
        # 将URL添加到Redis队列中
        self.add_urls_to_redis()

        # 开始爬取
        while True:
            # print("===========================try========================")
            # 从Redis队列中取出URL进行爬取
            url = self.rc.lpop('weibo_comment:start_urls')

            if url:
                # url = url.decode('utf-8')
                # print("===============okkkk===================")
                yield Request(url, callback=self.parse)


    def parse(self, response, **kwargs):
        """
        网页解析
        """
        html = response.text
        if '<p>抱歉，未找到相关结果。</p>' in html:
            self.logger.info(f'no search result. url: {response.url}')
            return
        tweets_infos = re.findall('<div class="from"\s+>(.*?)</div>', html, re.DOTALL)
        for tweets_info in tweets_infos:
            tweet_ids = re.findall(r'weibo\.com/\d+/(.+?)\?refer_flag=1001030103_" ', tweets_info)
            for tweet_id in tweet_ids:
                url = f"https://weibo.com/ajax/statuses/show?id={tweet_id}"
                yield Request(url, callback=self.parse_tweet, meta=response.meta, priority=10)
        next_page = re.search('<a href="(.*?)" class="next">下一页</a>', html)
        if next_page:
            url = "https://s.weibo.com" + next_page.group(1)
            yield Request(url, callback=self.parse, meta=response.meta)

    def parse_tweet(self, response):
        """
        解析推文
        """
        data = json.loads(response.text)
        item = self.parse_tweet_info(data)
        # item['keyword'] = response.meta['keyword']
        if item['isLongText']:
            url = "https://weibo.com/ajax/statuses/longtext?id=" + item['mblogid']
            yield Request(url, callback=self.parse_long_tweet, meta={'item': item}, priority=20)
        else:
            yield item

    def parse_tweet_info(self, data):
        """
        解析推文数据
        """
        tweet = {
            "_id": str(data['mid']),
            "mblogid": data['mblogid'],
            "created_at": self.parse_time(data['created_at']),
            "geo": data.get('geo', None),
            "ip_location": data.get('region_name', None),
            "reposts_count": data['reposts_count'],
            "comments_count": data['comments_count'],
            "attitudes_count": data['attitudes_count'],
            "source": data['source'],
            "content": data['text_raw'].replace('\u200b', ''),
            "pic_urls": ["https://wx1.sinaimg.cn/orj960/" + pic_id for pic_id in data.get('pic_ids', [])],
            "pic_num": data['pic_num'],
            'isLongText': False,
            'is_retweet': False,
            "user": self.parse_user_info(data['user']),
            "keywords": self.keywords,
        }
        if '</a>' in tweet['source']:
            tweet['source'] = re.search(r'>(.*?)</a>', tweet['source']).group(1)
        if 'page_info' in data and data['page_info'].get('object_type', '') == 'video':
            media_info = None
            if 'media_info' in data['page_info']:
                media_info = data['page_info']['media_info']
            elif 'cards' in data['page_info'] and 'media_info' in data['page_info']['cards'][0]:
                media_info = data['page_info']['cards'][0]['media_info']
            if media_info:
                tweet['video'] = media_info['stream_url']
                # 视频播放量
                tweet['video_online_numbers'] = media_info.get('online_users_number', None)
        tweet['url'] = f"https://weibo.com/{tweet['user']['_id']}/{tweet['mblogid']}"
        if 'continue_tag' in data and data['isLongText']:
            tweet['isLongText'] = True
        if 'retweeted_status' in data:
            tweet['is_retweet'] = True
            tweet['retweet_id'] = data['retweeted_status']['mid']
        if 'reads_count' in data:
            tweet['reads_count'] = data['reads_count']
        return tweet

    def parse_long_tweet(self, response):
        """
        解析长推文
        """
        data = json.loads(response.text)['data']
        item = response.meta['item']
        item['content'] = data['longTextContent']
        yield item

    def base62_decode(self, string):
        """
        base
        """
        alphabet = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        string = str(string)
        num = 0
        idx = 0
        for char in string:
            power = (len(string) - (idx + 1))
            num += alphabet.index(char) * (len(alphabet) ** power)
            idx += 1

        return num


    def reverse_cut_to_length(self, content, code_func, cut_num=4, fill_num=7):
        """
        url to mid
        """
        content = str(content)
        cut_list = [content[i - cut_num if i >= cut_num else 0:i] for i in range(len(content), 0, (-1 * cut_num))]
        cut_list.reverse()
        result = []
        for i, item in enumerate(cut_list):
            s = str(code_func(item))
            if i > 0 and len(s) < fill_num:
                s = (fill_num - len(s)) * '0' + s
            result.append(s)
        return ''.join(result)


    def url_to_mid(self, url: str):
        """>>> url_to_mid('z0JH2lOMb')
        3501756485200075
        """
        result = self.reverse_cut_to_length(url, self.base62_decode)
        return int(result)


    def parse_time(self, s):
        """
        Wed Oct 19 23:44:36 +0800 2022 => 2022-10-19 23:44:36
        """
        return dateutil.parser.parse(s).strftime('%Y-%m-%d %H:%M:%S')


    def parse_user_info(self, data):
        """
        解析用户信息
        """
        # 基础信息
        user = {
            "_id": str(data['id']),
            "avatar_hd": data['avatar_hd'],
            "nick_name": data['screen_name'],
            "verified": data['verified'],
        }
        # 额外的信息
        keys = ['description', 'followers_count', 'friends_count', 'statuses_count',
                'gender', 'location', 'mbrank', 'mbtype', 'credit_score']
        for key in keys:
            if key in data:
                user[key] = data[key]
        if 'created_at' in data:
            user['created_at'] = self.parse_time(data.get('created_at'))
        if user['verified']:
            user['verified_type'] = data['verified_type']
            if 'verified_reason' in data:
                user['verified_reason'] = data['verified_reason']
        return user