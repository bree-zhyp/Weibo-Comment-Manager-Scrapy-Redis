# -*- coding: utf-8 -*-

BOT_NAME = 'weibo_spider'

SPIDER_MODULES = ['weibo_spider']
NEWSPIDER_MODULE = 'weibo_spider'

ROBOTSTXT_OBEY = False

# cookie = "XSRF-TOKEN=56RLvgqIlfpyyiONiMfyFVuF; WBPSESS=Wk6CxkYDejV3DDBcnx2LOUuyjUb5ny6U8XGAETh1XBU7V1a0-fhQuL49hmFCzrbH5AeFthlj2ysGiR9pALdDjS8hgDPxu_X2lRFoH9dDJI1jQ37tN9yykey5im45ByyWWMuzuc0ps3zwtwlSwHnSqM9k28im52Zen8l44xYGkIU=; SUB=_2A25LXPX2DeRhGeFI7lAQ8S7JzjSIHXVoEHc-rDV8PUNbmtAGLXLdkW9NfRwIdF9iPkVAQBL4b7aYvKR6MGeuFxGh; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WW3gJQ0VAY5QC4H1bR7I7ly5JpX5KzhUgL.FoMcSKzpeK5fSKn2dJLoIpqLxK-LBo5L12qLxK.LBKeL12HkeK-c; ALF=02_1719669414"
cookie = "INAGLOBAL=2324097991757.5234.1717078366598; ALF=1720526170; SUB=_2A25LYegLDeRhGeFI7lAQ8S7JzjSIHXVoH2XDrDV8PUJbkNAGLUj8kW1NfRwIdGZJ0mZK2mbRmJAfCr2jHuFGe_A3; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WW3gJQ0VAY5QC4H1bR7I7ly5JpX5KMhUgL.FoMcSKzpeK5fSKn2dJLoIpqLxK-LBo5L12qLxK.LBKeL12HkeK-c; _s_tentry=-; Apache=6315746680861.754.1717934848261; ULV=1717934848274:2:1:1:6315746680861.754.1717934848261:1717078366600"

DEFAULT_REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:61.0) Gecko/20100101 Firefox/61.0',
    # 'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36",
    'Cookie': cookie
}

# 使用Redis调度器
# SCHEDULER = "scrapy_redis.scheduler.Scheduler"

# 使用Redis去重
# DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"

# 指定Redis连接信息
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

# 允许中断恢复
SCHEDULER_PERSIST = True

CONCURRENT_REQUESTS = 16

DOWNLOAD_DELAY = 1

DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': None,
    'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': None,
    'weibo_spider.middlewares.IPProxyMiddleware': 100,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 101,
}

ITEM_PIPELINES = {
    # 'weibo_spider.pipelines.JsonWriterPipeline': 300,
    'weibo_spider.pipelines.RedisPipeline': 299,
}


