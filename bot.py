import os
import discord
from discord.ext import tasks
from dotenv import load_dotenv


import downloader
import player
import state


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD', '')
GUILDS = GUILD.split(",") if GUILD else []

intents = state.intents
intents.message_content = state.intents.message_content
intents.voice_states = state.intents.voice_states
client = state.client
connecting_guild_ids = state.connecting_guild_ids

@tasks.loop(seconds=5.0)
async def auto_dc():
    for vc in client.voice_clients:
        if not vc.is_connected() or not vc.channel:
            continue
        if vc.guild and vc.guild.id in connecting_guild_ids:
            continue

        # Disconnect if channel is empty
        human_members = [member for member in vc.channel.members if not member.bot]
        if len(human_members) <= 0:
            await vc.disconnect()
    

@client.event
async def on_ready():
    print(f'{client.user} is connected to the following guild:\n')
    for guild in client.guilds:
        if guild.name in GUILDS:
                print(
                    f'{guild.name}(id: {guild.id})'
                    )
        else:
            print(
                f'Servidor no autorizado: {guild.name}(id: {guild.id}). Abandonando'
                )
            await guild.leave()

    #Cleans audio files from all servers
    downloader.clean_all_guilds()

    if not auto_dc.is_running():
        auto_dc.start()


async def test(message):
    await message.channel.send("ACK")
    await message.channel.send(f"Latency: {round(client.latency*1000)} ms")
    return

async def help(message):
    # Modify help.txt to change, translate or add commands to the default help message
    try:
        with open("help.txt", "r", encoding="utf-8") as f:
            help_text = f.read()

        embed_message = discord.Embed(
            title="🤖 Comandos del bot",
            description=help_text,
            color=discord.Color.blue()
        )

        await message.channel.send(embed=embed_message)

    except FileNotFoundError:
        await message.channel.send("❌ No se encontró el archivo help.txt")
    return

async def join(message):
    if not message.author.voice or not message.author.voice.channel:
        await message.channel.send ("No estas en un canal de voz.")
        return
    
    # -------
    voice_channel = message.author.voice.channel # User voice channel
    voice_client = message.guild.voice_client # Bot voice client
    say = message.channel.send # Send message
    # -------

    connecting_guild_ids.add(message.guild.id)
    try:
        if voice_client:
            await voice_client.move_to(voice_channel)
        else:
            voice_client = await voice_channel.connect()
    finally:
        connecting_guild_ids.discard(message.guild.id)
    await say(f"Entrando a {voice_channel.name}.")

    if not voice_client:
        voice_client = message.guild.voice_client

    return

async def disconnect(message):
    # -------
    voice_client = message.guild.voice_client # Bot voice client
    say = message.channel.send # Send message
    # -------

    if voice_client:
        await voice_client.disconnect()
        await say("Desconectado del canal.")
        voice_client.cleanup()
        connecting_guild_ids.discard(message.guild.id)
    else:
        await say("No estoy en ningún canal de voz.")
    return

async def pause(message):
    # -------
    voice_client = message.guild.voice_client # Bot voice client
    say = message.channel.send # Send message
    # -------
    if voice_client and voice_client.is_playing():
            voice_client.pause()
            await say("Audio pausado.")
    return

async def resume(message):
    # -------
    voice_client = message.guild.voice_client # Bot voice client
    # -------
    if voice_client and voice_client.is_paused():
            voice_client.resume()
    return


@client.event
async def on_message(message):


# The bot can't read their own messages
    if message.author == client.user:
        return

    content = message.content.strip().lower()

# Commands
    if content == 'ktest':
        await test(message)

    if content == 'kjoin':
        await join(message)
    
    if content == 'kdc' or content == "kdisconnect":
        await disconnect(message)

    if content.startswith('kplay'):
        await player.playlist_add(message)
    
    if content == ('kpause'):
        await pause(message)

    if content == ('kresume'):
        await resume(message)
    
    if content == ('kskip'):
        await player.playlist_next(message.guild.id)
    
    if content == ('kshuffle'):
        await player.playlist_shuffle(message)

    if content == ('khelp'):
        await help(message)


client.run(TOKEN)