import json
import time

from common import config

from spiderutil.network import Session
from spiderutil.log import Log
from spiderutil.connector import RedisSet, MongoDB
from spiderutil.exceptions import NetworkException, RetryLimitExceededException

from .extractor import Extractor

BASE_URL = 'http://www.cbooo.cn/'
INTERVAL = config.Config.spider.interval
MAX_RETRY = config.Config.spider.max_retry


def url(path):
    return BASE_URL + path


class CboooSpider:
    def __init__(self):
        self.session = Session()
        self.logger = Log.create_logger('spider')

    def get_id(self, redis: RedisSet):
        start_page = config.Config.spider.start_page
        params = {
            'area': config.Config.spider.area,
            'type': 0,
            'year': 0,
            'initial': '全部',
            'pIndex': start_page
        }

        res = self.session.get(url=url('/Mdata/getMdata_movie'), params=params)
        data = json.loads(res.text)
        self.logger.info('Total: {0} pages, {1} items'.format(data['tPage'], data['tCount']))
        end_page = data['tPage']
        for item in data['pData']:
            redis.add(item['ID'])
        self.logger.info('Page {}'.format(start_page))
        time.sleep(10)
        for i in range(start_page + 1, end_page + 1):
            params['pIndex'] = i
            res = self.session.get(url=url('/Mdata/getMdata_movie'), params=params)
            data = json.loads(res.text)
            for item in data['pData']:
                redis.add(item['ID'])
            self.logger.info('Page {}'.format(i))
            time.sleep(10)

    def start_crawl(self, extractor: Extractor, redis: RedisSet, mongo: MongoDB):
        while not redis.empty():
            movie_id = redis.pop()
            self.logger.info('Movie ID: {}'.format(movie_id))
            try:
                info = self._crawl(movie_id, extractor)
                if info is not None:
                    if mongo.count({'id': movie_id}) <= 0:
                        mongo.insert(info)
                    else:
                        self.logger.info('Duplicate record {}'.format(movie_id))
                else:
                    self.logger.warning('Useless record {}'.format(movie_id))
            except NetworkException as e:
                self.logger.error(e)
                redis.add(movie_id)
            time.sleep(10)

    def _crawl(self, movie_id, extractor: Extractor):
        retry = MAX_RETRY
        while retry:
            try:
                res = self.session.get(url=url('/m/{}'.format(movie_id)))
                info = extractor.extract_info(res.text)
                if info is None:
                    return None
                res = self.session.get(url=url('/Mdata/getMovieEventAll?movieid={}'.format(movie_id)))
                info['event'] = extractor.extract_events(res.text)
                info['id'] = movie_id
                return info
            except (NetworkException, AttributeError) as e:
                self.logger.error(str(e))
                retry -= 1
                if retry <= 0:
                    raise RetryLimitExceededException(movie_id) from e
