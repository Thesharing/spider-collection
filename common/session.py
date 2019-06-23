import random
import requests
from .error import NetworkException

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.81 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3497.81 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3497.81 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3497.81 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3497.81 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3497.81 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3497.81 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:62.0) Gecko/20100101 Firefox/62.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko'
]


class Session:

    def __init__(self):
        self.PROXY = False
        self.TIMEOUT = 20
        self.session = requests.session()

    @property
    def user_agent(self):
        return USER_AGENTS[random.randrange(0, len(USER_AGENTS))]

    def post(self, **kwargs):
        try:
            r = self.session.post(timeout=self.TIMEOUT, **kwargs)
            if r.status_code == 200:
                if len(r.text) > 0:
                    return r
                else:
                    raise NetworkException('Null value')
            else:
                raise NetworkException('Error Code: {}'.format(r.status_code))
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            raise NetworkException(str(e))

    def get(self, **kwargs):
        try:
            r = self.session.get(timeout=self.TIMEOUT, **kwargs)
            if r.status_code == 200:
                if len(r.text) > 0:
                    return r
                else:
                    raise NetworkException('Null page')
            else:
                raise NetworkException('Error Code: {}'.format(r.status_code))
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            raise NetworkException(str(e))
