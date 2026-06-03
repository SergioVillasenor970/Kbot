import asyncio
import discord
import os
import random

import yt_dlp

import downloader
import state

connecting_guild_ids = state.connecting_guild_ids
playlist_manager = state.playlist_manager


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NUMBER_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]


def _track_message(track):
    if isinstance(track, dict):
        return track["message"]
    return track


def _track_url(track):
    if isinstance(track, dict):
        return track["url"]
    return track.content[5:].strip()


def _looks_like_url(value):
    value = value.strip().lower()
    return value.startswith(("http://", "https://", "www.")) or "youtube.com" in value or "youtu.be" in value


def _format_duration(seconds):
    if seconds is None:
        return ""
    minutes, remaining_seconds = divmod(int(seconds), 60)
    hours, remaining_minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{remaining_minutes:02d}:{remaining_seconds:02d}"
    return f"{remaining_minutes}:{remaining_seconds:02d}"


def search_videos(query):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch5:{query}", download=False)

    entries = info.get("entries") or []
    results = []
    for entry in entries[:5]:
        if not entry:
            continue

        url = entry.get("webpage_url") or entry.get("url") or entry.get("original_url")
        if url and not url.startswith(("http://", "https://")):
            video_id = entry.get("id") or url
            url = f"https://www.youtube.com/watch?v={video_id}"

        if not url:
            continue

        results.append(
            {
                "title": entry.get("title") or "Sin título",
                "url": url,
                "duration": entry.get("duration"),
                "channel": entry.get("channel") or entry.get("uploader") or "",
            }
        )

    return results


async def choose_search_result(message, query):
    results = search_videos(query)

    if not results:
        await message.channel.send(embed=state.blue_embed("No encontré resultados para esa búsqueda.", "⚠️"))
        return None

    lines = []
    for index, result in enumerate(results):
        duration = _format_duration(result["duration"])
        channel = result["channel"]
        extra = []
        if channel:
            extra.append(channel)
        if duration:
            extra.append(duration)
        suffix = f" · {' · '.join(extra)}" if extra else ""
        lines.append(f"{NUMBER_EMOJIS[index]} [{result['title']}]({result['url']}){suffix}")

    embed = discord.Embed(
        title="🔎 Resultados de búsqueda",
        description="\n".join(lines),
        color=discord.Color.blue(),
    )
    embed.set_footer(text="Reacciona con 1️⃣ a 5️⃣ para elegir un video.")

    results_message = await message.channel.send(embed=embed)

    for emoji in NUMBER_EMOJIS[:len(results)]:
        await results_message.add_reaction(emoji)

    def check(reaction, user):
        return (
            reaction.message.id == results_message.id
            and user != state.client.user
            and str(reaction.emoji) in NUMBER_EMOJIS[:len(results)]
        )

    try:
        reaction, user = await state.client.wait_for("reaction_add", timeout=60.0, check=check)
    except asyncio.TimeoutError:
        await message.channel.send(embed=state.blue_embed("No se eligió ningún resultado a tiempo.", "⏱️"))
        return None

    selected_index = NUMBER_EMOJIS.index(str(reaction.emoji))
    selected_result = results[selected_index]

    await results_message.edit(
        embed=state.blue_embed(f"Seleccionado: {selected_result['title']}", "✅")
    )

    return selected_result["url"]


async def play(message, url=None):
    # -------
    voice_client = message.guild.voice_client # Bot voice client
    say = message.channel.send # Send message
    # -------
    url = url or _track_url(message)

    if not message.author.voice or not message.author.voice.channel:
        await say(embed=state.blue_embed("No estas en un canal de voz.", "⚠️"))
        return
    
    tittle = downloader.download(url, message.guild.id)

    if not tittle:
        await message.channel.send(embed=state.blue_embed("No se pudo descargar el audio", "❌"))
        return

    # File that will play
    raw_path = os.path.join(BASE_DIR, "audio", str(message.guild.id), tittle)

    
    # -------
    voice_channel = message.author.voice.channel # User voice channel
    # -------
    
    connecting_guild_ids.add(message.guild.id)
    try:
        if voice_client:
            await voice_client.move_to(voice_channel)
        else:
            voice_client = await voice_channel.connect()
    finally:
        connecting_guild_ids.discard(message.guild.id)

    if not voice_client:
        voice_client = message.guild.voice_client

    if voice_client and voice_client.is_playing():
        voice_client.pause()
    if not voice_client:
        await say(embed=state.blue_embed("No pude conectarme al canal de voz.", "❌"))
        return

    audio = discord.FFmpegPCMAudio(raw_path)
    voice_client.play(
        audio,
        after=lambda error: asyncio.run_coroutine_threadsafe(
            playlist_next(message.guild.id),
            state.client.loop,
        ),
    )
    await say(embed=state.blue_embed(f"Reproduciendo {tittle[:-4]}.", "🎵"))
    return




# ---- QUEUE MANAGER ----




async def playlist_add(message):

    query = message.content[5:].strip()

    if _looks_like_url(query):
        if not await downloader.valid_url(query):
            await message.channel.send(embed=state.blue_embed("Url no valida o duración máxima de video excedido (30 min)", "⚠️"))
            return
        url = query
    else:
        url = await choose_search_result(message, query)
        if not url:
            return
        if not await downloader.valid_url(url):
            await message.channel.send(embed=state.blue_embed("El video seleccionado no es válido o supera 30 min.", "⚠️"))
            return

    track = {
        "message": message,
        "url": url,
    }

    #Case 1: Nothing is playing
    if message.guild.id not in playlist_manager:
        playlist_manager[message.guild.id] = [track]
        await play(message, url)

    #Case 2: There is a queue
    else:
        guild_playlist = playlist_manager[message.guild.id]
        guild_playlist.append(track)
        playlist_manager[message.guild.id] = guild_playlist
        await message.channel.send(embed=state.blue_embed(f"Añadido a la cola. Posición: {len(guild_playlist)-1}", "🎵"))

    return

async def playlist_next(guild_id):
    if guild_id not in playlist_manager:
        return

    guild_playlist = playlist_manager[guild_id]
    if guild_playlist:
        guild_playlist.pop(0)

    if not guild_playlist:
        playlist_clean(guild_id)
        return

    next_track = guild_playlist[0]
    await play(_track_message(next_track), _track_url(next_track))
    return

def playlist_clean(guild_id):
    if guild_id in playlist_manager:
        del playlist_manager[guild_id]
        downloader.clean_files(guild_id)
    return

async def playlist_shuffle(message):
    if message.guild.id in playlist_manager:
        guild_playlist = playlist_manager[message.guild.id]
        if len(guild_playlist) <= 2:
            await message.channel.send(embed=state.blue_embed("No hay suficientementes elementos para barajar", "⚠️"))
            return
        first = guild_playlist[0]
        rest = guild_playlist[1:]
        random.shuffle(rest)
        shuffled_playlist = [first] + rest
        playlist_manager[message.guild.id] = shuffled_playlist
        await message.channel.send(embed=state.blue_embed("Lista barajada", "🔀"))
    else:
        await message.channel.send(embed=state.blue_embed("No hay ninguna lista sonando", "⚠️"))
    return