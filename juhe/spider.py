import json
import re

from bs4 import BeautifulSoup as Soup

from spiderutil.network import Session


class JuheSpider:

    def __init__(self):
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
        self.session = Session(retry=10, timeout=20)

    def crawl_api(self, total_page=6, start_from=None):
        url = 'https://www.juhe.cn/docs/index/page/{0}'
        start = start_from is None
        for page in range(total_page + 1):
            r = self.session.get(url.format(page))
            s = Soup(r.text, 'lxml')
            ul = s.find('ul', class_='api-list-ul')
            for li in ul.find_all('li', class_='api-list-li'):
                a = li.find('a')
                link = a['href']
                if not start:
                    if link == start_from:
                        start = True
                    continue
                # h2 = a.find('h2', class_='api-name')
                # title = h2.text
                # div = li.find('div', class_='api-price')
                # price = div.text if div is not None else None
                # p = li.find('p', class_='api-marks')
                # desc = p.text if p is not None else None
                yield link, self._crawl_api_item(link)

    def _crawl_api_item(self, link):

        url = 'https://www.juhe.cn{0}'.format(link)
        num = link.split('/')[-1]
        r = self.session.get(url)
        s = Soup(r.text, 'lxml')
        ul = s.find('ul', class_='api-pp')
        temp = []
        for li in ul.find_all('li'):
            div = li.find('div')
            temp.append(div.text)
        api_item = {
            'ID': temp[0],
            'API请求次数': temp[1],
            '收藏量': temp[2]
        }

        api_infos = s.find('div', class_='api-infos')
        h1 = api_infos.find('h1')
        api_item['标题'] = h1.text if h1 is not None else None
        tags = api_infos.find_all('span')
        api_item['标签列表'] = list(span.text for span in tags) if tags is not None else None

        api_des_info = api_infos.find('p', class_='api-des-info')
        desc = api_des_info.text
        api_item['简介'] = desc
        product_content = s.find('div', class_='product-content')
        if product_content is not None:
            product_aways = product_content.find('div', class_='product-aways')
            api_item['功能介绍'] = product_aways.text

        api_url_list = []
        doc_api_area = s.find('div', id='docs-api-area')
        ul = doc_api_area.find('ul')
        li_list = ul.find_all('li')
        for li in li_list:
            a = li.find('a')
            api_title = a.text
            api_url = a['href']
            api_url_list.append({'title': api_title, 'url': api_url + '/' + num})

        price_url = 'https://www.juhe.cn/docs/api/packages/{0}'.format(num)
        r = self.session.get(price_url)
        result = json.loads(r.text)
        html = result['result']['html']
        s = Soup(html, 'lxml')
        ul = s.find('ul')
        li_list = ul.find_all('li')
        prices = []
        for li in li_list:
            price = li['data-price'] if 'data-price' in li.attrs else None
            tag = re.sub(r'\s+', '', li.text)
            if price is not None or tag is not None:
                prices.append({'price': price, 'tag': tag})
        api_item['价格'] = prices

        api_list = []
        for api_url in api_url_list:
            api = {
                'title': api_url['title']
            }
            api_url = 'https://www.juhe.cn{0}'.format(api_url['url'])
            r = self.session.get(api_url)
            result = json.loads(r.text)['result']
            s = Soup(result['html'], 'lxml')
            div_list = s.find_all('div', class_='simpleline')
            for i in range(len(div_list) - 1):
                div = div_list[i]
                tag_and_content = div.text.split('：', 1)
                if len(tag_and_content) > 1:
                    api[tag_and_content[0]] = tag_and_content[1].strip().strip('\n')

            idx = 0
            div_list = s.find_all('div', class_='simpleTable')

            div = div_list[idx]
            p = div.find('p')
            tag = p.text.strip('：')
            if tag == '请求参数说明':
                params = []
                table = div.find('table')
                tr_list = table.find_all('tr')
                header_tr = tr_list[0]
                headers = []
                for th in header_tr.find_all('th')[1:]:
                    headers.append(th.text)
                for tr in tr_list[1:]:
                    param = {}
                    for index, td in enumerate(tr.find_all('td')[1:]):
                        param[headers[index]] = td.text
                    params.append(param)
                api[tag] = params

                idx = min(idx + 1, len(div_list) - 1)

            codes = []
            div = div_list[idx]
            p = div.find('p')
            tag = p.text.strip('：')

            if tag == '请求代码示例':
                for code in div.find_all('code'):
                    language = code['class'][0]
                    content = code.text
                    codes.append({'language': language, 'code': content})
                api[tag] = codes

                idx = min(idx + 1, len(div_list) - 1)

            return_param = []
            div = div_list[idx]
            p = div.find('p')
            tag = p.text.strip('：')
            if tag == '返回参数说明':
                table = div.find('table')
                tr_list = table.find_all('tr')
                header_tr = tr_list[0]
                headers = []
                for th in header_tr.find_all('th')[1:]:
                    headers.append(th.text)
                for tr in tr_list[1:]:
                    param = {}
                    for index, td in enumerate(tr.find_all('td')[1:]):
                        param[headers[index]] = td.text
                    return_param.append(param)
                api[tag] = return_param

                idx = min(idx + 1, len(div_list) - 1)

            div = div_list[idx]
            p = div.find('p')
            tag = p.text.strip('：')
            if tag == 'JSON返回示例':
                return_example = div.find('code').text
                api[tag] = return_example

            api_list.append(api)
        api_item['API'] = api_list

        error_code_url = 'https://www.juhe.cn/docs/api/errorCode/{}'.format(num)
        r = self.session.get(error_code_url)
        result = json.loads(r.text)
        api_item['错误码'] = result['result'] if 'result' in result else None

        return api_item

    def crawl_data(self, start_from=None):
        url = 'https://www.juhe.cn/market'
        start = start_from is None
        r = self.session.get(url)
        s = Soup(r.text, 'lxml')
        ul = s.find('ul', class_='api-list-ul')
        for li in ul.find_all('li', class_='api-list-li'):
            a = li.find('a')
            link = a['href']
            if not start:
                if link == start_from:
                    start = True
                continue
            # h2 = a.find('h2', class_='api-name')
            # title = h2.text
            yield link, self._crawl_data_item(link)

    def _crawl_data_item(self, link):
        r = self.session.get(link)
        s = Soup(r.text, 'lxml')
        block_main_info = s.find('div', class_='block-main-info')

        data_item = {'标题': block_main_info.find('h1').text,
                     '简介': block_main_info.find('p', class_='block-main-desc').text}

        block_main_detail = block_main_info.find('div', class_='block-main-detail')
        dl_list = block_main_detail.find_all('dl')
        for dl in dl_list:
            dt = dl.find('dt')
            dd = dl.find('dd')
            data_item[dt.text] = dd.text

        ul = s.find('ul', class_='block-main-list')
        temp = []
        for li in ul.find_all('li'):
            span = li.find('span')
            temp.append(span.text)
        data_item.update({
            'ID': temp[0],
            '下载次数': temp[1],
            '收藏量': temp[2]
        })

        table = s.find('table', class_='block-table')
        tr_list = table.find_all('tr')
        header_tr = tr_list[0]
        headers = []
        for td in header_tr.find_all('td')[1:]:
            headers.append(td.text)
        data_list = []
        for tr in tr_list[1:]:
            data = {}
            for idx, td in enumerate(tr.find_all('td')[1:]):
                data[headers[idx]] = td.text
            data_list.append(data)
        data_item['数据列表'] = data_list
        return data_item
