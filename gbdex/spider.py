import json
import requests
import re

from bs4 import BeautifulSoup as Soup
from requests.exceptions import Timeout
from tqdm import tqdm

from spiderutil.network import Session


class GBDEXSpider:

    def __init__(self):
        self.session = Session(timeout=10)

    def crawl_api(self):
        param = {
            'parentIndustryId': '',
            'industryId': '',
            'cityId': '',
            'areaId': '',
            'dataType': 0,
            'sort': 'updateTime',
            'order': 'desc',
            'keyword': '',
            'page': 1,
            'limit': 1000
        }
        url = 'http://trade.gbdex.com/trade.web/accurateData/filterDataByAjax'
        r = self.session.post(url, params=param)
        json_data = json.loads(r.text)
        link_list = json_data['rows'] if 'rows' in json_data else list()
        print('GDBEX - API: {0} items total in list'.format(len(link_list)))
        tqdm_list = tqdm(link_list)
        for link in tqdm_list:
            tqdm_list.set_description('Crawling: {}'.format(link['id']))
            try:
                yield self._crawl_api_item(link['id'])
            except Timeout:
                continue

    def _crawl_api_item(self, product_id):
        url = 'http://trade.gbdex.com/trade.web/api/apishow'
        param = {'productID': product_id}
        r = self.session.get(url, params=param)
        s = Soup(r.text, 'lxml')
        api = dict()
        api['标题'], api['简介'], api['价格'], api['数据类型'], api['覆盖区域'], api['点击量'], api[
            '收藏量'] = self._parse_brief(s)
        api['API'] = self._parse_list(s)
        api['代码示例'] = self._parse_code_demo(s)
        api['id'] = product_id
        return api

    @staticmethod
    def _parse_brief(s):
        detail_info_r = s.find('div', class_='detailInfo-R')
        datum_title = detail_info_r.find('h3', class_='datumTitle')
        title = datum_title.text if datum_title is not None else None
        data_content_hidden = detail_info_r.find('p', id='dataContentHidden')
        brief = data_content_hidden.text if data_content_hidden is not None else None
        product_price = detail_info_r.find('span', id='productPrice')
        price = re.sub(r'\s+', '', product_price.text) if product_price is not None else None
        product_profile = detail_info_r.find('ul', class_='product-profile clearfix')
        if product_profile is not None:
            li_list = product_profile.find_all('li')
            data_type = li_list[1].text.split('：')[1]
            area = li_list[2].text.split('：')[1]
        else:
            combo_set = detail_info_r.find('div', class_='combo-set comboLeft')
            p_list = combo_set.find_all('p')
            data_type = p_list[0].text.split('：')[1]
            area = p_list[2].text.split('：')[1]
        detail_info_l = s.find('div', class_='detailInfo-l')
        target = detail_info_l.find('div', class_='target')
        span_list = target.find_all('span')
        click_count = int(re.sub(r'\s+', '', span_list[0].text))
        fav_count = int(re.sub(r'\s+', '', span_list[2].text))

        return title, brief, price, data_type, area, click_count, fav_count

    @staticmethod
    def _parse_list(s):
        api_title = []
        div = s.find('div', id='definite0')
        section = div.find('section', class_='clearfix base-boder')
        base_info = section.find('div', class_='baseInfo')
        ul = base_info.find(id='navUl')
        for li in ul.find_all('li'):
            api_title.append(li['title'])

        api_list = []

        for idx, page in enumerate(s.find_all('div', class_='baseContent fl')):
            api = {}
            table_list = page.find_all('table')
            if len(table_list) <= 0:
                continue
            table = table_list[0]
            tr_list = table.find_all('tr')
            l = []
            for tr in tr_list:
                td = tr.find_all('td')[1]
                l.append(re.sub(r'\s+', '', td.text))
            api['接口地址'], api['请求类型'], api['返回数据格式'], \
            api['数据总量'], api['是否收费'] = l[0], l[1], l[2], l[3], l[4]
            table = table_list[1]
            t_body = table.find('tbody')
            tr_list = t_body.find_all('tr')
            api['输入字段'] = []
            for tr in tr_list:
                td_list = tr.find_all('td')
                input_data = {'描述': td_list[0].text, '参数名称': td_list[1].text, '数据类型': td_list[2].text,
                              '默认值': td_list[3].text, '是否必填': td_list[4].text}
                api['输入字段'].append(input_data)

            table = table_list[2]
            t_body = table.find('tbody')
            tr_list = t_body.find_all('tr')
            api['返回字段'] = []
            for tr in tr_list:
                td_list = tr.find_all('td')
                return_data = {'描述': td_list[0].text, '参数名称': td_list[1].text, '数据类型': td_list[2].text,
                               '默认值': td_list[3].text, '是否必填': td_list[4].text}
                api['返回字段'].append(return_data)

            api['API名称'] = api_title[idx]
            api_list.append(api)

        return api_list

    @staticmethod
    def _parse_code_demo(s):
        code_demo = {}
        div = s.find('div', id='definite2')
        ul = div.find('ul', id='tab-dm')
        if ul is None:
            return None
        li_list = ul.find_all('li')
        if li_list is None:
            return None
        code_type_list = list(li.text for li in li_list)
        sample_div = div.find('div', class_='definiteContent sample')
        if sample_div is None:
            return None
        code_span_list = sample_div.find_all('span')
        if code_span_list is None:
            return None
        if len(code_type_list) != len(code_span_list):
            print('Count of type ({0}) is not eqaul to count of code span ({1})'.format(len(code_type_list),
                                                                                        len(code_span_list)))
        for idx, code in enumerate(code_span_list):
            code_demo[code_type_list[idx]] = code.text
        return code_demo

    def crawl_data_file(self):
        param = {
            'parentIndustryId': '',
            'industryId': '',
            'cityId': '',
            'areaId': '',
            'dataType': 1,
            'sort': 'updateTime',
            'order': 'desc',
            'keyword': '',
            'page': 1,
            'limit': 3000
        }
        url = 'http://trade.gbdex.com/trade.web/accurateData/filterDataByAjax'
        r = requests.post(url, params=param, timeout=10)
        json_data = json.loads(r.text)
        link_list = json_data['rows'] if 'rows' in json_data else list()
        print('GDBEX - Data File: {0} items total in list'.format(len(link_list)))
        tqdm_list = tqdm(link_list)
        for link in tqdm_list:
            tqdm_list.set_description('Crawling: {}'.format(link['id']))
            try:
                yield self._crawl_data_file_item(link['id'])
            except Timeout:
                continue

    def _crawl_data_file_item(self, product_id):
        url = 'http://trade.gbdex.com/trade.web/dataReport/reportPayForProduct'
        param = {'productID': product_id}
        r = requests.get(url, params=param, timeout=10)
        s = Soup(r.text, 'lxml')
        item = dict()
        item['标题'], item['简介'], item['价格'], item['数据类型'], item['覆盖区域'], item['点击量'], item[
            '收藏量'] = self._parse_brief(s)
        item['详细信息'] = self._parse_file_info(s)
        item['ID'] = product_id
        return item

    @staticmethod
    def _parse_file_info(s):
        table = s.find('table')
        info = {}
        for tr in table.find_all('tr'):
            td_list = tr.find_all('td')
            info[td_list[0].text] = re.sub(r'\s+', '', td_list[1].text)
        return info
