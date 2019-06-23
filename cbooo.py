from cbooo.spider import Spider
from cbooo.extractor import Extractor
from common.persistence import RedisSet, MongoDB

if __name__ == '__main__':
    spider = Spider()
    ext = Extractor()
    redis = RedisSet('cbooo')
    mongo = MongoDB('cbooo-total')

    # from pprint import pprint
    # pprint(spider._crawl('640367', ext))

    spider.start_crawl(ext, redis, mongo)
    # spider.get_id(redis)
