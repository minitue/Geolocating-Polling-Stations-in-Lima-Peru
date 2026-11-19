import pandas as pd
import requests
from unidecode import unidecode

with open('data/api_key.env', 'r') as a:
    api_key = a.read().strip('\n')
url = 'https://places.googleapis.com/v1/places:searchText'
headers = {
    'Content-Type': 'application/json',
    'X-Goog-API-Key': api_key,
    'X-Goog-FieldMask': 'places.formattedAddress,places.location'
}

schools = pd.read_csv('data/polling_locations_tagged.csv').drop(columns = [
    'departamento', 'provincia'])
schools = schools[~schools['distrito'].isin(['Lurin', 'Pachacamac', 'San Juan de Miraflores'])]

def norm(t):
    """Accent-stripping so the 'ok' variable won't be misleading"""
    return ' '.join(unidecode(str(t)).lower().replace('-', ' ').split())

def search_school(name, district):
    body = {
        'textQuery': f"{name}, {district}, Lima, Peru", 
        'regionCode': 'PE',
        'pageSize': 1,
        'locationRestriction': {'rectangle': {
            'low': {'latitude': -12.6, 'longitude': -77.3},
            'high': {'latitude': -11.5, 'longitude': -76.5}
        }}
    }
    r = requests.post(url, json = body, headers= headers, timeout = 30)
    r.raise_for_status()
    places = r.json().get('places', [])
    return places[0] if places else None

results = []
for n, (i, s) in enumerate(schools.iterrows(), start = 1):
    p = search_school(s['local_de_votacion'], s['distrito'])
    if p:
        addr = p.get('formattedAddress', "")
        results.append({
            **s,
            'lat': p['location']['latitude'],
            'lng': p['location']['longitude'],
            'matched_address': addr,
            'ok': norm(s['distrito']) in norm(addr)
        })
    else:
        results.append({
            **s, 'lat': None, 'lng': None, 'matched_address': None, 'ok': False
        })
    if n % 25 == 0:
        print(f"{n} of {len(schools)} done")
    if n % 100 == 0:
        pd.DataFrame(results).to_csv('data/rest_school_coords.csv', index=False)
        print(n, 'done')

pd.DataFrame(results).to_csv('data/rest_school_coords.csv', index = False)
