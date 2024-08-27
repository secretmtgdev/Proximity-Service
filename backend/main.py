# https://github.com/firebase/firebase-functions-python/issues/92
import sys
from pathlib import Path
sys.path.insert(0, Path(__file__).parent.as_posix())

from utils.General import getApiKey
from utils.FushionAPI import getLocalStores
from Constants import Places

DEFAULT_COORDINATES = (Places['SEATTLE']['lat'], Places['SEATTLE']['long'])

if __name__ == '__main__':
    apiKey = getApiKey()
    getLocalStores(apiKey, DEFAULT_COORDINATES)