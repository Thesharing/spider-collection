import time

from imdb.spider import IMDBSpider
from spiderutil.connector import MongoDB

if __name__ == '__main__':
    spider = IMDBSpider()
    mongo = MongoDB('imdb')
    for title, link in spider.top250(start_from='/title/tt0476735/'):
        if mongo.find({'link': link}) is None:
            print(link)
            mongo.insert(spider.crawl(link))
            time.sleep(2)
