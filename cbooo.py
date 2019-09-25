from spiderutil.connector import RedisSet, MongoDB

from cbooo.spider import CboooSpider
from cbooo.extractor import Extractor

if __name__ == '__main__':
    spider = CboooSpider()
    ext = Extractor()
    redis = RedisSet('cbooo')
    redis.check_connection()
    mongo = MongoDB('cbooo')
    mongo.check_connection()

    spider.get_id(redis)
    spider.start_crawl(ext, redis, mongo)
