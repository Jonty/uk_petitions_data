import os
import json
import requests
import time

# The petitions API is totally broken when browsing old governments so we have
# to fix up the URL
governments = {
    #    '2010-2015_Conservative_-_Liberal_Democrat_coalition_government': ('https://petition.parliament.uk/archived/petitions.json?state=all', '&parliament=3'),
    #    '2015-2017_Conservative_government': ('https://petition.parliament.uk/archived/petitions.json?parliament=1&state=all', '&parliament=2'),
    #    '2017-2019_Conservative_government': ('https://petition.parliament.uk/archived/petitions.json?parliament=1&state=all', '&parliament=1'),
    #    "2019-2024_Conservative_government": ("https://petition.parliament.uk/petitions.json?state=all", "",)
    "2024-_Labour_government": (
        "https://petition.parliament.uk/petitions.json?state=all",
        "",
    )
}


def get_data(url):
    attempts = 0
    response = None
    while attempts < 100:
        print("Fetching %s..." % url)
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
        except Exception as e:
            print("Request failure: %s" % e)

        if not response or response.status_code != 200 or "data" not in data:
            attempts += 1
            print("Fetch failed, retry %s" % attempts)
            time.sleep(5)
        else:
            break

    return data


for gov, (url, append) in governments.items():
    print("Processing the %s government...." % gov)
    path = "petitions/" + gov
    try:
        os.mkdir(path)
    except OSError:
        pass

    while url:
        data = get_data(url + append)
        for petition in data["data"]:
            filename = "%s/%s.json" % (path, petition["id"])
            exists = False

            # Petitions that are open or closed have extended geo data that
            # needs to be fetched separately
            extended_data = petition["attributes"]["state"] in ("open", "closed")

            if os.path.isfile(filename):
                exists = True
                with open(filename, "r") as f:
                    existing_data = json.load(f)

                    updated = (
                        existing_data["attributes"]["updated_at"]
                        != petition["attributes"]["updated_at"]
                    )
                    ext_data_missing = (
                        extended_data
                        and "signatures_by_constituency"
                        not in existing_data["attributes"]
                    )

                    if ext_data_missing:
                        print(
                            "Petition %s missing extended geo data, updating"
                            % petition["id"]
                        )

                    # Skip writing/fetching petitions that have not been
                    # updated since we last ran, unless the extended data is
                    # missing on disk and needs fetching
                    if not updated and not ext_data_missing:
                        continue

            if extended_data:
                print(
                    "%s is %s, fetching full data..."
                    % (petition["id"], petition["attributes"]["state"])
                )
                petition_data = get_data(petition["links"]["self"])

                # The link data is in a different location in this response, so move it
                petition = petition_data["data"]
                petition["links"] = petition_data["links"]

            with open(filename, "w") as f:
                change = "updated" if exists else "new"
                print("Writing %s petition %s" % (change, petition["id"]))
                f.write(
                    json.dumps(
                        petition, sort_keys=True, indent=4, separators=(",", ": ")
                    )
                )

        url = data["links"]["next"]
