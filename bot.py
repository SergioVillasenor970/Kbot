import os
import discord
from discord.ext import tasks
from dotenv import load_dotenv


import downloader


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
client = discord.Client(intents=intents)
connecting_guild_ids = set()

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
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

    if not auto_dc.is_running():
        auto_dc.start()


async def test(message):
    await message.channel.send("ACK")
    return

async def help(message):
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
    voice_channel = message.author.voice.channel # Canal de voz del usuario
    voice_client = message.guild.voice_client # Cliente de voz del bot
    say = message.channel.send # Enviar mensaje
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
    voice_client = message.guild.voice_client # Cliente de voz del bot
    say = message.channel.send # Enviar mensaje
    # -------

    if voice_client:
        await voice_client.disconnect()
        await say("Desconectado del canal.")
        voice_client.cleanup()
    else:
        await say("No estoy en ningún canal de voz.")
    return

async def pause(message):
    # -------
    voice_client = message.guild.voice_client # Cliente de voz del bot
    say = message.channel.send # Enviar mensaje
    # -------
    if voice_client and voice_client.is_playing():
            voice_client.pause()
            await say("Audio pausado.")
    return

async def resume(message):
    # -------
    voice_client = message.guild.voice_client # Cliente de voz del bot
    # -------
    if voice_client and voice_client.is_paused():
            voice_client.resume()
    return

async def play(message):
    # -------
    voice_client = message.guild.voice_client # Cliente de voz del bot
    say = message.channel.send # Enviar mensaje
    # -------
    url = message.content[5:].strip()

    if not downloader.valid_url(url):
        await say("Url no valida")
        return

    if not message.author.voice or not message.author.voice.channel:
        await say("No estas en un canal de voz.")
        return
    
    tittle = downloader.download(url)

    if not tittle:
        await message.channel.send("No se pudo descargar el audio")
        return

    raw_path = os.path.join(BASE_DIR, "audio", tittle) # Cambiar el nombre del archivo para el video que se quiera reproducir

    
    # -------
    voice_channel = message.author.voice.channel
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
    voice_client.play(audio)
    await say(f"Reproduciendo {tittle[:-4]}.")
    return


@client.event
async def on_message(message):


# Código de seguridad para que el bot no interprete sus propios mensajes
    if message.author == client.user:
        return

    content = message.content.strip().lower()

# Bloques de acciones por comandos
    if content == 'ktest':
        await test(message)

    if content == 'kjoin':
        await join(message)
    
    if content == 'kdc' or content == "kdisconnect":
        await disconnect(message)

    if content.startswith('kplay'):
        await play(message)
    
    if content == ('kpause'):
        await pause(message)

    if content == ('kresume'):
        await resume(message)

    if content == ('khelp'):
        await help(message)


client.run(TOKEN)