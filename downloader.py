import os

import discord
import yt_dlp

def valid_url(url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=False)
        return True
    except:
        return False