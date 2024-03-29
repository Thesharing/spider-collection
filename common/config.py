import os
import json
import logging
from .util import encode_json


class Nested:
    def __init__(self, structure):
        self.dict = structure

    def __new__(cls, structure):
        self = super(Nested, cls).__new__(cls)
        self.dict = structure
        if type(structure) is dict:
            self.__dict__ = {key: Nested(structure[key]) for key in structure}
        elif type(structure) is list:
            self = [Nested(item) for item in structure]
        else:
            self = structure
        return self

    def __str__(self):
        return str(self.dict)


Config = Nested({
    'spider': {
        'start_page': 1
    },
    'config': {
        'max_retry': 10,
        'proxy': True,
        'timeout': 60
    },
    'database': {
        'redis': {
            'host': 'localhost',
            'port': 6379
        },
        'mongodb': {
            'host': 'localhost',
            'port': 27017,
            'database': 'spider'
        }
    },
    'log': {
        'level': 'INFO'  # CRITICAL - 50, ERROR - 40, WARNING - 30, INFO - 20, DEBUG - 10, NOTSET - 9
    }
})


def read_config(file_name: str = 'config.json'):
    if os.path.isfile(file_name):
        with open(file_name, 'r', encoding='utf-8') as f:
            data = json.load(f)

            data['name'] = file_name

            # start_date = data['start']['date']
            # if start_date is not None:
            #     data['start']['date'] = parser.parse(start_date)

            log_level = data['log']['level']
            if log_level is not None:
                data['log']['level'] = getattr(logging, log_level)

            global Config
            Config = Nested(data)
    else:
        with open(file_name, 'w', encoding='utf-8') as f:
            # Config.dict['log']['level'] = logging.getLevelName(Config.dict['log']['level'])
            json.dump(Config.dict, f, default=encode_json, ensure_ascii=False, indent=2)


read_config()
