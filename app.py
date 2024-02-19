import os
import yt_dlp
import subprocess
import imageio_ffmpeg  # Ensures FFmpeg is available in the venv
import argparse
from utils.formatparser import get_format_option
from utils.conversion import converter 
from utils.trimmer import trim_args
#change this to become a parsed arg
url = "https://www.youtube.com/watch?v=sLfAcqbzdco"

# Set whether to trim the video or download the full video
use_trim = False  # Change to False to download the full video

# Times in seconds (only used if trimming)
start = "00:04:03"
end = "00:04:21"


vidConverter = converter()
# Get FFmpeg path from imageio_ffmpeg
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

# Set FFmpeg arguments based on the chosen mode
ffmpeg_args = {}
if use_trim:
    ffmpeg_args = trim_args(start,end)

opts = {
    "outtmpl": "downloads/input.webm",
    "external_downloader": ffmpeg_path,  # Use FFmpeg from venv
    "external_downloader_args": ffmpeg_args if use_trim else {},
    "format": "bestvideo+bestaudio",
    "writesubtitles": False,
    "writeautomaticsub": False,
}


def main():
    parser = argparse.ArgumentParser(description="Download YouTube videos in specified quality.")
    parser.add_argument("url", type=str, help="YouTube video URL")
    parser.add_argument("quality", type=str, choices=["1080p", "720p", "480p", "360p", "144p", "audio-only"], help="Desired quality")
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download(url)
# Function to convert .webm to .mp4 using venv FFmpeg
    vidConverter.convert_webm_to_mp4("downloads/input.webm", "downloads/output.mp4", deletesOriginal=True)

if __name__ == "main":
    main()