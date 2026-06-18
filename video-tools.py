import subprocess
import os
import time

# ===== AUTO THUMBNAIL FROM VIDEO =====
def generate_thumbnail(video_path, user_id):

    thumb_path = f"thumbs/{user_id}_auto.jpg"

    try:
        subprocess.run([
            "ffmpeg",
            "-i", video_path,
            "-ss", "00:00:03",
            "-vframes", "1",
            thumb_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if os.path.exists(thumb_path):
            return thumb_path

    except:
        pass

    return None


# ===== VIDEO SCREENSHOTS =====
def generate_screenshots(video_path, user_id):

    folder = f"screenshots_{user_id}"
    os.makedirs(folder, exist_ok=True)

    output_pattern = f"{folder}/shot_%02d.jpg"

    try:
        subprocess.run([
            "ffmpeg",
            "-i", video_path,
            "-vf", "fps=1/5",
            output_pattern
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return folder

    except:
        return None


# ===== GET VIDEO INFO =====
def get_video_info(video_path):

    try:
        result = subprocess.check_output([
            "ffprobe",
            "-v", "error",
            "-show_entries",
            "format=duration,size",
            "-of", "default=noprint_wrappers=1",
            video_path
        ]).decode()

        return result

    except:
        return "Unknown"
