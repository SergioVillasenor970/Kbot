import os
import yt_dlp

def valid_url(url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'noplaylist': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=False)
        return True
    except:
        return False

def download(url):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    audio_dir = os.path.join(base_dir, "audio")

    clean_files()

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(audio_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            filename = os.path.splitext(filename)[0] + ".mp3"
            return os.path.basename(filename)

    except Exception as e:
        print("Error:", e)
        return None

def clean_files():
    # Sets relative route to "audio" dir
    base_dir = os.path.dirname(os.path.abspath(__file__))
    audio_dir = os.path.join(base_dir, "audio")

    # Creates a folder if one doesnt exists
    os.makedirs(audio_dir, exist_ok=True)

    # Deletes other files in the folder
    for file in os.listdir(audio_dir):
        target_path = os.path.join(audio_dir, file)
        os.remove(target_path)
    
    return