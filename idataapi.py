from idataapi.spider import IDataAPISpider

if __name__ == '__main__':
    spider = IDataAPISpider()
    for data in spider.crawl_api():
        print(data)
