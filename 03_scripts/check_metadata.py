import urllib.request,json
u='https://data.lacity.org/api/views/d5tf-ez2w.json';d=json.load(urllib.request.urlopen(u));print(d.get('description'));print(d.get('rowsUpdatedAt'));print(json.load(open('01_data/raw/city_boundary.json'))['features'][0]['properties']);print(open('01_data/raw/acs2021_population.json').read()[:250])
