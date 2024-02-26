
import subprocess
import os
import imageio_ffmpeg  # Ensures FFmpeg is available in the venv

ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

class converter:
    def __init__(self):
        pass
    def convert_webm_to_mp4(self,input_file, output_filedir,output_fileName, deletesOriginal):
        output_dir = os.path.dirname(output_fileName)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        mkv_file = input_file + ".mkv"
        webm_file = input_file + ".webm"

        if os.path.exists(mkv_file):
            input_file = mkv_file
        elif os.path.exists(webm_file):
            input_file = webm_file
        
        command = [
            ffmpeg_path,        # Use FFmpeg from imageio_ffmpeg
            "-i", input_file,   # Input file
            "-c:v", "libx264",  # Encode video with H.264 (MP4-compatible)
            "-preset", "slow",  # Higher quality compression
            "-crf", "2",       # Constant Rate Factor (lower = better quality)
            "-c:a", "aac",      # Convert audio to AAC
            "-b:a", "128k",     # Set audio bitrate
            "-y",               # Overwrite output if exists
            output_filedir+output_fileName,
            "-movflags",
            "+faststart",
            
        ]
        
        try:
            subprocess.run(command, check=True)
            print(f"✅ Conversion successful: {output_fileName}")
            if deletesOriginal:
                if os.path.exists(input_file):
                    os.remove(input_file)
                    print(f"🗑️ Deleted original file: {input_file}")
                else:
                    print(f"⚠️ File not found: {input_file}")
        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg error: {e}")