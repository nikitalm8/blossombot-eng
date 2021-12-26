import discord
from discord.ext import commands
import music

cogs = [music]

client = commands.Bot(command_prefix='?', intents=discord.Intents.all(), case_insensitive=True) #prefix


@client.event
async def on_ready():
    game = discord.Game("In Development") #status
    await client.change_presence(status=discord.Status.online, activity=game)

for i in range(len(cogs)):
    cogs[i].setup(client)

client.run("TOKEN HERE") 