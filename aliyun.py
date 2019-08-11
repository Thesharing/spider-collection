from time import sleep

from aliyun.spider import AliyunSpider
from common.persistence import MongoDB

if __name__ == '__main__':
    spider = AliyunSpider()
    mongo = MongoDB('aliyun')
    for data in spider.crawl_list():
        mongo.insert(data)
        sleep(5)
