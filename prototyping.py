"""
It took me far longer than necessary to figure out how to use yt-dlp to trim/download a subset of a longer video
outside the context of a command line (i.e., directly in Python), so I'm recording it here for posterity.
There's no shortage of command-line examples of using `--ppa "ffmpeg_i:[...]`, but the documentation doesn't
exactly make it clear how to translate this to the Python version of the options, so here goes. A couple
additional quirks come into play too; we'll get to those soon enough.
"""

import yt_dlp
import subprocess
url = "https://www.youtube.com/watch?v=sLfAcqbzdco"

# times in seconds
start = "00:04:03"
end ="00:04:21"

ffmpeg_args = {
  # - Don't forget the _i after "ffmpeg"; this puts the arguments before ffmpeg's `-i` argument,
  #   thus short-circuiting the download itself. Fail to do that,
  #   and you might as well skip ffmpeg for the download and trim in post-processing.
  # - Note that the arguments are pre-parsed into a list, like you'd pass to `subprocess.run`.
  "ffmpeg_i": ["-ss", str(start), "-to", str(end)]  ,
  "ffmpeg_o": ["-to", str(end), "-c:v", "copy", "-c:a", "copy"]  # Ensure both video & audio are copied
}
opts = {
    "outtmpl":"input.webm",
    "external_downloader": "ffmpeg",
    "external_downloader_args": ffmpeg_args,
    "format": "bestvideo+bestaudio",  # Keep both video & audio
    # though not required, I'm including the subtitles options here for a reason; see below
    "writesubtitles": False,
    "writeautomaticsub": False,
    # to suppress ffmpeg's stdout output
}



with yt_dlp.YoutubeDL(opts) as ydl:
  ydl.download(url)
  
  # If you want WebVTT captions, yt-dlp will fail to download them if you're using ffmpeg.
  # This isn't ffmpeg's fault; it's because yt-dlp (as of this writing) forces ffmpeg to use
  # the stream copy encoder (look for `args += ['-c', 'copy']` in downloader/external.py).
  # yt-dlp hosts their own builds of ffmpeg, and one of them supposedly fixes this problem
  # by ignoring certain WebVTT header lines, but why would you want to install a custom build
  # to download a less informative version of the caption files?
  # Anyway, we can't get around this with any other options that I've found, 
  # so we'll run a second download to get captions.
  
  # Note that you can create a new YouTubeDL instance with a new options dictionary, but the
  # constructor is a bit expensive, so I'm including an example of reusing a built instance
  # for kicks. This dictionary tweaking is likely best separated out into its own function.
  opts = {
    **ydl.params,
    "external_downloader": "native",
    "external_downloader_args": {},
    "writesubtitles": True,
    # if you also want automatically generated captions/subtitles
    "writeautomaticsub": True,
    # so we only get the captions and don't download the (whole) video again
    "skip_download": True,
  }
  ydl.params = opts
  ydl.download(url)


import subprocess
def convert_webm_to_mp4(input_file, output_file):
    command = [
        "ffmpeg",
        "-i", input_file,    # Input file
        "-c:v", "libx265",   # Encode video with H.264
        "-preset", "slow",   # Higher quality compression
        "-crf", "22",        # Constant Rate Factor (lower = better quality)
        "-c:a", "aac",       # Convert audio to AAC
        "-b:a", "128k",      # Set audio bitrate to 128kbps
        "-y",                # Overwrite output if exists
        output_file
    ]
    
    try:
        subprocess.run(command, check=True)
        print(f"✅ Conversion successful: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg error: {e}")

convert_webm_to_mp4("input.webm", "output.mp4")
