def trim_args(start,end):
    return {
        "ffmpeg_i": ["-ss", str(start), "-to", str(end)],
        "ffmpeg_o": ["-c:v", "copy", "-c:a", "copy"]  # Ensure both video & audio are copied
    }