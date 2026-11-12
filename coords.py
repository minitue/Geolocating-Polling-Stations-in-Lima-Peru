import pandas as pd
import requests

with open('data/api_key.txt', 'r') as a:
    api_key = a.read().strip('\n')
url = 'https://places.googleapis.com/v1/places:searchText'
headers = {
    'Content-Type': 'application/json',
    'X-Goog-API-Key': api_key,
    'X-Goog-FieldMask': 'places.formattedAddress,places.location'
}
schools = pd.read_csv('data/polling_locations_tagged.csv').drop(columns = [
    'departamento', 'provincia'])
schools = schools.query("distrito == 'Lurin' | distrito == 'Pachacamac' | distrito == 'San Juan de Miraflores'")
treated = schools[schools['treated'] == 1]
poll_results = pd.read_csv('data/polling_results_by_table.csv')

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
for i, s in schools.iterrows():
    p = search_school(s['local_de_votacion'], s['distrito'])
    if p:
        addr = p.get('formattedAddress', "")
        results.append({
            **s,
            'lat': p['location']['latitude'],
            'lng': p['location']['longitude'],
            'matched_address': addr,
            'ok': s['distrito'].lower() in addr.lower()
        })
    else:
        results.append({
            **s, 'lat': None, 'lng': None, 'matched_address': None, 'ok': False
        })

pd.DataFrame(results).to_csv('data/school_coords.csv', index = False)
