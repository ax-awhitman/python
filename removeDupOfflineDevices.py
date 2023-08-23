import datetime
import requests

current_datetime = datetime.datetime.now()
print("Current date and time:", current_datetime)

apiKey = "your_api_key"
mintuesDisconnectFor = 10

url = "https://console.automox.com/api/servers"
headers = {"Authorization": "Bearer " + apiKey}

response = requests.get(url, headers=headers)

data = response.json()

# Create a temp working list
working_names = []

# Create a list of the names from the dicts
for device in data:
    working_names.append(device["display_name"])

# Now Find dup names
duplicate_names = set([x for x in working_names if working_names.count(x) > 1])

# Convert the set into a list
duplicate_names = list(duplicate_names)

# Get delta minutes calc
cutoff_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=mintuesDisconnectFor)

# Create list to be deleted
devices_to_remove = []

# Find any devices that are a duplicate that are disconnected for greater than X minues
for device in data:
    if device['last_disconnect_time'] is not None:
        if device['display_name'] in duplicate_names:
            last_disconnect_time = datetime.datetime.strptime(device['last_disconnect_time'].split("+")[0], "%Y-%m-%dT%H:%M:%S")

            # If device has been disconnected before the cutoff date, include it in the list
            if last_disconnect_time < cutoff_time:
                print("Device " + str(device['name']) + " with Device ID " + str(device['id']) + " will be deleted.")
                devices_to_remove.append(device)


if len(devices_to_remove) > 0:
    for device in devices_to_remove:
        del_url = url + "/" + str(device['id'])
        print("removing device from Automox console: "+ device['display_name'])
        response = requests.delete(del_url, headers=headers)
        print(response)
else:
    print("Nothing to remove!")
