import os
import json

import lxml.html
from dateutil.parser import parse

government = '2007-2010_Labour_government'
file_path = 'petitions/' + government
try:
    os.mkdir(file_path)
except OSError:
    pass

base_url = 'http://webarchive.nationalarchives.gov.uk'
lists = [
    '/20100810135728/http://petitions.number10.gov.uk/list/closed?sort=signers',
    '/20100810135738/http://petitions.number10.gov.uk/list/rejected?sort=signers',
]

for next_url in lists:

    while next_url:
        print(base_url + next_url)
        root = lxml.html.parse(base_url + next_url).getroot()

        next_url = None
        for path in ('//*[@id="skip_to_content"]/p[3]/a[3]', '//*[@id="skip_to_content"]/p[3]/a[1]'):
            next_url_node = root.xpath(path)
            if next_url_node:
                next_url = next_url_node[0].attrib['href']
                break

        petitions_list_nodes = root.xpath('//*[@id="skip_to_content"]/table/tr/td[1]/a')
        for node in petitions_list_nodes:
            print(base_url + node.attrib['href'])
            root = lxml.html.parse(base_url + node.attrib['href']).getroot()

            original = base_url + node.attrib['href']
            pid = node.attrib['href'].split('/')[-2]

            action = root.xpath('//*[@id="skip_to_content"]/div[1]/p[1]/text()')[0]
            action = action.replace('We the undersigned petition the Prime Minister to', '').strip()
            
            background_nodes = root.xpath('//*[@id="more_detail"]/p')
            background = '\n\n'.join([bg_node.text_content() for bg_node in background_nodes])

            signatures_node = root.xpath('//*[@id="skip_to_content"]/div[1]/p[2]/text()[3]')
            signatures = None
            if signatures_node:
                signatures = int(signatures_node[0].replace(',', '').strip())

            closed_at = None
            closed_node = root.xpath('//*[@id="skip_to_content"]/div[1]/p[2]/text()[2]')
            if closed_node:
                closed_at = closed_node[0].replace('–', '').strip()
                closed_at = parse(closed_at).isoformat() + 'Z'

            creator = root.xpath('//*[@id="skip_to_content"]/div[1]/p[2]/text()[1]')[0]
            creator = creator.replace('Submitted by', '')
            creator = creator.replace('–', '').strip()

            responses_node = root.xpath('//*[@id="response"]')
            responses = []
            government_response_at = None
            if responses_node:
                lines = []
                created_at = ''
                during_petition = False
                for elem in responses_node[0].getchildren():
                    if elem.tag == 'h3':
                        if lines:
                            responses.append({
                                'created_at': created_at,
                                'during_petition': during_petition,
                                'details': '\n\n'.join(lines)
                            })
                            lines = []

                        header = elem.text.strip()
                        during_petition = 'while petition was still open' in header
                        bits = header.split(',')
                        created_at = parse(bits[1]).isoformat() + 'Z'

                    if elem.tag == 'a':
                        lines.append(elem.text)

                    if elem.tail and elem.tail.strip():
                        lines.append(elem.tail.strip())

                if lines:
                    responses.append({
                        'created_at': created_at,
                        'during_petition': during_petition,
                        'details': '\n\n'.join(lines)
                    })

                for response in reversed(responses):
                    if response['during_petition'] == False:
                        government_response_at = response['created_at']
                        break
            
            state = "closed"
            rejection = None
            rejected_node = root.xpath('//*[@id="signatories"]/p[1]/strong')
            if rejected_node:
                state = "rejected"
                rejection = {
                    'reason': root.xpath('//*[@id="signatories"]/ul/li/text()')[0].strip()
                }
                rejected_details = root.xpath('//*[@id="signatories"]/p[2]/text()[2]')
                if rejected_details:
                    rejection['details'] = rejected_details[0]

            petition_data = {
                "attributes": {
                    "action": action,
                    "background": background,
                    "state": state,
                    "signature_count": signatures,
                    "closed_at": closed_at,
                    "creator_name": creator,
                    "government_response_at": government_response_at,
                    "rejection": rejection,
                    "government_responses": responses
                }
                "id": pid,
                "links": {
                    "original": original
                },
                "type": "petition",
            }

            with open('%s/%s.json' % (file_path, pid), 'w') as f:
                f.write(json.dumps(petition_data, sort_keys=True, indent=4, separators=(',', ': ')))
