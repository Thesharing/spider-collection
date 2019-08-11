import json
import requests

from common.log import Log


class AliyunSpider:
    def __init__(self):
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
        self.log = Log.create_logger('aliyun', level='INFO')

    def crawl_list(self, page=1, url=None):
        headers = {
            'user-agent': self.user_agent,
            'referer': 'https://market.aliyun.com/products/56956004'
        }
        page_size = 50
        page_index = page
        list_url = 'https://market.aliyun.com/api/ajax/product/queryProducts.json?' \
                   'pageSize={0}&pageIndex={1}&categoryId=56956004'.format(page_size, '{0}')

        r = requests.get(list_url.format(page_index), headers=headers)
        query_result = json.loads(r.text)['result']
        total_records, total_page = query_result['totalRecords'], query_result['totalPage']
        self.log.info('Total {} records, {} pages'.format(total_records, total_page))
        start = url is None
        for product in query_result['products']:
            info = self._parse_info(product)
            if not start:
                if info['url'] != url:
                    continue
                else:
                    start = True
            if 'API' in info['delivery_method']:
                self.log.info('Crawling {0}({1})'.format(info['title'], info['url']))
                info['price'], info['api'], info['comments'] = self._crawl_detail(info)
                yield info

        while page_index < total_page:
            page_index += 1
            r = requests.get(list_url.format(page_index), headers=headers)
            query_result = json.loads(r.text)['result']
            for product in query_result['products']:
                info = self._parse_info(product)
                if 'API' in info['delivery_method']:
                    self.log.info('Crawling {0}({1})'.format(info['title'], info['url']))
                    info['price'], info['api'], info['comments'] = self._crawl_detail(info)
                    yield info

    @staticmethod
    def _parse_info(info):
        return {
            'title': info['title'],
            'shop_name': info['shop_name'],
            'shop_id': info['shop_id'],
            'shop_url': info['shop_url'],
            'tags': info['tagList'],
            'short_description': info['short_description'],
            'category_id': info['category_id'],
            'delivery_method': info['delivery_method'],
            'url': info['url'],
            'product_type': info['product_type'],
            'user_count': info['user_count'],
            'product_code': info['productcode'],
            'refundable': info['refundable'],
            'rating_score': info['score']
        }

    def _crawl_detail(self, info):
        url = info['url']
        headers = {'user-agent': self.user_agent,
                   'referer': 'https://market.aliyun.com{}'.format(url)}

        product_code = info['product_code']
        product_spec_url = 'https://market.aliyun.com/api/ajax/product/queryProductSpecification.json?' \
                           'productCode={0}&' \
                           'skuCode={0}-prepay&' \
                           'orderType=BUY&' \
                           'chargeType=PREPAY'.format(product_code)
        r = requests.get(product_spec_url, headers=headers)
        parse_result = json.loads(r.text)
        spec = parse_result['result'] if 'result' in parse_result else None
        # csrf_token = spec['_csrf_token']
        price = list(item['text'] for item in spec['components']['package_version'][
            'package_version']) if spec is not None and 'components' in spec and 'package_version' in spec[
            'components'] else []

        api_list_url = 'https://market.aliyun.com/api/ajax/product/queryApiList.json?productCode={}'.format(
            product_code)
        r = requests.get(api_list_url, headers=headers)
        parse_result = json.loads(r.text)
        api_list = parse_result['result'] if 'result' in parse_result else None
        end_point = api_list['endPoint'] if api_list is not None else None
        api_info = api_list['ApiInfo'] if api_list is not None else []

        # pricing_plan_url = 'https://market.aliyun.com/api/ajax/product/queryProductPricingPlan.json?' \
        #                    'productCode={0}&skuCode={0}-prepay'.format(product_code)
        # r = requests.get(pricing_plan_url, headers=headers)
        # pricing_plan = json.loads(r.text)['result']

        page_index = 1
        query_rates_url = 'https://market.aliyun.com/api/ajax/product/queryRates.json?' \
                          'curPage={0}&pageIndex={0}&' \
                          'productCode={1}'.format('{0}', product_code)
        r = requests.get(query_rates_url.format(page_index), headers=headers)
        parse_result = json.loads(r.text)
        query_rates = parse_result['result'] if 'result' in parse_result else None
        total_records = query_rates['totalRecords'] if query_rates is not None else 0
        self.log.info('Total rating records: {}'.format(total_records))
        total_page = query_rates['totalPage'] if query_rates is not None else 0
        comments = query_rates['commens'] if query_rates is not None else []
        while page_index < total_page:
            page_index += 1
            r = requests.get(query_rates_url.format(page_index), headers=headers)
            query_rates = json.loads(r.text)
            query_rates = query_rates['result']
            comments += query_rates['comments']

        api_doc = []
        for api in api_info:
            api_doc_url = 'https://market.aliyun.com/api/ajax/product/queryApiDoc.json?' \
                          'productCode={0}&' \
                          'endPoint={1}&' \
                          'groupId={2}&' \
                          'apiId={3}&' \
                          'stageName={4}'.format(product_code, end_point,
                                                 api['GroupId'], api['ApiId'], api['StageName'])
            r = requests.get(api_doc_url, headers=headers)
            api_doc.append(json.loads(r.text)['result'])

        api = list({**info, **doc} for info, doc in zip(api_info, api_doc))
        return price, api, comments
t