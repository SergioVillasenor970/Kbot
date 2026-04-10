'''
TODO:
* Cambiar ejecutable yt-dlp
'''

import os

import discord
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )


async def test(message):
    await message.channel.send("ACK")
    return

async def join(message):
    # -------
    voice_channel = message.author.voice.channel # Canal de voz del usuario
    voice_client = message.guild.voice_client # Cliente de voz del bot
    say = message.channel.send # Enviar mensaje
    # -------

    if not message.author.voice or not voice_channel:
        await say("No estas en un canal de voz.")
        return

    voice_channel = message.author.voice.channel
    if voice_client:
        await voice_client.move_to(voice_channel)
    else:
        await voice_channel.connect()
    await say(f"Entrando a {voice_channel.name}.")
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

async def play(message):
    # -------
    voice_channel = message.author.voice.channel # Canal de voz del usuario
    voice_client = message.guild.voice_client # Cliente de voz del bot
    say = message.channel.send # Enviar mensaje
    # -------
    raw_path = os.path.join(BASE_DIR, "audio", "Parklife.webm")
    if not message.author.voice or not message.author.voice.channel:
        await say("No estás en un canal de voz.")
        return

    
    if not voice_client:
        voice_client = await voice_channel.connect()
    elif voice_client.channel != voice_channel:
        await voice_client.move_to(voice_channel)


    if voice_client.is_playing():
            voice_client.pause()
    audio = discord.FFmpegPCMAudio(raw_path)
    voice_client.play(audio)
    await say("Reproduciendo.")
    return

async def pause(message):
    # -------
    voice_client = message.guild.voice_client # Cliente de voz del bot
    # -------
    if voice_client.is_playing():
            voice_client.pause()
    return

async def resume(message):
    # -------
    voice_client = message.guild.voice_client # Cliente de voz del bot
    # -------
    if voice_client.is_paused():
            voice_client.resume()
    return


@client.event
async def on_message(message):


# Código de seguridad para que el bot no interprete sus propios mensajes
    if message.author == client.user:
        return

    content = message.content.strip().lower()

# Bloques de acciones por comandos
    if content == 'test':
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

        

client.run(TOKEN)