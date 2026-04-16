import asyncio
import discord
import os
import random

import downloader
import state

connecting_guild_ids = state.connecting_guild_ids
playlist_manager = state.playlist_manager


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


async def play(message):
    # -------
    voice_client = message.guild.voice_client # Bot voice client
    say = message.channel.send # Send message
    # -------
    url = message.content[5:].strip()

    if not message.author.voice or not message.author.voice.channel:
        await say("No estas en un canal de voz.")
        return
    
    tittle = downloader.download(url,message.guild.id)

    if not tittle:
        await message.channel.send("No se pudo descargar el audio")
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
        await say("No pude conectarme al canal de voz.")
        return

    audio = discord.FFmpegPCMAudio(raw_path)
    voice_client.play(
        audio,
        after=lambda error: asyncio.run_coroutine_threadsafe(
            playlist_next(message.guild.id),
            state.client.loop,
        ),
    )
    await say(f"Reproduciendo {tittle[:-4]}.")
    return




# ---- QUEUE MANAGER ----




async def playlist_add(message):

    url = message.content[5:].strip()
    if not await downloader.valid_url(url):
        await message.channel.send("Url no valida o duración máxima de video excedido (30 min)")
        return

    #Case 1: Nothing is playing
    if message.guild.id not in playlist_manager:
        playlist_manager[message.guild.id] = [message]
        await play(message)

    #Case 2: There is a queue
    else:
        guild_playlist = playlist_manager[message.guild.id]
        guild_playlist.append(message)
        playlist_manager[message.guild.id] = guild_playlist
        await message.channel.send(f"Añadido a la cola. Posición: {len(guild_playlist)-1}")

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

    await play(guild_playlist[0])
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
            await message.channel.send("No hay suficientementes elementos para barajar")
            return
        first = guild_playlist[0]
        rest = guild_playlist[1:]
        random.shuffle(rest)
        shuffled_playlist = [first] + rest
        playlist_manager[message.guild.id] = shuffled_playlist
        await message.channel.send("Lista barajada")
    else:
        await message.channel.send("No hay ninguna lista sonando")
    return