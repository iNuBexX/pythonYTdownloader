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

## Gui Usage


- **How to download a video:**
  -  **find a video** – find a youtube video you would like to download.
  -  **copy its share link** – click on share button, copy the link on the widget that appears.
  -  **populate fields on the GUI** 
      - copy the url into the url input field , 
      - choose a name **(no format please )**, 
      - chose a quality **(must be existing on youtube)**, 
      - choose partial download or not ,incase partial is chosen please provide the from and to sections in this format: HH:MM:SS for example to download from minute one to minute one and thirty six seconds **from** will be **00:01:00** and **to** will be   **00:01:36**

- **Limitations:**
  -  **Quality checking:** must manually check the existing qualities and make sure not to chose one that doesn't exist fore example cannot chose 1080p for a video the max quality of which is 360p might add that later
  -  **Max Quality:** cannot yet download videos in higher quality than 1080p like 2k and 4k might add that later
  -  **Progress Bars:**  cannot yet implement a progress bar for downloads (limitation within the used library and must wait mainters to fill it)
  -  **Field Checking** must not provide weird file names that contain slashes in them because that will confuse the software might implement checks for that 
  


  thank you most kindly for reading