## Simple Usage
use this command for a simple partial download into the directory where the tool is being invoked
```py .\app.py https://youtu.be/dSjjEzKLqPI?si=JfXGnCaVrNy673Ro ./ 1080p --start "00:04:11" --end "00:04:19"```


to view all options help:

`` py .\app.py -h``

usage: app.py [-h] [--start START] [--end END] url directory {1080p,720p,480p,360p,144p,audio-only}

Download YouTube videos in specified quality.

positional arguments:
  url                   YouTube video URL
  directory             Pick directory to download the video into
  {1080p,720p,480p,360p,144p,audio-only}
                        Desired quality

options:
  -h, --help            show this help message and exit
  --start START         Partial download Start time (HH:MM:SS)
  --end END             Partial download End time (HH:MM:SS)