
class DownloadThread(QThread):
    progress = pyqtSignal(int)  # Signal to update the progress bar

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        def progress_hook(d):
            if d['status'] == 'downloading':
                downloaded = d.get('_downloaded_bytes', 0)
                total = d.get('total_bytes', d.get('total_bytes_estimate', 1))
                percentage = int((downloaded / total) * 100) if total else 0
                self.progress.emit(percentage)

            elif d['status'] == 'finished':
                self.progress.emit(100)  # Mark as complete

        ydl_opts = {'progress_hooks': [progress_hook]}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(self.url)



