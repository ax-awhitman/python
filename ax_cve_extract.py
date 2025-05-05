import requests 
import json
import time 
import os
import sys
import csv

##### USER INPUT #####
api_key = "your_api_key"
org_id = "your_org_id"
#####################
  
url = "https://console.automox.com/api/orgs/" + org_id + "/packages"

query = {
  "includeUnmanaged": "0",
  "awaiting": "1",
  "o": org_id,
  "page": "0",
  "limit": "500"
}


def ax_exit_error(error_code, error_message=None, system_message=None):
    print(error_code)
    if error_message is not None:
        print(error_message)
    if system_message is not None:
        print(system_message)
    sys.exit(1)

def ax_report_api_call(api_key, url, params=None, data=None, try_count=0, max_retries=2):
    retry_statuses = [429, 500, 502, 503, 504]
    retry_wait_timer = 5

    headers = {
    "Authorization": "Bearer " + api_key
  }
  
    response = requests.get(url, headers=headers, params=params)

    if response.status_code in retry_statuses:
            try_count = try_count + 1
            if try_count <= max_retries:
                time.sleep(retry_wait_timer)
                return ax_report_api_call(api_key=api_key, url=url, params=params, try_count=try_count, max_retries=max_retries)
            else:
                if not response:
                    print(response.json())
                    response.raise_for_status()

    else:
        if not response:
            print(response.json())
            response.raise_for_status()


    api_response_package = {}
    api_response_package['statusCode'] = response.status_code
    try:
        api_response_package['data'] = response.json()
    except ValueError:
        if response.text == '':
            api_response_package['data'] = None
        else:
            ax_exit_error(501, 'The server returned an unexpected server response.')
    return api_response_package


# Page wrapper for API Call
def ax_call_api_page(api_key, url, params={}, max_retries=2):
    # Validate (or set) Params defaults
    if not params:
        params = {}
    if 'limit' not in params:
        params['limit'] = "500"
    if 'page' not in params:
        params['page'] = "0"
    limit_int = int(params['limit'])
    page_int = int(params['page'])

    full_data_list = []
    while True:
        api_response_package = ax_report_api_call(api_key, url, params=params, try_count=0, max_retries=max_retries)
        if api_response_package['data']:
            full_data_list.append(api_response_package['data'])
            if len(api_response_package['data']) < limit_int:
                api_response_package['data'] = full_data_list
                return api_response_package
            page_int = page_int + 1
            params['page'] = str(page_int)
        else:
            return api_response_package


data = ax_call_api_page(api_key, url, params=query, max_retries=2)
response = json.dumps(data, indent=4)

results = []
server = []

for inner_list in data["data"]:
    for item in inner_list:
        cves = item.get("cves")
        if cves:  # Only include if cves is not empty or None
            results.append({
                "server_id": item["server_id"],
                "installed": item["installed"],
                "display_name": item["display_name"],
                "cves": cves,
                "severity": item["severity"]

            })

for inner_list in data["data"]:
    for item in inner_list:
        server.append(item["server_id"])

ids = list(set(server))

server_list = []

for id in ids:
    url = "https://console.automox.com/api/servers/" + str(id)
    query = {"o": org_id}
    headers = {"Authorization": "Bearer " + api_key}
    response = requests.get(url, headers=headers, params=query)
    data = response.json()
    device = data['display_name']
    serverid = int(data['id'])

    server_list.append({'device': device, 'serverid': serverid})


for item in results:
    for server in server_list:
        if item["server_id"] == server["serverid"]:
            item["device"] = server["device"]


with open('server_list.json', 'w') as f:
    json.dump(results, f, indent=4)

fieldnames = ["server_id", "installed", "display_name", "severity", "device", "cve_count"]

total_cve_count = 0

with open("vuln_list.csv", "w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for item in results:
        # Count CVEs
        cve_list = item["cves"] if isinstance(item["cves"], list) else []
        cve_count = len(cve_list)
        total_cve_count += cve_count

        # Add new field, skip 'cves'
        row = {
            "server_id": item["server_id"],
            "installed": item["installed"],
            "display_name": item["display_name"],
            "severity": item["severity"],
            "device": item.get("device", ""),
            "cve_count": cve_count
        }

        writer.writerow(row)

    # Write total row
    writer.writerow({
        "server_id": "",
        "installed": "",
        "display_name": "",
        "severity": "",
        "device": "TOTAL",
        "cve_count": total_cve_count
    })
