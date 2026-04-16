import os
import shutil
import yt_dlp

async def valid_url(url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'noplaylist': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info.get("duration") > 1800:
                return False
        return True
    except:
        return False

def download(url, guild_id):
    guild_id = str(guild_id)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    audio_dir = os.path.join(base_dir, "audio", guild_id)

    clean_files(guild_id)

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
    

def clean_files(guild_id):
    '''
    ---- DANGER ----
    This function permanently removes entire directories and files based on where it is located.
    Running it outside the propossed file structure may cause irreversable losses of data
    Execute it at your own risk
    '''
    # Sets relative route to "audio" dir
    base_dir = os.path.dirname(os.path.abspath(__file__))
    audio_dir = os.path.join(base_dir, "audio", guild_id)

    # Creates a folder if one doesnt exists
    os.makedirs(audio_dir, exist_ok=True)

    # Deletes other files in the folder
    for file in os.listdir(audio_dir):
        target_path = os.path.join(audio_dir, file)
        os.remove(target_path)
    
    return


def clean_all_guilds():
    '''
    ---- DANGER ----
    This function permanently removes entire directories and files based on where it is located.
    Running it outside the propossed file structure may cause irreversable losses of data
    Execute it it at your own risk
    '''
    base_dir = os.path.dirname(os.path.abspath(__file__))
    audio_dir = os.path.join(base_dir, "audio")

    os.makedirs(audio_dir, exist_ok=True)

    for dir in os.listdir(audio_dir):
        target_path = os.path.join(audio_dir, dir)
        #Only removes directories
        if not os.path.isfile(target_path):
            shutil.rmtree(target_path)
            
    return