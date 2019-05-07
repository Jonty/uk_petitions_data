import sys
import json
import requests
import time


def get_data(url):
    attempts = 0
    response = None
    while attempts < 100:
        print("Fetching %s..." % url)
        try:
            response = requests.get(url, timeout=20)
            data = response.json()
        except Exception as e:
            print("Request failure: %s" % e)

        if not response or response.status_code != 200 or "result" not in data:
            attempts += 1
            print("Fetch failed, retry %s" % attempts)
            time.sleep(5)
        else:
            break

    return data


count = 0
url = "http://lda.data.parliament.uk/epetitions.json?_page=0"
while url:
    print("\n\n---------LOADING INDEX: " + url)
    data = get_data(url + "&_pageSize=500")

    for petition in data["result"]["items"]:
        filename = "tracking/%s.json" % (petition["identifier"]["_value"])
        ldid = petition["_about"].replace("http://data.parliament.uk/resources/", "")

        petition_data = get_data(
            "http://lda.data.parliament.uk/epetitions/%s/track.json?_pageSize=500"
            % (ldid)
        )

        if petition_data["result"]["totalResults"] > 500:
            print("ERROR: PETITION HAS MORE THAN 500 ENTRIES")
            sys.exit(1)

        with open(filename, "w") as f:
            count += 1
            print("Writing petition %s: %s" % (count, filename))
            f.write(
                json.dumps(
                    petition_data, sort_keys=True, indent=4, separators=(",", ": ")
                )
            )

    url = data["result"].get("next", None)

