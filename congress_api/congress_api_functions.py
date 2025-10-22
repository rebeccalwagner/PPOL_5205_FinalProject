
import requests

session = requests.Session()

##########################################################################################

def generate_all_bills(congress, limit, offset, api_key, max_bills):
    """
    This is a generating function that yields one bill at a time from the api call.
    """

    # beginning url based on passed arguments
    url = f"https://api.congress.gov/v3/bill/{congress}?limit={limit}&offset={offset}&api_key={api_key}" 
    count = 0

    while url:

        # call api
        response = session.get(url)
        # make sure request worked
        if response.status_code != 200:
            raise Exception(f"Request failed with status code {response.status_code}")
        
        # extract data
        data = response.json()
        bills = data.get("bills", []) # grab empty list if there are no bills

        # generate bills, ending the loop if we hit a given max
        for bill in bills:
            yield bill
            count += 1

            if max_bills is not None and count >= max_bills:
                return
        

        pagination = data.get("pagination", {})
        next_url = pagination.get("next")

        if next_url:
            url = next_url + f"&api_key={api_key}"
        else:
            url = None  # End the loop cleanly

##########################################################################################

def get_bill_metadata(bill, api_key):
    """
    Fill doc string here
    """
    
    # construct url from bill and api key
    url = bill["url"] + f"&api_key={api_key}"

    # call api
    try:
        response = session.get(url)
    except Exception as e:
        print(f"Failed to fetch bill {bill['number']} with code: {response.status_code}: {e}")
    
    # extract data
    data = response.json()
    
    return data["bill"]

##########################################################################################

def get_bill_text_url(bill_metadata, api_key):

    # construct url from text version and api key
    url = bill_metadata["textVersions"]["url"] + f"&api_key={api_key}"

    # call api
    try:
        response = session.get(url)
    except Exception as e:
        print(f"Request failed with status code {response.status_code}: {e}")
    
    data = response.json()
    versions = data["textVersions"]

    # identify the latest version of the bill (they are not necesarily in order, and sometimes have no date)
    latest_version = _get_latest_bill_version(versions)
    # grab the formats associated with this latest version
    latest_version_formats = [version for version in versions if version["type"] == latest_version][0]["formats"]
    # grab the url for the format we want (.htm prefered, .xml ok)
    formatted_text_url = _get_best_format(latest_version_formats)

    return formatted_text_url

    # then, we will also save the metadata for the other versions, in case it is necessary in the future

##########################################################################################

def _get_latest_bill_version(versions):

    # most recent to least recent order (house/senate variable)
    priority_order = [
        "Public Law",
        "Enrolled Bill",
        "Reported to House",
        "Reported to Senate",
        "Referred in House",
        "Referred in Senate",
        "Engrossed in House",
        "Engrossed in Senate",
        "Introduced in House",
        "Introduced in Senate"
    ]

    for stage in priority_order:
        for version in versions:
            if version.get("type") == stage:
                return stage
                
##########################################################################################

def _get_best_format(latest_version_formats):

    for format in latest_version_formats:
        if format['url'].lower().endswith('.htm'):
            best_url = format['url']
            break

    # If no .htm found, fallback to .xml
    if not best_url:
        for format in latest_version_formats:
            if format['url'].lower().endswith('.xml'):
                best_url = format['url']
                break
    
    return best_url

##########################################################################################

def save_bill_text(url, file_path, api_key):
    
    response = session.get(url)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(response.text)

##########################################################################################
##########################################################################################
##########################################################################################

def get_policy_area(bill, api_key):
    """
    Out of date - not in use
    """
    
    # construct url from bill and api key
    url = bill["url"] + f"&api_key={api_key}"

    # call api
    response = session.get(url)
    # make sure request worked
    if response.status_code != 200:
        raise Exception(f"Failed to fetch bill {bill['number']} details: {response.status_code}")
    
    # extract data
    data = response.json()
    policy_areas = data["bill"]["policyArea"]

    return policy_areas