import os
import json
import requests

# The petitions API is totally broken when browsing old governments so we have
# to fix up the URL
governments = {
#    '2010-2015_Conservative_-_Liberal_Democrat_coalition_government': ('https://petition.parliament.uk/archived/petitions.json?state=all', '&parliament=2'),
#    '2015-2017_Conservative_government': ('https://petition.parliament.uk/archived/petitions.json?parliament=1&state=all', '&parliament=1'),
    '2017-_Conservative_government': ('https://petition.parliament.uk/petitions.json?state=all', '')
}

for gov, (url, append) in governments.items():
    print('Processing the %s government....' % gov)
    path = 'petitions/' + gov
    try:
        os.mkdir(path)
    except OSError:
        pass

    while url:
        print('Fetching %s...' % (url + append))
        response = requests.get(url + append)
        data = json.loads(response.content)

        for petition in data['data']:
            with open('%s/%s.json' % (path, petition['id']), 'w') as f:
                print('Dumping %s' % petition['id'])
                f.write(json.dumps(petition, sort_keys=True, indent=4, separators=(',', ': ')))

        url = data['links']['next']
