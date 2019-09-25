from time import sleep

from gbdex.spider import GBDEXSpider

from spiderutil.connector import MongoDB

if __name__ == '__main__':
    spider = GBDEXSpider()

    mongo = MongoDB('gbdex-api')
    for api in spider.crawl_api():
        mongo.insert(api)
        sleep(2)

    mongo = MongoDB('gbdex-data')
    for item in spider.crawl_data_file():
        mongo.insert(item)
        sleep(2)
