import sys
import tempfile
from better_ffmpeg_progress import FfmpegProcess
from tqdm import tqdm
from pytube import Playlist as pl, YouTube
from pytube.cli import on_progress
from constants import MP3_PATH
from utils import write_to_jsonl

class Playlist:
    def __init__(self, url, use_oauth=True, allow_oauth_cache=True):
        self.url = url
        self.use_oauth = use_oauth
        self.allow_oauth_cache = allow_oauth_cache
        
        self.playlist = pl(url)

    def extract_metadata(self, vid_url, publish_date, vid_details):
        # extract relevant metadata for pre-processing
        meta = {}
        meta['url'] = vid_url
        meta['published'] = publish_date
        meta['video_id'] = vid_details['videoId']
        meta['title'] = vid_details['title']
        meta['length'] = vid_details['lengthSeconds']
        meta['keywords'] = vid_details['keywords']
        meta['description'] = vid_details['shortDescription']
        meta['thumbnail'] = vid_details['thumbnail']['thumbnails'][0]['url']
        return meta
    
    def extract_audio(self, streams):
        # get highest bitrate audio stream
        highest_bitrate = streams.get_audio_only()
        itag = highest_bitrate.itag
        # confirm if audio stream is mp4 file, else get lower bitrate mp4 file
        if highest_bitrate.mime_type != 'audio/mp4':
            itag = None
            audio_streams = streams.filter(only_audio=True)
            for stream in audio_streams:
                if stream.mime_type == 'audio/mp4':
                    itag = stream.itag
                    break
        if itag is None: return None
        return streams.get_by_itag(itag)

    def download_audio(self, vid_url):
        try:
            yt = YouTube(vid_url, use_oauth=self.use_oauth, allow_oauth_cache=self.allow_oauth_cache)
            # extract video metadata
            publish_date = yt.publish_date.strftime('%m/%d/%Y')
            vid_details = yt.vid_info['videoDetails']
            meta = self.extract_metadata(vid_url, publish_date, vid_details)
            # extract audio stream
            audio_stream = self.extract_audio(yt.streams)
            if audio_stream:
                # append each video's metadata to .jsonl file with path to audio
                write_to_jsonl(meta)
                # download audio file to mp4 (audio)
                print('\nDownloading...', meta['title'], '({})'.format(meta['url']))
                # create temp file for mp4 file download
                temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', dir=MP3_PATH)
                audio_stream.download(filename=temp_file.name)
                # convert mp4 to mp3 using ffmpeg
                out_file = MP3_PATH + meta['video_id'] + '.mp3'
                process = FfmpegProcess(["ffmpeg", "-i", temp_file.name, out_file])
                process.run()
                temp_file.close()

        except Exception as err:
            print('Error in downloading video:', vid_url)
            raise(err)
    
    def download_playlist(self):
        # Download every video in YouTube playlist
        vid_urls = self.playlist.video_urls
        print('Starting download of YouTube playlist:', self.playlist.title)
        for i, url in enumerate(vid_urls): 
            self.download_audio(url)
            print('Completed ', '({done}/{total})'.format(done=i+1, total=len(vid_urls)))
        print('Finished playlist download!')
    
    # def upload_to_hub(self, path=AUDIO_PATH):
        

    
if __name__ == '__main__':
    if len(sys.argv) != 2: 
        print('Invalid Arguments: Provide YouTube URL of playlist in command line.')
        exit(1)
    try: 
        # Download playlist from cli input of playlist url
        p = Playlist(url=sys.argv[1])
        p.download_playlist()
    
    except Exception as err:
        print(err)
        exit(1)
    
    

    