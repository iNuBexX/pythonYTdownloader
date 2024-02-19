
def get_format_option(quality):
    """Returns the yt-dlp format string based on user input."""
    if quality == "1080p":
        return "bestvideo[height<=1080]+bestaudio/best"
    elif quality == "720p":
        return "bestvideo[height<=720]+bestaudio/best"
    elif quality == "480p":
        return "bestvideo[height<=720]+bestaudio/best"
    elif quality == "144p":
        return "bestvideo[height<=720]+bestaudio/best"
    elif quality == "audio-only":
        return "bestaudio/best"
    else:
        return "bestvideo+bestaudio/best"  # Default to highest quality