import requests

IDEABOARD_IP = "192.168.68.103"

def doorAutomate(val):
    if val == 0:
        response = requests.get(f"http://{IDEABOARD_IP}/open")
        if response.status_code == 200:
            print("Door opened successfully.")
        else:
            print(f"Failed to open door: {response.status_code}")
    elif val == 1:
        response = requests.get(f"http://{IDEABOARD_IP}/close")
        if response.status_code == 200:
            print("Door closed successfully.")
        else:
            print(f"Failed to close door: {response.status_code}")
