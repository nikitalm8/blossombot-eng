import discord
import asyncio
import os
import youtube_dl
import time

import urllib.parse, urllib.request, re
import requests

from discord.ext import commands
from discord import Embed, FFmpegPCMAudio
from discord.utils import get
from time import sleep

plist = []
queue = []
checker = False
ending = True
killa = False
forloop = ''
loopah = False
qloop = False
nmb = 0
waitfor = False
afkworks = False

client = discord.Client()

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn',
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
}  # исключаем возможность вылета из голоса

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):  # не трогать!
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

        self.queue = queue

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False, play=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream or play))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = queue
        self.checker = checker
        self.plist = plist
        self.ending = ending
        self.killa = killa
        self.loopah = loopah
        self.qloop = qloop
        self.forloop = forloop
        self.nmb = nmb
        self.waitfor = waitfor
        self.afkworks = afkworks

    @commands.command()
    async def join(self, ctx):

        if not ctx.message.author.voice:
            await ctx.send("Ты не в голосе, клоун...")
            return
        else:
            channel = ctx.message.author.voice.channel
            self.queue = {}
            await ctx.send(f'Присоединился к ``{channel}``')
            await channel.connect()

    async def afk(self, ctx):

        global afkworks

        await asyncio.sleep(1)
        afkcount = 0
        while True:
            afkworks = True
            try:
                if ctx.voice_client.is_connected() and not ctx.voice_client.is_playing():
                    print(afkcount)
                    afkcount += 1
                    await asyncio.sleep(60)
                else:
                    await asyncio.sleep(60)
                    afkcount = 0
                if afkcount > 25:
                    queue.clear()
                    plist.clear()
                    killa = True
                    voice_client = ctx.message.guild.voice_client 
                    await voice_client.disconnect() 
                    await ctx.send(f'Я слишком долго был неактивен...')
            except:
                await asyncio.sleep(60)
                afkcount = 0

    @commands.command(aliases=['p'])
    async def play(self, ctx, *, url=None):

        global plist
        global queue
        if not ctx.voice_client.is_connected():
            channel = ctx.message.author.voice.channel
            await channel.connect()
        if not url:
            if len(queue) < 1:
                if ctx.voice_client.is_playing():
                    pass
                if ctx.voice_client.is_paused():
                    voice = get(self.bot.voice_clients, guild=ctx.guild)
                    
                    voice.resume()
                    unpause = self.bot.get_emoji(892866024670646322)
                    last = ctx.channel.last_message_id
                    msg = await ctx.channel.fetch_message(int(last))
                    await msg.add_reaction(unpause)
                if not ctx.voice_client.is_playing():
                    await ctx.send("Нечего включать...")
            else:
                if ctx.voice_client.is_paused():
                    voice = get(self.bot.voice_clients, guild=ctx.guild)
                    
                    voice.resume()
                    unpause = self.bot.get_emoji(892866024670646322)
                    last = ctx.channel.last_message_id
                    msg = await ctx.channel.fetch_message(int(last))
                    await msg.add_reaction(unpause)
                else:
                    await self.player(ctx) and await self.afk(ctx)
        else:
            async with ctx.typing():
                player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
                a = player.title
                plist.append(url)
                queue.append(a)
            if ctx.voice_client.is_playing():
                await ctx.send('**Трек добавлен:** ``{}'.format(player.title) + "``")
            if not ctx.voice_client.is_playing():
                if ctx.voice_client.is_paused():
                    await ctx.send('**Трек добавлен:** ``{}'.format(player.title) + "``")
                    voice = get(self.bot.voice_clients, guild=ctx.guild)      
                    voice.resume()
                else:
                    await self.player(ctx)

    async def player(self, ctx):

        global queue
        global plist
        global checker
        global ending
        global killa
        global loopah
        global qloop
        global forloop
        global nmb
        global waitfor

        nmb = 0

        killa = False

        while True:
                if killa == True:
                    break
                checker = True
                if len(queue) < 1:
                    if ctx.voice_client.is_playing():
                        pass
                    if ctx.voice_client.is_paused():
                        pass
                    if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
                        if loopah == True:
                            await self.looper(ctx)
                        if not loopah == True:
                            checker = False
                            if ending == True:
                                await ctx.send("Очередь кончилась.")
                            if ending == False:
                                pass
                            break
                if ctx.voice_client.is_playing():
                    await asyncio.sleep(5)
                if ctx.voice_client.is_paused():
                    await asyncio.sleep(5)
                if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
                    if loopah == True or qloop == True:
                        async with ctx.typing():
                            await self.looper(ctx)
                    else:
                        if len(queue) > 0:
                            async with ctx.typing():
                                for url in plist:
                                    if ctx.voice_client.is_playing():
                                        voice = get(self.bot.voice_clients, guild=ctx.guild)
                                        voice.stop()
                                    forloop = queue[0]
                                    player = await YTDLSource.from_url(plist[0], loop=self.bot.loop, stream=True)
                                    ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
                                    await self.now(ctx)
                                    del(plist[0])
                                    del(queue[0])
                                else:
                                    pass

    async def now(self, ctx):

        global queue
        global qloop
        global loopah
        global forloop
        global nmb

        if loopah == True:
            nowp = forloop
        if qloop == True:
            nowp = queue[nmb]
        else:
            nowp = queue[0]

        msg = await ctx.channel.fetch_message(ctx.channel.last_message_id)
        if 'Сейчас играет' in msg.content and msg.author.bot:
            await msg.edit(content='<:yt:892878028642852884> **Сейчас играет:** ``' + nowp + '``')
        else:
            await ctx.send('<:yt:892878028642852884> **Сейчас играет:** ``' + nowp + "``")

    async def looper(self, ctx):
        
        global forloop
        global loopah
        global qloop
        global queue
        global plist
        global nmb
        global waitfor

        if qloop == False:
            if forloop == '':
                loopah = False
            if not forloop == '':
                async with ctx.typing():
                    player = await YTDLSource.from_url(forloop, loop=self.bot.loop, stream=True)
                    voice = get(self.bot.voice_clients, guild=ctx.guild)
                    voice.stop()
                    await asyncio.sleep(0.5)
                    ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
                    await self.now(ctx)
        if qloop == True or waitfor == True:
            async with ctx.typing():
                if nmb < len(queue):
                    nmb += 1
                    waitfor = True
                if len(queue) == 0:
                    qloop = False
                    waitfor = False
                if nmb >= len(queue):
                    nmb = 0
                    waitfor = False
                forloop = queue[nmb]
                temp = nmb
                if waitfor == True and qloop == False:
                    temp = nmb - 1
                player = await YTDLSource.from_url(plist[temp], loop=self.bot.loop, stream=True)
                voice = get(self.bot.voice_clients, guild=ctx.guild)
                voice.stop()
                ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
                await self.now(ctx)


    @commands.command()
    async def loop(self, ctx, *, url = None):
        
        global loopah
        global qloop
        global forloop
        global queue
        global plist
        global waitfor

        if not url:
            if loopah == True:
                loopah = False
                qloop = False 
                waitfor = False
                unloop = self.bot.get_emoji(897929571561799690)
                last = ctx.channel.last_message_id
                msg = await ctx.channel.fetch_message(int(last))
                await msg.add_reaction(unloop)
            elif loopah == False:
                qloop = False
                waitfor = False
                loopah = True
                loopemoji1 = self.bot.get_emoji(899987875410636811)
                last = ctx.channel.last_message_id
                msg = await ctx.channel.fetch_message(int(last))
                await msg.add_reaction(loopemoji1)

        if url == 'queue':
            if qloop == True:
                del(queue[0])
                del(plist[0])
                qloop = False
                unloop = self.bot.get_emoji(897929571561799690)
                last = ctx.channel.last_message_id
                msg = await ctx.channel.fetch_message(int(last))
                await msg.add_reaction(unloop)
            elif qloop == False:
                queue.insert(0, forloop)
                plist.insert(0, forloop)
                qloop = True
                loopemoji = self.bot.get_emoji(897929571431776327)
                last = ctx.channel.last_message_id
                msg = await ctx.channel.fetch_message(int(last))
                await msg.add_reaction(loopemoji)
            loopah = False
            
    @commands.command(aliases=['fp'])
    async def qp(self, ctx, *, url):
        
        global checker
        global forloop
        global loopah
        global qloop

        qloop = False
        loopah = False

        if not ctx.voice_client.is_connected():
            channel = ctx.message.author.voice.channel
            await channel.connect()
            await ctx.send(f'Присоединился к ``{channel}``')

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            forloop = player.title
            if ctx.voice_client.is_playing():
                voice = get(self.bot.voice_clients, guild=ctx.guild)
                voice.stop()
            ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
            await ctx.send('<:yt:892878028642852884> **Сейчас играет:** ``{}'.format(player.title) + "``")
        if checker == False:
            await self.player(ctx)

    @commands.command(aliases=['stop'])
    async def pause(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)

        voice.pause()

        pause = self.bot.get_emoji(892866024616132608)
        last = ctx.channel.last_message_id
        msg = await ctx.channel.fetch_message(int(last))
        await msg.add_reaction(pause)

    @commands.command(aliases=['resume'])
    async def unpause(self, ctx):
        if ctx.voice_client.is_paused():
            voice = get(self.bot.voice_clients, guild=ctx.guild)

            voice.resume()

            unpause = self.bot.get_emoji(892866024670646322)
            last = ctx.channel.last_message_id
            msg = await ctx.channel.fetch_message(int(last))
            await msg.add_reaction(unpause)

    @commands.command(aliases=['skip'])
    async def s(self, ctx):
        
        global loopah
        global qloop
        global forloop

        forloop = ''

        if qloop == False:
            loopah == False

        voice = get(self.bot.voice_clients, guild=ctx.guild)

        voice.stop()

        skip = self.bot.get_emoji(892998428609642506)
        last = ctx.channel.last_message_id
        msg = await ctx.channel.fetch_message(int(last))
        await msg.add_reaction(skip)

    @commands.command()
    async def add(self, ctx, *, url):

        global queue
        global plist

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            a = player.title
            queue.append(a)
            plist.append(url)
            await ctx.send('**Трек добавлен:** ``{}'.format(player.title) + "``")

    @commands.command(aliases=['delete', 'del'])
    async def remove(self, ctx, *, number):

        global queue
        global plist

        nn = int(number) - 1

        try:
            if len(queue) < 1:
                await ctx.send("Очередь пуста!")
            else:
                x = queue[nn]
                await ctx.send('Из очереди удален трек: ``' + x + '``')
                del(queue[int(nn)])
                del(plist[int(nn)])
        except:
            await ctx.send("В очереди нет такого трека...")

    @commands.command()
    async def clear(self, ctx):

        global queue
        global plist

        queue.clear()
        plist.clear()
        user = ctx.message.author.mention
        await ctx.send(f"Очередь очистил {user}")

    @commands.command()
    async def queue(self, ctx):
        output = ""
        if len(queue) < 1:
            await ctx.send("Нет треков в очереди")
        else:
            if len(queue) > 10:
                i = 1
                while i <= 10:
                    output += str(i) + ". " + queue[i - 1]  + "\n"
                    i += 1
                output += "И другие...\n"
            if len(queue) > 0 and len(queue) < 11:
                i = 1
                while i <= len(queue):
                    output += str(i) + ". " + queue[i - 1]  + "\n"
                    i += 1
            await ctx.send("**Список треков:**\n```\n" + output + "```")

    @commands.command()
    async def h(self, ctx):
        await ctx.send("```swift\nСписок команд:\n?join / ?leave - управление голосовыми каналами\n?play - проигрывание одного трека / очереди\n?add - добавить в очередь\n?s - пропуск трека\n?pause / ?unpause - управление паузой\n?remove № - убрать из очереди\n?queue - очередь\n?fp / ?qp - проигрывание трека без очереди\n?fs - пропуск всей очереди\n?loop - повтор трека\n```")

    @commands.command()
    async def leave(self, ctx):

        global queue
        global plist
        global killa

        queue.clear()
        plist.clear()
        killa = True
        voice_client = ctx.message.guild.voice_client 
        await voice_client.disconnect() 
        await ctx.send(f'Пока...')


    @commands.command(aliases=['fs'])
    async def end(self, ctx):

        global plist
        global queue
        global ending

        ending = False
        plist.clear()
        queue.clear()

        voice = get(self.bot.voice_clients, guild=ctx.guild)
        voice.stop()
        skip = self.bot.get_emoji(892998428609642506)
        last = ctx.channel.last_message_id
        msg = await ctx.channel.fetch_message(int(last))
        await msg.add_reaction(skip)

    @qp.before_invoke
    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("Ты не в голосе, клоун...")
                raise commands.CommandError("Я не в голосе...")

    @play.after_invoke
    @qp.after_invoke
    @join.after_invoke
    async def ensure_voice(self, ctx):

        global afkworks
        
        if afkworks == False:
            await self.afk(ctx)


def setup(client):
    client.add_cog(Music(client))