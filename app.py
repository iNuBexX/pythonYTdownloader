import os
import yt_dlp
import subprocess
import imageio_ffmpeg  # Ensures FFmpeg is available in the venv

url = "https://www.youtube.com/watch?v=sLfAcqbzdco"

# Set whether to trim the video or download the full video
use_trim = False  # Change to False to download the full video

# Times in seconds (only used if trimming)
start = "00:04:03"
end = "00:04:21"

# Get FFmpeg path from imageio_ffmpeg
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

# Set FFmpeg arguments based on the chosen mode
ffmpeg_args = {}
if use_trim:
    ffmpeg_args = {
        "ffmpeg_i": ["-ss", str(start), "-to", str(end)],
        "ffmpeg_o": ["-to", str(end), "-c:v", "copy", "-c:a", "copy"]  # Ensure both video & audio are copied
    }

opts = {
    "outtmpl": "downloads/input.webm",
    "external_downloader": ffmpeg_path,  # Use FFmpeg from venv
    "external_downloader_args": ffmpeg_args if use_trim else {},
    "format": "bestvideo+bestaudio",
    "writesubtitles": False,
    "writeautomaticsub": False,
}

with yt_dlp.YoutubeDL(opts) as ydl:
    ydl.download(url)

# Function to convert .webm to .mp4 using venv FFmpeg
def convert_webm_to_mp4(input_file, output_file, deletesOriginal):
    command = [
        ffmpeg_path,        # Use FFmpeg from imageio_ffmpeg
        "-i", input_file,   # Input file
        "-c:v", "libx264",  # Encode video with H.264 (MP4-compatible)
        "-preset", "slow",  # Higher quality compression
        "-crf", "22",       # Constant Rate Factor (lower = better quality)
        "-c:a", "aac",      # Convert audio to AAC
        "-b:a", "128k",     # Set audio bitrate
        "-y",               # Overwrite output if exists
        output_file
    ]
    
    try:
        subprocess.run(command, check=True)
        print(f"✅ Conversion successful: {output_file}")
        if deletesOriginal:
            if os.path.exists(input_file):
                os.remove(input_file)
                print(f"🗑️ Deleted original file: {input_file}")
            else:
                print(f"⚠️ File not found: {input_file}")
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg error: {e}")

convert_webm_to_mp4("downloads/input.webm", "downloads/output.mp4", deletesOriginal=True)