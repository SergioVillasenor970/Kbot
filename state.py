import discord

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
client = discord.Client(intents=intents)
connecting_guild_ids = set()
playlist_manager = dict()