import requests
from Constants import Fushion
from Types import Coordinates

def getLocalStores(apiKey: str, coordinates: Coordinates[float]):
    # perform a basic search via python
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {apiKey}'
    }

    lat, long = coordinates
    query = f'?latitude={lat}&longitude={long}&categories=tabletopgames'
    url = Fushion['FUSHION_BASE_URL'] + Fushion['FUSHION_ENDPOINTS']['search'] + query
    
    response = requests.get(url, headers=headers)
    response = response.json()
    for business in response['businesses']:
        print(business['name'])
