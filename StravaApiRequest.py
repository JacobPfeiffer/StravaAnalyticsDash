import time
from stravalib.client import Client
import requests
from bs4 import BeautifulSoup
import webbrowser
from urllib.parse import urlparse, parse_qs
import http.server
import socketserver
import os
from pprint import pprint
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        query = urlparse(self.path).query
        query_components = parse_qs(query)
        auth_code = query_components["code"][0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Authorization successful. You can close this window.")

def get_secrets(filename):
    secrets = {}
    with open(filename, 'r') as f:
        lines = f.readlines()
        for line in lines:
            key, value = line.strip().split('=')
            secrets[key] = value
    return secrets

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Build the full path to the file
file_path = os.path.join(script_dir, 'secrets.txt')
secrets = get_secrets(file_path)
client_id = secrets['CLIENT_ID']
client_secret = secrets['CLIENT_SECRET']

redirect_uri = "http://localhost:8282"
client = Client()
authorize_url = client.authorization_url(
    client_id=client_id, redirect_uri=redirect_uri
)

webbrowser.open(authorize_url)

# Start the server
with socketserver.TCPServer(("localhost", 8282), Handler) as httpd:
    print("Serving at port", 8282)
    httpd.handle_request()

# At this point, auth_code should contain the authorization code
print("Authorization code:", auth_code)
# Parse the URL

token_response = client.exchange_code_for_token(
    client_id=client_id, client_secret=client_secret, code=auth_code
)
access_token = token_response["access_token"]
refresh_token = token_response["refresh_token"]
expires_at = token_response["expires_at"]

# Now store that short-lived access token somewhere (a database?)
client.access_token = access_token
# You must also store the refresh token to be used later on to obtain another valid access token
# in case the current is already expired
client.refresh_token = refresh_token

# An access_token is only valid for 6 hours, store expires_at somewhere and
# check it before making an API call.
client.token_expires_at = expires_at

athlete = client.get_athlete()
print(
    "For {id}, I now have an access token {token}".format(
        id=athlete.id, token=access_token
    )
)

ten_days_ago = datetime.now() - timedelta(days=10)

activities = client.get_activities(after=ten_days_ago)
first_activity_id = next(activities).id
print(first_activity_id)
activity = client.get_activity(first_activity_id)
print(activity.name)
print(activity.type)
print(activity.moving_time)

# Convert activities to a list of dictionaries
activities_list = [activity.to_dict() for activity in activities]

# Convert the list of dictionaries to a DataFrame
df = pd.DataFrame(activities_list)

# Print the DataFrame
#print(df.columns)
#print(df['has_heartrate'])
#print(df["name"], df["sport_type"], df["distance"])
unique_values_and_count = df["sport_type"].value_counts(ascending=True) 
sport_png_path = os.path.join(script_dir, 'sport_type.png')
plt.bar(unique_values_and_count.index, unique_values_and_count)
plt.savefig(sport_png_path)

time_spent_path = os.path.join(script_dir, 'time_spent_per_sport.png')
time_spent_per_sport = df.groupby("sport_type")["moving_time"].sum().astype('timedelta64[s]').astype('int64')/60
print(time_spent_per_sport)
# convert timedelta to minutes
plt.bar(time_spent_per_sport.index, time_spent_per_sport)
plt.savefig(time_spent_path)

# ... time passes ...
if time.time() > client.token_expires_at:
    refresh_response = client.refresh_access_token(
        client_id=client_id, client_secret=client_secret, refresh_token=client.refresh_token
    )
    access_token = refresh_response["access_token"]
    refresh_token = refresh_response["refresh_token"]

# Get the most recent activity
activities = client.get_activities(limit=1)
most_recent_activity = next(activities)
print(most_recent_activity.name)
streams = client.get_activity_streams(most_recent_activity.id, types=["time", "heartrate", "cadence", "watts", "velocity_smooth"])
df2 = pd.DataFrame({
    'time': streams['time'].data,
    'heartrate': streams['heartrate'].data,
    'cadence': streams['cadence'].data,
    'watts': streams['watts'].data,
    'speed': streams['velocity_smooth'].data
})

# Plot the heart rate over time of most recent activity
def
    plt.clf()
    plt.plot(df2['time'], df2['heartrate'])
    plt.xlabel('Time (s)')
    plt.ylabel('Heart rate (bpm)')
    plt.title('Heart Rate Over Time for ' + most_recent_activity.name)
    plt.savefig(os.path.join(script_dir, 'heartrate.png'))
    print(df2)