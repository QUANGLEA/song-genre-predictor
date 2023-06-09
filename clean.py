import numpy as np
import pandas as pd
import requests
import json
import os
from dotenv import load_dotenv
import time
from collections import defaultdict

# Constants
token_url = "https://accounts.spotify.com/api/token"
track_url = "https://api.spotify.com/v1/tracks/"
start_idx = 0

# Load data
# Note: Change the starting file every time. This is recorded in record.txt.
df = pd.read_csv('./dataset.csv')

# Authenticate
load_dotenv()
payload = {
    'grant_type': 'client_credentials',
    'client_id': os.getenv('SPOTIFY_CLIENT_ID_NA'),
    'client_secret': os.getenv('SPOTIFY_CLIENT_SECRET_NA')
}

# Request access token
token = ""
try:
    res = requests.post(url=token_url,
                        data=payload)
    if (res.status_code != 200):
        print("ERROR GETTING TOKEN")
        raise res.raise_for_status()

    # Data
    data = res.json()
    if not data['access_token']:
        print('ACCESS TOKEN NOT FOUND')
        raise SystemExit()

    token = data['access_token']

# Failed request
except requests.exceptions.RequestException as e:
    raise SystemExit(e)

# Get preview_url for all tracks
track_headers = {"Authorization": f"Bearer {token}"}

genre_count = defaultdict(int)
GENRE_SET = set(['acoustic', 'blues', 'classical', 'country', 'dance', 'hip-hop', 'rock', 'world-music', 'indie', 'jazz', 'pop', 'edm'])
TRACKS_PER_GENRE = 100

for idx, row in df.iloc[start_idx:].iterrows():
    genre = row['track_genre']
    if genre not in GENRE_SET or genre_count[genre] == TRACKS_PER_GENRE: continue

    try:
        track_res = requests.get(url=track_url+row['track_id'],
                                 headers=track_headers)

        if (track_res.status_code != 200):
            print(track_res.content)
            # Save csv upon error
            new_csv_name = f'dataset_clean_{time.time()}.csv'
            df.to_csv(new_csv_name,
                      sep=',', encoding='utf-8')

            # Save index failed at and retry time
            record_msg = f"Stopped at index {idx}. Saved to file {new_csv_name}. Try again after {track_res.headers['retry-after']} seconds."
            txt_file = open('record.txt', 'w')
            txt_file.write(record_msg)

            # Report
            print("ERROR GETTING TRACK")
            print(record_msg)
            print(df.head(5))

            raise track_res.raise_for_status()

        data = track_res.json()

        # Check for existence of preview_url
        if 'preview_url' not in data or data['preview_url'] is None:
            continue
        df.loc[idx, 'preview_url'] = data['preview_url']
        print(data['preview_url'])
        print(genre, genre_count[genre])
        genre_count[genre] += 1

    # Failed request
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

# Save csv
df.to_csv(f'dataset_clean_{time.time()}.csv', sep=',', encoding='utf-8')
