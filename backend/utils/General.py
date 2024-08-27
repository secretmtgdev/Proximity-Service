import configparser
import os
from pathlib import Path
from Constants import Configuration

def getApiKey():
    parser = configparser.RawConfigParser()
    path = Path(os.getcwd())

    # local path did not work, using absolute path from pwd
    yelpPath = f'{path.parent.absolute()}/configs/yelp.ini'

    # pass a raw string to the parser to read from
    parser.read(r'{}'.format(yelpPath))
    details = dict(parser.items(Configuration['SECTIONS']['CLIENT']['name']))
    return details['client.apikey']
