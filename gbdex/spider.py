import requests
import json
from bs4 import BeautifulSoup as soup
import re
from tqdm import tqdm
from requests.exceptions import Timeout


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
    click_count = re.sub(r'\s+', '', span_list[0].text)
    fav_count = re.sub(r'\s+', '', span_list[1].text)

    return title, brief, price, data_type, area, click_count, fav_count


def _parse_list(s):
    api_title = []
    section = s.find('section', class_='clearfix base-boder')
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
        api['address'], api['request_type'], api['res_type'], \
        api['data_amount'], api['pay'] = l[0], l[1], l[2], l[3], l[4]
        table = table_list[1]
        t_body = table.find('tbody')
        tr_list = t_body.find_all('tr')
        api['input'] = []
        for tr in tr_list:
            input_data = {}
            td_list = tr.find_all('td')
            input_data['desc'], input_data['name'], input_data['type'] = td_list[0].text, td_list[1].text, td_list[
                2].text
            input_data['default'], input_data['required'] = td_list[3].text, td_list[4].text
            api['input'].append(input_data)

        table = table_list[2]
        t_body = table.find('tbody')
        tr_list = t_body.find_all('tr')
        api['return'] = []
        for tr in tr_list:
            return_data = {}
            td_list = tr.find_all('td')
            return_data['desc'], return_data['name'], return_data['type'] = td_list[0].text, td_list[1].text, td_list[
                2].text
            return_data['default'], return_data['required'] = td_list[3].text, td_list[4].text
            api['return'].append(return_data)

        api['title'] = api_title[idx]
        api_list.append(api)

    return api_list


def _crawl_api_item(product_id):
    url = 'http://trade.gbdex.com/trade.web/api/apishow'
    param = {
        'productID': product_id
    }
    r = requests.get(url, params=param, timeout=10)
    s = soup(r.text, 'lxml')
    api = dict()
    api['title'], api['brief'], api['price'], api['data_type'], api['area'], api['click_count'], api[
        'fav_count'] = _parse_brief(s)
    api['list'] = _parse_list(s)
    api['id'] = product_id
    return api


def crawl_api():
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
    r = requests.post(url, params=param, timeout=10)
    json_data = json.loads(r.text)
    link_list = json_data['rows'] if 'rows' in json_data else list()
    print('GDBEX - API: {0} items total in list'.format(len(link_list)))
    tqdm_list = tqdm(link_list)
    for link in tqdm_list:
        tqdm_list.set_description('Crawling: {}'.format(link['id']))
        try:
            yield _crawl_api_item(link['id'])
        except Timeout:
            continue


def _parse_file_info(s):
    table = s.find('table')
    info = {}
    for tr in table.find_all('tr'):
        td_list = tr.find_all('td')
        info[td_list[0].text] = re.sub(r'\s+', '', td_list[1].text)
    return info


def _crawl_data_file_item(product_id):
    url = 'http://trade.gbdex.com/trade.web/dataReport/reportPayForProduct'
    param = {
        'productID': product_id
    }
    r = requests.get(url, params=param, timeout=10)
    s = soup(r.text, 'lxml')
    item = dict()
    item['title'], item['brief'], item['price'], item['data_type'], item['area'], item['click_count'], item[
        'fav_count'] = _parse_brief(s)
    item['info'] = _parse_file_info(s)
    item['id'] = product_id
    return item


def crawl_data_file():
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
            yield _crawl_data_file_item(link['id'])
        except Timeout:
            continue
