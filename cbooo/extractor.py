from bs4 import BeautifulSoup as soup
import re


def convert_box_office(string):
    try:
        res = re.search('[0-9.]+', string)
        num = float(res.group(0)) if res is not None else 0
    except ValueError:
        return 0
    if '万' in string:
        num *= 10000
    return num


def extract_name(section, pattern):
    name_list = []
    name_idx = 1
    for item in section.find_all('p'):
        link = item.find('a')
        text = link.text.strip().replace('\r', '').replace('\n', '') if link is not None else None
        if text is not None:
            res = pattern.search(text)
            idx = res.start() if res is not None else len(text)
            name_list.append({
                'name': text[:idx].strip(),
                'english': text[idx:],
                'idx': name_idx
            })
            name_idx += 1
    return name_list if len(name_list) > 0 else None


class Extractor:
    def __init__(self):
        self.pattern = {
            'number': re.compile(r'\d+'),
            'onscreen-time': re.compile(r'\d+(-\d+)*'),
            'english-name': re.compile(r'([0-9A-Za-z]+ )*[A-Za-z]+( [A-Za-z]+)*'),
            'header': re.compile(r'\w+'),
            'date': re.compile(r'\d+(-\d+)+')
        }

    def extract_info(self, page):
        s = soup(page, features='lxml')
        info_section = s.find('div', class_='cont')

        title_section = info_section.find('h2').text.split('（')
        title = title_section[0] if len(title_section) > 0 else ''
        year = 0
        if len(title_section) > 1:
            res = self.pattern['number'].search(title_section[1])
            year = int(res.group(0)) if res is not None else 0

        it = info_section.find('p')
        english_title = it.text

        it = it.find_next_sibling('p')
        spans = it.find_all('span')
        box_section = spans[-1] if len(spans) > 0 else None
        text = box_section.text if box_section else ''
        box_office_string = text[4:] if '累计票房' in text else ''
        total_box_office = convert_box_office(box_office_string)

        it = it.find_next_sibling('p')
        movie_type = it.text[3:].split('/')

        it = it.find_next_sibling('p')
        res = self.pattern['number'].search(it.text)
        movie_length = int(res.group(0)) if res is not None else None

        it = it.find_next_sibling('p')
        res = self.pattern['onscreen-time'].search(it.text)
        onscreen_time = res.group(0) if res is not None else None

        it = it.find_next_sibling('p')
        movie_format = it.text[3:].split('/')

        it = it.find_next_sibling('p')
        country = it.text[6:].split('/')

        it = it.find_next_sibling('p')
        link = it.find('a') if it is not None else None
        main_publisher = link.text if link is not None else None

        detail_section = s.find('dl', class_='dltext')
        director_section = detail_section.find('dd')
        director = extract_name(director_section, self.pattern['english-name'])

        cast_section = director_section.find_next_sibling('dd')
        cast = extract_name(cast_section, self.pattern['english-name'])

        producer_section = cast_section.find_next_sibling('dd')
        producer = extract_name(producer_section, self.pattern['english-name'])

        publisher_section = producer_section.find_next_sibling('dd')
        publisher = extract_name(publisher_section, self.pattern['english-name'])

        box_office_section = s.find(id='tabcont2')
        box_office = {}
        for header in box_office_section.find_all('h4'):
            text = header.text
            res = self.pattern['header'].search(text)
            if res is not None:
                header_list = []
                table_title = res.group(0)
                table = header.find_next_sibling('table')
                tr = table.find('tr')
                for th in tr.find_all('th'):
                    if len(th.text) > 0:
                        header_list.append(th.text)
                table_content = []
                for row in table.find_all('tr')[1:]:
                    content = {}
                    time_text = row.find('td')
                    if time_text is not None:
                        content['时间'] = re.sub(r'[\s\r\n]+', '', time_text.text)
                    for idx, th in enumerate(time_text.find_next_siblings('td')):
                        content[header_list[idx]] = int(th.text) if th.text != 'N/A' else 0
                    table_content.append(content)
                box_office[table_title] = table_content

        info = {
            'title': title,
            'year': year,
            'english_title': english_title,
            'total_box_office': total_box_office,
            'type': movie_type,
            'length': movie_length,
            'onscreen_time': onscreen_time,
            'format': movie_format,
            'country': country,
            'main_publisher': main_publisher,
            'director': director,
            'cast': cast,
            'producer': producer,
            'publisher': publisher,
            'box_office': box_office
        }
        return info

    def extract_events(self, page):
        if page == '该影片暂无营销事件':
            return None
        else:
            s = soup(page, features='lxml')
            tab_text = s.find('div', class_='tabText')
            ul = tab_text.find('ul')
            event = []
            for li in ul.find_all('li'):
                day = li.find('em').find('span').text
                event_type = li.find('h5').text

                detail_section = li.find('div', class_='tabTcon')
                if detail_section is not None:
                    title_section = detail_section.find('h4')
                    title = title_section.text if title_section is not None else ''

                    source_section = detail_section.find('var')
                    source_text = source_section.text if source_section is not None else ''
                    res = self.pattern['date'].search(source_text)
                    idx = res.start() if res is not None else len(source_text)
                    source = source_text[:idx].strip().replace('来源：', '')
                    date = source_text[idx:]

                    content_section = detail_section.find('p')
                    detail = content_section.text.replace('阅读全部', '') if content_section is not None else None

                    link_section = content_section.find('a') if content_section is not None else None
                    link = link_section.attrs['href'] if link_section is not None and 'href' in link_section.attrs else None

                    event.append({
                        'day': day,
                        'type': event_type,
                        'title': title,
                        'source': source,
                        'date': date,
                        'detail': detail,
                        'link': link
                    })
            return event if len(event) > 0 else None
