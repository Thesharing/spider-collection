from gbdex.spider import crawl_api, crawl_data_file
from common.persistence import MongoDB
from time import sleep

if __name__ == '__main__':
    mongo = MongoDB('gbdex')
    for api in crawl_api():
        mongo.insert(api)
        sleep(2)

    for item in crawl_data_file():
        mongo.insert(item)
        sleep(2)
