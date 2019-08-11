import json
import re
import requests

from bs4 import BeautifulSoup as Soup


class IDataAPISpider:

    def crawl_api(self, pages=7):
        url = 'https://www.idataapi.cn/product/get_list'
        params = {
            'page': 1,
            'type': 1,
            'pricetype': 0,
            'status': 0,
            'tid': 0,
            'cid': 0,
            'keyword': '',
            'sort': 1,
            'sort_type': 'desc'
        }
        for page in range(pages):
            params['page'] = page
            r = requests.post(url=url, data=params)
            result = json.loads(r.text)
            yield self._crawl_api_item(result['id'])

    @staticmethod
    def _crawl_api_item(api_id):
        url = 'https://www.idataapi.cn/product/detail/{0}'
        r = requests.get(url.format(api_id))
        soup = Soup(r.text, 'lxml')

        api_item = {}

        # Basic info
        detail_div = soup.find('div', class_='pull-left detail-left')
        user_num_div = detail_div.find('div', class_='pull-left new-tmp')
        span = user_num_div.find('span')
        match = re.search(r'\d+', span.text)
        api_item['使用人数'] = int(match.group(0)) if match is not None else 0

        info_show = detail_div.find('div', class_='info-show')
        h1 = info_show.find('h1')
        api_item['标题'] = re.sub(r'\s+', '', h1.text)

        new_price_show = detail_div.find('div', class_='new-price-show')
        p = new_price_show.find('p', class_='clearfix')

        def __find_description(tag):
            return tag.name == 'span' and tag.has_attr('class') and 'pull-left' in tag.attrs['class'] and tag.has_attr(
                'title')

        span = p.find(__find_description)
        api_item['简介'] = span.text

        down_des_div = new_price_show.find('div', class_='down_des')
        b_list = down_des_div.find_all('b')
        tag_list = []
        if b_list is not None:
            for b in b_list:
                tag_list.append(b.text)
        api_item['标签'] = tag_list

        i = new_price_show.find('i')
        api_item['上架时间'] = i.text

        small_icon = new_price_show.find('div', class_='small_icon clearfix')
        i_list = small_icon.find_all('i')
        type_list = list(i.attrs['title'] for i in i_list) if i_list is not None else None

