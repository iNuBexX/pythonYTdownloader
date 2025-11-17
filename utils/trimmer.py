def trim_args(start,end):
    return {
        "ffmpeg_i": ["-ss", str(start), "-to", str(end)],
        "ffmpeg_o": ["-c:v", "libx264", "-preset", "fast", "-c:a", "aac", "-b:a", "128k", "-f", "mp4"],
    }