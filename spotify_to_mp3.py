# Downloads a Spotify playlist into a folder of MP3 tracks
# Jason Chen, 21 June 2020

import os
import spotipy
import spotipy.oauth2 as oauth2
import yt_dlp
from youtube_search import YoutubeSearch

def write_track_page(outfile, tracks):
    for item in tracks['items']:
        if 'track' in item:
            track = item['track']
        else:
            track = item
        try:
            track_url = track['external_urls']['spotify']
            track_name = track['name']
            track_artist = track['artists'][0]['name']
            csv_line = track_name + "," + track_artist + "," + track_url + "\n"
            try:
                outfile.write(csv_line)
            except UnicodeEncodeError:  # Most likely caused by non-English song names
                print("Track named {} failed due to an encoding error. This is \
                    most likely due to this song having a non-English name.".format(track_name))
        except KeyError:
                print(u'Skipping track {0} by {1} (local only?)'.format(
                        track['name'], track['artists'][0]['name']))

def write_tracks(text_file: str, tracks: dict):
    # Writes the information of all tracks in the playlist to a text file. 
    # This includins the name, artist, and spotify URL. Each is delimited by a comma.
    with open(text_file, 'w+', encoding='utf-8') as outfile:
        while tracks['next']:
            write_track_page(outfile, tracks)
            tracks = spotify.next(tracks)

def write_playlist(username: str, playlist_id: str):
    results = spotify.user_playlist(username, playlist_id, fields='tracks,next,name')
    playlist_name = results['name']
    text_file = u'{0}.txt'.format(playlist_name, ok='-_()[]{}')
    print(u'Writing {0} tracks to {1}.'.format(results['tracks']['total'], text_file))
    tracks = results['tracks']
    write_tracks(text_file, tracks)
    return playlist_name

def find_and_download_songs(reference_file: str):
    TOTAL_ATTEMPTS = 10
    with open(reference_file, "r", encoding='utf-8') as file:
        for line in file:
            temp = line.split(",")
            name, artist = temp[0], temp[1]
            text_to_search = artist + " - " + name
            best_url = None
            attempts_left = TOTAL_ATTEMPTS
            while attempts_left > 0:
                try:
                    results_list = YoutubeSearch(text_to_search, max_results=1).to_dict()
                    best_url = "https://www.youtube.com{}".format(results_list[0]['url_suffix'])
                    break
                except IndexError:
                    attempts_left -= 1
                    print("No valid URLs found for {}, trying again ({} attempts left).".format(
                        text_to_search, attempts_left))
            if best_url is None:
                print("No valid URLs found for {}, skipping track.".format(text_to_search))
                continue
            # Run you-get to fetch and download the link's audio
            print("Initiating download for {}.".format(text_to_search))
            # this is what is fucking up - fix this so that it downloads in mp3
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([best_url])

if __name__ == "__main__":
    # Parameters
    print("Please read README.md for use instructions.")    
    client_id = input("Client ID: ")
    client_secret = input("Client secret: ")
    username = input("Spotify username: ")
    playlist_uri = input("Playlist URI/Link: ")
    if playlist_uri.find("https://open.spotify.com/playlist/") != -1:
        playlist_uri = playlist_uri.replace("https://open.spotify.com/playlist/", "")
    auth_manager = oauth2.SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    playlist_name = write_playlist(username, playlist_uri)
    reference_file = "{}.txt".format(playlist_name)
    # Create the playlist folder
    if not os.path.exists(playlist_name):
        os.makedirs(playlist_name)
    os.rename(reference_file, playlist_name + "/" + reference_file)
    os.chdir(playlist_name)
    find_and_download_songs(reference_file)
    print("Operation complete.")
