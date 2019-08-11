from time import sleep

from common.persistence import MongoDB
from juhe.spider import JuheSpider

if __name__ == '__main__':
    spider = JuheSpider()

    mongo = MongoDB('juhe-api')
    for link, data in spider.crawl_api():
        print(data['标题'], link)
        mongo.insert(data)
        sleep(5)

    mongo = MongoDB('juhe-data')
    for link, data in spider.crawl_data():
        print(data['标题'], link)
        mongo.insert(data)
        sleep(5)
