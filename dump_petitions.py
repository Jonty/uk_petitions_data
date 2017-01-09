import json
import requests

url = 'https://petition.parliament.uk/petitions.json?state=all'
while url:
    print('Fetching %s...' % url)
    response = requests.get(url)
    data = json.loads(response.content)

    for petition in data['data']:
        with open('petitions/%s.json' % petition['id'], 'w') as f:
            print('Dumping %s' % petition['id'])
            f.write(json.dumps(petition, sort_keys=True, indent=4, separators=(',', ': ')))

    url = data['links']['next']
