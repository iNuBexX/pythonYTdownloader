import os
import yt_dlp
import subprocess
import imageio_ffmpeg  # Ensures FFmpeg is available in the venv
import argparse
from utils.formatparser import get_format_option
from utils.conversion import converter 
from utils.trimmer import trim_args
#change this to become a parsed arg
import datetime


def validate_time_format(time_str):
    """Validates and converts a time string (hh:mm:ss) to a datetime object."""
    try:
        return datetime.datetime.strptime(time_str, "%H:%M:%S").time()
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid time format: {time_str}. Use HH:MM:SS.")

# Setup argument parser
parser = argparse.ArgumentParser(description="Compare two time arguments")



def main():
    print("youtube downloader utility running ...")
    parser = argparse.ArgumentParser(description="Download YouTube videos in specified quality.")
    parser.add_argument("url", type=str, help="YouTube video URL")
    parser.add_argument("directory", type=str, help="Pick directory to download the video into")
    parser.add_argument("name", type=str, help="output file name", help="Desired quality")
    parser.add_argument("quality", type=str, choices=["1080p", "720p", "480p", "360p", "144p", "audio-only"], help="Desired quality")
    parser.add_argument("--start", type=validate_time_format, help="Partial download Start time (HH:MM:SS)")
    parser.add_argument("--end", type=validate_time_format, help="Partial download End time (HH:MM:SS)")
    ffmpeg_args = {}
    args = parser.parse_args()
    if args.start is not None and args.end is None:
        parser.error("if Start time is provided for partial download you must provide the End time")
    if args.end is not None and args.start is None:
        parser.error("if End time is provided for partial download you must provide the Start time")
    if args.end is not None and args.start is not None:
        if args.start >= args.end:
            parser.error("Start time must be earlier than end time!")
    if args.end is not None and args.start is not None:
        ffmpeg_args = trim_args(args.start.strftime("%H:%M:%S"),args.end.strftime("%H:%M:%S"))
    vidConverter = converter()
    # Get FFmpeg path from imageio_ffmpeg
    args.quality = get_format_option(args.quality)
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    
    # Set FFmpeg arguments based on the chosen mode

    if args.directory[-1]!= "/":
        args.directory += "/"
    opts = {
        "outtmpl": args.directory+"input.webm", #webm seems to be the most comfortable format to be downloaded in 
        "external_downloader": ffmpeg_path,  # Use FFmpeg from venv
        "external_downloader_args": ffmpeg_args,
        "format": args.quality,
        "writesubtitles": False,
        "writeautomaticsub": False,
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download(args.url)
    # Function to convert .webm to .mp4 using venv FFmpeg
    vidConverter.convert_webm_to_mp4(args.directory+"input.webm", args.directory,args.name, deletesOriginal=True)

if __name__ == "__main__":
    main()