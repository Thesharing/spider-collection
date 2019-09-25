from bs4 import BeautifulSoup as Soup
import urllib.parse as urlparse
import re

from spiderutil.network import Session
from spiderutil.log import Log


class IMDBSpider:

    def __init__(self):
        self.base_url = 'https://www.imdb.com/'
        self.session = Session(retry=5)
        self.pattern = {
            'title_and_year': re.compile(r'(.+?)\s+\(([0-9]+)\)'),
            'number': re.compile(r'[\d,]+'),
            'space': re.compile(r'\s+')
        }
        self.log = Log.create_logger('IMDBSpider', './imdb.log')

    def __url(self, url):
        return urlparse.urljoin(self.base_url, url)

    def __text(self, text, repl=' '):
        return self.pattern['space'].sub(repl, text).strip()

    @staticmethod
    def __str2int(string: str):
        return int(string.replace(',', ''))

    @staticmethod
    def __percent2float(string: str):
        return float(string.strip('%')) / 100

    def top250(self, start_from=None):
        r = self.session.get(urlparse.urljoin(self.base_url, 'chart/top?ref_=nv_mv_250'))
        s = Soup(r.text, 'lxml')
        table = s.find('table')
        tbody = table.find('tbody')
        tr_list = tbody.find_all('tr')
        start = start_from is None
        for tr in tr_list:
            title_col = tr.find('td', class_='titleColumn')
            a = title_col.find('a')
            title = a.text
            link = a.attrs['href']
            if not start:
                if link == start_from:
                    start = True
            if start:
                yield title, link

    def crawl(self, link):
        title, year, rating, num_rating, short_summary, metascore, review_user, review_critic, num_awards, num_video, num_image, story_line, tag_line, mpaa, genre, details, num_review = self._main(
            link)
        summary, synopsis = self._plot(link)
        keywords = self._keyword(link)
        awards = self._awards(link)
        casts = self._cast(link)
        spec = self._tech_spec(link)
        trivia = self._trivia(link)
        quotes = self._quotes(link)
        goofs = self._goofs(link)
        connections = self._connections(link)
        faq = self._faq(link)
        rating_detail = self._user_rating(link)
        companies = self._company_credits(link)
        return {key: value for key, value in locals().items() if key[0] != '_' and key != 'self'}

    def _main(self, link):
        r = self.session.get(self.__url(link))
        s = Soup(r.text, 'lxml')

        # Title and year
        title_wrapper = s.find('div', class_='title_wrapper')
        h1 = title_wrapper.find('h1')
        title_and_year = h1.text
        res = self.pattern['title_and_year'].findall(title_and_year)
        title = res[0][0]
        year = self.__str2int(res[0][1])

        # ratings
        rating_wrapper = s.find('div', class_='ratings_wrapper')
        rating_value = rating_wrapper.find('div', class_='ratingValue')
        strong = rating_value.find('strong')
        span = strong.find('span')
        rating = float(self.__text(span.text))
        a = rating_value.find_next('a')
        num_rating = self.__str2int(self.__text(a.text))

        # Short summary
        plot_summary_wrapper = s.find('div', class_='plot_summary_wrapper')
        summary_text = plot_summary_wrapper.find('div', class_='summary_text')
        short_summary = summary_text.text.strip() if summary_text else None

        # metascore
        title_review_bar = plot_summary_wrapper.find('div', class_='titleReviewBar')
        if title_review_bar is not None:
            metascore_div = title_review_bar.find('div', class_='metacriticScore')
            if metascore_div is not None:
                span = metascore_div.find('span')
                metascore = self.__str2int(span.text)
            else:
                metascore = None
        else:
            metascore = None

        # num of review user and critic
        if title_review_bar is not None:
            reviews_div = title_review_bar.find('div', class_='titleReviewBarItem titleReviewbarItemBorder')
            a_list = reviews_div.find_all('a')
            review_user, review_critic = [self.__str2int(self.pattern['number'].search(a.text).group()) for a in a_list]
        else:
            review_user, review_critic = None, None

        # num of awards
        title_awards_ranks = s.find('div', id='titleAwardsRanks')
        num_awards = []
        strong = title_awards_ranks.find('strong')
        if strong is not None:
            num_awards.append(strong.text.strip())
        span_list = title_awards_ranks.find_all('span', class_='awards-blurb')
        for span in span_list:
            num_awards.append(self.__text(span.text, ' '))

        # num of videos
        title_video_strip = s.find('div', id='titleVideoStrip')
        if title_video_strip is not None:
            see_more = title_video_strip.find('div', class_='combined-see-more see-more')
            a = see_more.find('a')
            num_video = int(self.pattern['number'].search(a.text).group())
        else:
            num_video = 0

        # num of images
        title_image_strip = s.find('div', id='titleImageStrip')
        if title_image_strip is not None:
            see_more = title_image_strip.find('div', class_='combined-see-more see-more')
            if see_more is not None:
                a = see_more.find_all('a')[1]
                num_image = int(self.pattern['number'].search(a.text).group())
            else:
                num_image = 0
        else:
            num_image = 0

        # short story line
        title_story_line = s.find('div', id='titleStoryLine')
        div = title_story_line.find('div', class_='inline canwrap')
        span = div.find('span')
        story_line = span.text.strip()

        # tagline and mpaa
        txt_block_list = title_story_line.find_all('div', class_='txt-block')
        tag_line_div = txt_block_list[0]
        tag_line = self.__text(tag_line_div.contents[2])
        mpaa_div = txt_block_list[1]
        span = mpaa_div.find('span')
        mpaa = self.__text(span.text, ' ')

        # genre
        see_more_list = title_story_line.find_all('div', class_='see-more inline canwrap')
        genre_div = see_more_list[1]
        genre = list(self.__text(a.text, '') for a in genre_div.find_all('a'))

        # details
        title_details = s.find('div', id='titleDetails')
        details = {}
        for txt_block in title_details.find_all('div', class_='txt-block'):
            h4 = txt_block.find('h4', class_='inline')
            if h4 is not None:
                text = self.__text(txt_block.text)
                if text.find('See more') > 0:
                    text = text[text.find(':') + 1: text.find('See more')].strip()
                else:
                    text = text[text.find(':') + 1:].strip()
                details[self.__text(h4.text)] = text

        title_user_review = s.find('div', id='titleUserReviewsTeaser')
        div = title_user_review.find('div', class_='yn')
        num_review = self.__str2int(self.pattern['number'].search(
            div.find_next('a').find_next('a').find_next('a').text).group())

        return title, year, rating, num_rating, short_summary, metascore, review_user, review_critic, num_awards, num_video, num_image, story_line, tag_line, mpaa, genre, details, num_review

    def _plot(self, link):
        r = self.session.get(urlparse.urljoin(self.__url(link), 'plotsummary'))
        s = Soup(r.text, 'lxml')

        # summary
        h4 = s.find('h4', id='summaries')
        ul = h4.find_next('ul')
        summary = [li.find('p').text for li in ul.find_all('li')]

        # synopsis
        h4 = s.find('h4', id='synopsis')
        ul = h4.find_next('ul')
        synopsis = [li.text for li in ul.find_all('li')]

        return summary, synopsis

    def _keyword(self, link):
        r = self.session.get(urlparse.urljoin(self.__url(link), 'keywords'))
        s = Soup(r.text, 'lxml')
        div = s.find('div', id='keywords_content')
        table = div.find('table')
        tbody = table.find('tbody')
        keywords = []
        for td in tbody.find_all('td'):
            if td is not None:
                a = td.find('a')
                if a is not None:
                    keywords.append(a.text)
        return keywords

    def _awards(self, link):
        r = self.session.get(urlparse.urljoin(self.__url(link), 'awards'))
        s = Soup(r.text, 'lxml')
        main = s.find('div', id='main')
        awards = []
        for h3 in main.find_all('h3')[1:]:
            title = self.__text(h3.next)
            year = self.__text(h3.find('a').text)
            awards.append({
                'title': title,
                'year': year
            })
        return awards

    def _cast(self, link):
        r = self.session.get(urlparse.urljoin(self.__url(link), 'fullcredits'))
        s = Soup(r.text, 'lxml')
        div = s.find('div', id='fullcredits_content')
        casts = {}
        for h4 in div.find_all('h4'):
            category = self.__text(h4.text)
            table = h4.find_next('table')
            cast_list = []
            if 'class' in table.attrs and 'cast_list' in table.attrs['class']:
                for tr in table.find_all('tr'):
                    if 'class' in tr.attrs:
                        a = tr.find_next('td').find_next('td').find('a')
                        name = self.__text(a.text)
                        td = tr.find('td', class_='character')
                        credit = self.__text(td.text)
                        cast_list.append({
                            'name': name,
                            'credit': credit
                        })
            else:
                tbody = table.find('tbody')
                for tr in tbody.find_all('tr'):
                    td = tr.find('td', class_='name')
                    name = self.__text(td.text) if td is not None else None
                    td = tr.find('td', class_='credit')
                    credit = self.__text(td.text) if td is not None else None
                    cast_list.append({
                        'name': name,
                        'credit': credit
                    })
            casts[category] = cast_list
        return casts

    def _tech_spec(self, link):
        r = self.session.get(urlparse.urljoin(self.__url(link), 'technical'))
        s = Soup(r.text, 'lxml')
        div = s.find('div', id='technical_content')
        table = div.find('table')
        tbody = table.find('tbody')
        spec = {}
        for tr in tbody.find_all('tr'):
            td = tr.find('td')
            label = self.__text(td.text)
            td = td.find_next('td')
            value = self.__text(td.text)
            spec[label] = value
        return spec

    def _trivia(self, link):
        r = self.session.get(urlparse.urljoin(self.__url(link), 'trivia'))
        s = Soup(r.text, 'lxml')
        div = s.find('div', id='trivia_content')
        trivia = []
        for text_list in div.find_all('div', class_='list'):
            for soda_text in text_list.find_all('div', class_='sodatext'):
                trivia.append(self.__text(soda_text.text))
        return trivia

    def _quotes(self, link):
        r = self.session.get(urlparse.urljoin(self.__url(link), 'quotes'))
        s = Soup(r.text, 'lxml')
        quote = []
        div = s.find('div', id='quotes_content')
        for quote_list in div.find_all('div', class_='list'):
            for soda_text in quote_list.find_all('div', class_='sodatext'):
                quote.append(self.__text(soda_text.text))
        return quote

    def _goofs(self, link):
        r = self.session.get(urlparse.urljoin(self.__url(link), 'goofs'))
        s = Soup(r.text, 'lxml')
        goofs = []
        div = s.find('div', id='goofs_content')
        for soda_text in div.find_all('div', class_='sodatext'):
            goofs.append(self.__text(soda_text.text))
        return goofs

    def _connections(self, link):
        r = self.session.get(urlparse.urljoin(self.__url(link), 'movieconnections'))
        s = Soup(r.text, 'lxml')
        div = s.find('div', id='connections_content')
        connections = {}
        category = None
        for soda_list in div.find_all('div', class_='list'):
            if 'id' in soda_list.attrs and soda_list.attrs['id'] == 'no_content':
                return None
            for soda in soda_list.find_all('div', class_='soda'):
                last = soda.find_previous()
                if last.name == 'h4':
                    category = self.__text(last.text)
                    if category not in connections:
                        connections[category] = []
                connections[category].append(self.__text(soda.text))
        return connections

    def _faq(self, link):
        r = self.session.get(urlparse.urljoin(self.__url(link), 'faq'))
        s = Soup(r.text, 'lxml')
        div = s.find('div', id='main')
        faq = []
        IDs = ['faq-no-spoilers', 'faq-spoilers']
        for ID in IDs:
            section = div.find('section', id=ID)
            ul = section.find('ul')
            for li in ul.find_all('li'):
                question_div = li.find('div', class_='faq-question-text')
                if question_div is None:
                    continue
                question = self.__text(question_div.text)
                answer_div = li.find('div', class_='ipl-hideable-container')
                if answer_div is None:
                    continue
                p = answer_div.find('p')
                answer = self.__text(p.text)
                faq.append({
                    'question': question,
                    'answer': answer
                })
        return faq

    def _user_rating(self, link):
        r = self.session.get(urlparse.urljoin(self.__url(link), 'ratings'))
        s = Soup(r.text, 'lxml')
        div = s.find('div', id='main')
        table = div.find('table')
        rating = {str(i): {} for i in range(1, 11)}
        for idx, div in enumerate(table.find_all('div', class_='topAligned')):
            rating[str(10 - idx)]['percent'] = self.__percent2float(self.__text(div.text))
        for idx, div in enumerate(table.find_all('div', class_='leftAligned')[1:]):
            rating[str(10 - idx)]['count'] = self.__str2int(self.__text(div.text))
        return rating

    def _company_credits(self, link):
        r = self.session.get(urlparse.urljoin(self.__url(link), 'companycredits'))
        s = Soup(r.text, 'lxml')
        div = s.find('div', id='company_credits_content')
        companies = {}
        for h4 in div.find_all('h4', class_='dataHeaderWithBorder'):
            category = self.__text(h4.text)
            credit = []
            for li in h4.find_next('ul').find_all('li'):
                credit.append(self.__text(li.text))
            companies[category] = credit
        return companies
