class DownloadThread(QThread):
    progress = pyqtSignal(int)

    def __init__(self, url, directory, name, quality, start=None, end=None):
        super().__init__()
        self.url = url
        self.directory = directory
        self.name = name
        self.quality = quality
        self.start = start
        self.end = end

    def run(self):
        opts = {
            "outtmpl": os.path.join(self.directory, "input"),
            "format": self.quality,
            "progress_hooks": [self.progress_hook]  # Attach progress hook
        }

        if self.start and self.end:
            opts["external_downloader_args"] = ["-ss", self.start, "-to", self.end]

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([self.url])

    def progress_hook(self, d):
        """Handles progress updates from yt_dlp."""
        if d["status"] == "downloading":
            total_bytes = d.get("total_bytes", None) or d.get("total_bytes_estimate", None)
            downloaded_bytes = d.get("downloaded_bytes", 0)
            if total_bytes:
                progress_percentage = int((downloaded_bytes / total_bytes) * 100)
                self.progress.emit(progress_percentage)  # Update UI progress bar

        elif d["status"] == "finished":
            self.progress.emit(100)  # Mark as complete
