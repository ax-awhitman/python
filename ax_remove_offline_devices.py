import pip._vendor.requests as requests
from datetime import datetime
import argparse

# --Function Block--#

# GET servers ax api call 
def ax_api_call_servers(ax_api_key, org_id):
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + ax_api_key}
    url = "https://console.automox.com/api/servers"
    query = {"o": org_id}
    response = requests.get(url, headers=headers, params=query)
    data = response.json()
    return data


# DELETE servers ax api call
def remove_ax_device(ax_api_key, device_id, org_id):
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + ax_api_key}
    url = "https://console.automox.com/api/servers/" + device_id
    query = {"o": org_id}
    response = requests.delete(url, headers=headers, params=query)
    if response.status_code == 204:
        print("Successfully removed devices from Automox")
    else:
        data = response.json()


# determine device disconnect times 
def disconnect_time_in_days(disconnect_time):
    result = []
    for x in data:
        if x['last_disconnect_time']:
            date = datetime.strptime(x['last_disconnect_time'], '%Y-%m-%dT%H:%M:%S%z')
            current_date = datetime.now(date.tzinfo)
            date_difference = current_date - date
            days_difference = date_difference.days
            if days_difference > disconnect_time:
                result.append(x['id'])
    return result
    
    
# --Execution Block-- #
# --Parse command line arguments-- #

parser = argparse.ArgumentParser()

parser.add_argument(
    'ax_api_key',
    type=str,
    help='Automox API Key.')

parser.add_argument(
    'org_id',
    type=str,
    help='Automox Org ID.')

parser.add_argument(
    'disconnect_time',
    type=int,
    help='The amount of days disconnected needed to remove the device from ax'
)

# Parse the args into the args variable holder
args = parser.parse_args()

# (Optional) Map the args values into the named variables you are using later
ax_api_key = args.ax_api_key
org_id = args.org_id
disconnect_time = args.disconnect_time

# -MAIN-

data = ax_api_call_servers(ax_api_key, org_id)
device_to_remove = disconnect_time_in_days(disconnect_time)
print(device_to_remove)

for device in device_to_remove:
    device_id = str(device)
    remove_ax_device(ax_api_key, device_id, org_id)
