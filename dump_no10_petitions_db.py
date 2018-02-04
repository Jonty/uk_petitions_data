from datetime import datetime, time
import os
import json

import psycopg2
import psycopg2.extras
 
rejection_categories = {
    1: 'Party political material',
    2: 'Potentially libellous, false, or defamatory statements',
    4: 'Information which may be protected by an injunction or court order',
    8: 'Material which is potentially confidential, commercially sensitive, or which may cause personal distress or loss',
    16: 'The names of individual officials of public bodies, unless they are part of the senior management of those organisations',
    32: 'The names of family members of elected representatives or officials of public bodies',
    64: 'The names of individuals, or information where they may be identified, in relation to criminal accusations',
    128: 'Language which is offensive, intemperate, or provocative',
    256: 'Wording that needs to be amended, or is impossible to understand',
    512: 'Statements that don\'t actually request any action',
    1024: 'Commercial endorsement, promotion of any product, service or publication, or statements that amount to adverts',
    2048: 'Duplicate - this is similar to and/or overlaps with an existing petition or petitions',
    4096: 'Outside the remit of the Prime Minister and Government',
    8192: 'False or incomplete name or address information',
    16384: 'Issues for which an e-petition is not the appropriate channel',
    32768: 'Intended to be humorous, or has no point about government policy',
    65536: 'Contains links to websites',
    131072: 'Currently being administered via another process',
}

governments = (
    ('petitions/2005-2007_Labour_government', datetime(2005, 5, 5), datetime(2007, 6, 27, 14, 50, 0)),
    ('petitions/2007-2010_Labour_government', datetime(2007, 6, 27, 14, 50, 0), datetime(2010, 5, 11, 0, 0, 0)),
)

for path, _, _ in governments:
    try:
        os.mkdir(path)
    except OSError:
        pass

def get_rejection_reasons(number):
    reasons = []
    for k, v in rejection_categories.items():
        if number & k:
            reasons.append(v)
    return reasons


conn_string = "host='localhost' port='32768' user='postgres' password='mysecretpassword'"
conn = psycopg2.connect(conn_string)

cursor = conn.cursor('petition_cursor', cursor_factory=psycopg2.extras.DictCursor)
cursor.execute('SELECT id, ref, content, detail, name, organisation, creationtime, deadline, status, rejection_second_categories, rejection_second_reason, laststatuschange, cached_signers, lastupdate FROM petition ORDER BY id;')

for row in cursor:
    pid, ref, content, detail, name, organisation, creationtime, deadline, status, rejection_second_categories, rejection_second_reason, laststatuschange, cached_signers, lastupdate = row

    deadline = datetime.combine(deadline, time())
    closed_at = deadline.isoformat()
    if laststatuschange < deadline:
        closed_at = laststatuschange.isoformat() + 'Z'

    rejected_at = None
    rejection = None
    if status == 'rejected':
        rejected_at = laststatuschange.isoformat() + 'Z'
        rejection = {
            'code': rejection_second_categories,
            'reasons': get_rejection_reasons(rejection_second_categories),
            'details': rejection_second_reason,
        }

    # Get government responses (and first post-close date)
    cursor2 = conn.cursor()
    cursor2.execute("SELECT whencreated, emailsubject, emailbody FROM message WHERE petition_id = %s ORDER BY whencreated;" % pid)
    messages = cursor2.fetchall()

    government_response_at = None
    government_responses = None
    if messages:
        government_responses = []
        for created, subject, body in messages:
            if not government_response_at and created > deadline:
                government_response_at = created.isoformat() + 'Z'
            government_responses.append({
                'created_at': created.isoformat() + 'Z',
                'details': body,
                'summary': subject,
                'updated_at': created.isoformat() + 'Z',
            })

    petition_data = {
        'links': {
            'original': "http://petitions.number10.gov.uk/%s/" % ref
        },
        'data': {
            'id': pid,
            'attributes': {
                'action_prefix': 'We the undersigned petition the Prime Minister to',
                'action': content,
                'background': detail,
                'state': status,
                'signature_count': cached_signers,
                'closed_at': deadline.isoformat() + 'Z',
                'created_at': creationtime.isoformat() + 'Z',
                'opened_at': creationtime.isoformat() + 'Z',
                'creator_name': name,
                'government_response_at': government_response_at,
                'government_responses': government_responses,
                'rejected_at': rejected_at,
                'rejection': rejection,
                'updated_at': lastupdate.isoformat() + 'Z',
            }
        },
        'type': 'petition',
    }

    file_path = None
    for path, start, end in governments:
        if creationtime >= start and creationtime < end:
            file_path = path
            break

    print("Dumping %s..." % pid)
    with open('%s/%s.json' % (file_path, pid), 'w') as f:
        f.write(json.dumps(petition_data, sort_keys=True, indent=4, separators=(',', ': ')))
