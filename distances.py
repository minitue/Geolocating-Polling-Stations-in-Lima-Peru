import requests
import pandas as pd

coords = pd.read_csv('data/school_coords.csv')
treated = coords[coords['treated'] == 1]
control = coords[coords['treated'] == 0]
poll_results = pd.read_csv('data/polling_results_by_table.csv')
rows = []
print('treated rows:', len(treated))
if treated.shape[0] != 13:
    raise ValueError('lock in.')

with open('data/api_key.env', 'r') as a:
    api_key = a.read().strip('\n')

ROUTES_URL = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
ROUTES_HEADERS = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": api_key,
    "X-Goog-FieldMask": "originIndex,destinationIndex,duration,distanceMeters,status,condition",
}

def wp(lat, lng):
    return {"waypoint": {"location": {"latLng": {"latitude": lat, "longitude": lng}}}}

def drive_matrix(origin, dests):
    """
    origin: tuple that includes school name and coords (treated)
    dests: list of tuples (controls) in the same district as treated schools
    Returns a list of destinations from the origin within time limit
    """
    ocoords = origin[1:]
    out = []
    # time_limit = 27 originally for filtering
    for dest in dests:
        dcoords = dest[1:]
        body = {
            "origins": [wp(*ocoords)],
            "destinations": [wp(*dcoords)],
            "travelMode": "DRIVE",
        }
        r = requests.post(ROUTES_URL, json=body, headers=ROUTES_HEADERS, timeout=60)
        r.raise_for_status() # if request errors
        for el in r.json():
            if el.get("condition") != "ROUTE_EXISTS":
                continue
            # minutes = (float(el["duration"].rstrip("s")) / 60) originally for filtering
            out.append({
                "name" : dest[0],
                "dest_index": el["destinationIndex"],
                "drive_min": float(el["duration"].rstrip("s")) / 60,
                "drive_km": el["distanceMeters"] / 1000,
            })
    return out



for d, tdf in treated.groupby('distrito'):
    cdf = control[control['distrito'] == d]
    dests = list(zip(cdf['local_de_votacion'], cdf['lat'], cdf['lng']))
    print(d, len(tdf), 'treated;', len(cdf), 'controls')
    for t in tdf.itertuples():
        for res in drive_matrix((t.local_de_votacion, t.lat, t.lng), dests):
            rows.append({'stack': t.local_de_votacion, **res})

distances = pd.DataFrame(rows)
distances.to_csv('data/distances.csv', index = False)
