# Downloads a Spotify playlist into a folder of MP3 tracks
# Jason Chen, 21 June 2020 - Updated by Zachary B 24/10/22

import os
import spotipy
import spotipy.oauth2 as oauth2
import re
from pathlib import Path
from youtube_search import YoutubeSearch
from pytube import YouTube
from keys import client_id, client_secret

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
        write_track_page(outfile, tracks)
        while tracks['next']:
            tracks = spotify.next(tracks)
            write_track_page(outfile, tracks)

def write_playlist(username: str, playlist_id: str):
    results = spotify.user_playlist(username, playlist_id, fields='tracks,next,name')
    playlist_name = results['name']
    text_file = u'{0}.txt'.format(playlist_name, ok='-_()[]{}')
    print(u'Writing {0} tracks to {1}.'.format(results['tracks']['total'], text_file))
    tracks = results['tracks']
    write_tracks(text_file, tracks)
    return playlist_name

def download_youtube_mp3_from_video_id(url):
    yt = YouTube(url)
    status = yt.vid_info['playabilityStatus']['status']
    if status == "UNPLAYABLE":
        print(f"video {url} is not playable, cannot download.")
        return

    try: isinstance(yt.length, int)
    except:
        print(f"Could not get video length for {url}. Skipping download.")
        return

    # create condition - if the yt.length > 600 (10 mins), then don't download it
    if yt.length > 1800:
        print(f"video {url} is longer than 20 minutes. Skipping download.")
        return

    try: video = yt.streams.filter(only_audio=True).first()
    except:
        print(f'Unable to get title for video {url}. Skipping download.')
        return

    try: song_title_raw = yt.title
    except:
        print(f'Unable to get title for video {url}. Skipping download.')
        return

    song_title = re.sub('\W+',' ', song_title_raw).lower().strip()
    
    out_file = video.download(f"{song_title}")
    
    download_path = f"{song_title}"
    
    # save the file (which will be mp4 format)
    base, ext = os.path.splitext(out_file)

    if "Video Not Available" in base:
        print("video not available")
        os.rmdir(download_path)
        return

    new_file = base + '.mp3'
    os.rename(out_file, new_file)

    # move the mp3 to the root dir - why are we doing this?
    p = Path(new_file).absolute()
    parent_dir = p.parents[1]
    p.rename(parent_dir / p.name)

    # delete the child dir
    os.rmdir(download_path)

    # result of success
    print(f"{song_title} has been successfully downloaded. Video url: {url}")

def find_and_download_songs(reference_file: str, playlist_name):
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
            ## here is where I want to introduce my youtube to mp3 file

            # Run you-get to fetch and download the link's audio
            print("Initiating download for {}.".format(text_to_search))
            download_youtube_mp3_from_video_id(best_url)

if __name__ == "__main__":
    # Parameters
    print("Please read README.md for use instructions.")
    username = 'Mochary' # input("Spotify username: ")
    playlist_uri = input("Playlist URI/Link: ")
    playlist_uri = re.split("playlist/|\?",playlist_uri)[1]
    if playlist_uri.find("https://open.spotify.com/playlist/") != -1:
        playlist_uri = playlist_uri.replace("https://open.spotify.com/playlist/", "")
    auth_manager = oauth2.SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    playlist_name = write_playlist(username, playlist_uri)
    reference_file = f"{playlist_name}.txt"
    # Create the playlist folder
    if not os.path.exists(playlist_name):
        os.makedirs(playlist_name)
    os.rename(reference_file, playlist_name + "/" + reference_file)
    os.chdir(playlist_name)
    find_and_download_songs(reference_file, playlist_name)
    print("Operation complete.")
