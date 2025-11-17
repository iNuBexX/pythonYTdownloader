
import subprocess
import os
import imageio_ffmpeg  # Ensures FFmpeg is available in the venv

ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

class Converter:
    def __init__(self):
        pass

    def convert_webm_to_mp4(self, input_base, output_filedir, output_fileName, deletesOriginal):
        # Create the output directory if needed.
        if output_filedir and not os.path.exists(output_filedir):
            os.makedirs(output_filedir)
        
        # Try to locate the downloaded file using common extensions.
        possible_extensions = [".mp4", ".mmp4", ".mkv", ".webm"]
        input_file = None
        for ext in possible_extensions:
            candidate = input_base + ext
            if os.path.exists(candidate):
                input_file = candidate
                break

        if input_file is None:
            print(f"❌ No file found for base name: {input_base}")
            return

        # Build the output file path
        output_file = os.path.join(output_filedir, output_fileName)
        
        # Build the ffmpeg command.
        command = [
            ffmpeg_path,         # Use FFmpeg from imageio_ffmpeg
            "-i", input_file,    # Input file
            "-c:v", "libx264",   # Encode video with H.264 (MP4-compatible)
            "-preset", "fast",   # Higher quality compression
            "-crf", "22",         # Constant Rate Factor (lower = better quality)
            "-c:a", "aac",       # Convert audio to AAC
            "-b:a", "192k",      # Set audio bitrate
            "-movflags", "+faststart",
            "-y",                # Overwrite output if exists
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

