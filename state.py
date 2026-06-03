import discord
import time
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.reactions = True
client = discord.Client(intents=intents)
connecting_guild_ids = set()
playlist_manager = dict()
last_playing_time = dict()

# Locks for thread safety
playlist_lock = asyncio.Lock()
download_locks = {}  # Per-guild locks for downloads

#Get or create a lock for a specific guild's downloads.
def get_download_lock(guild_id):
	if guild_id not in download_locks:
		download_locks[guild_id] = asyncio.Lock()
	return download_locks[guild_id]

def blue_embed(text, title=None):
	embed = discord.Embed(description=text, color=discord.Color.blue())
	if title:
		embed.title = title
	return embed