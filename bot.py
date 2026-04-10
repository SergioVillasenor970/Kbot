'''
TODO:
* Cambiar ejecutable ffmpeg
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

    

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    i = 0
    lista = list(range(5))

    content = message.content.strip().lower()

    if content == 'test':
        i += 1
        await message.channel.send("ACK")

    if content == 'kjoin':
        if not message.author.voice or not message.author.voice.channel:
            await message.channel.send("No estas en un canal de voz.")
            return

        voice_channel = message.author.voice.channel
        if message.guild.voice_client:
            await message.guild.voice_client.move_to(voice_channel)
        else:
            await voice_channel.connect()
        await message.channel.send(f"Entrando a {voice_channel.name}.")

    if content.startswith('kplay'):
        '''
        raw_path = message.content[5:].strip().strip('"')
        if not raw_path:
            await message.channel.send("Ruta vacia.")
            return
        if not os.path.isfile(raw_path):
            await message.channel.send("No encuentro ese archivo.")
            return
        '''
        raw_path = os.path.join(BASE_DIR, "audio", "Parklife.webm")
        if not message.author.voice or not message.author.voice.channel:
            await message.channel.send("No estás en un canal de voz.")
            return

        voice_channel = message.author.voice.channel
        voice_client = message.guild.voice_client
        if not voice_client:
            voice_client = await voice_channel.connect()
        elif voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)

        if voice_client.is_playing():
            #voice_client.stop()
            voice_client.pause()

        audio = discord.FFmpegPCMAudio(raw_path)
        voice_client.play(audio)
        await message.channel.send("Reproduciendo.")
        

client.run(TOKEN)