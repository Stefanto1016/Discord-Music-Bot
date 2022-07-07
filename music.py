import discord
from discord.ext import commands, tasks
import math
import youtube_dl
import ffmpeg

# Standard options for FFMPEG
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

# Preliminary checks to ensure that the bot can execute the commands properly and connects to voice when needed
async def voice_check(self, ctx, command=None):
  # User must be in a voice channel to use commands
  if ctx.author.voice is None:
    await ctx.send("Need to be in voice channel")
    return False

  # Checks if bot is in a voice channel
  if ctx.voice_client is None:
    if command == "play" or command == "join":
      self.vclient = await ctx.author.voice.channel.connect()
    else:
      await ctx.send("Bot is not in a voice channel")
      return False
  else:
    if command =="join":
      await ctx.send("Bot already in a voice channel. Use $summon to move the bot to a different voice channel")
      return False

  # Checks if bot and user are in the same voice channel
  if not ctx.author.voice.channel is ctx.voice_client.channel and command != "summon":
    await ctx.send("Need to be in the same channel as the bot")
    return False
  elif ctx.author.voice.channel is ctx.voice_client.channel and command == "summon":
    await ctx.send("Can't summon bot to a voice channel it's currently in")
    return False

  return True

class Music(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.queue = [] # Queue of songs
    self.names = [] # Names of songs in queue
    self.thumbnails = [] # YT thumbnails of songs in queue
    self.urls = [] # YT URLS of songs in queue
    self.vclient = None # Instance of bot voice client
    self.np = None # Current playing song
    self.lp = None # Last played song (used for loop command)
    self.thumbnail = None # Thumbnail of current playing song
    self.url = None # YT URL of current playing song
    self.loop = False # Flag to loop current song

  # Task loop that plays the next song in queue when the current song has ended (if there are any songs in queue)
  @tasks.loop(seconds=2.0)
  async def check_end(self):
    # Checks if bot is no longer playing anything
    if self.vclient.is_playing() is False and self.vclient.is_paused() is False:
      # Loops current playing song if desired
      if self.loop is True:
        audio = await discord.FFmpegOpusAudio.from_probe(self.lp, **FFMPEG_OPTIONS)
        self.vclient.play(audio)
        return
      else:
        self.lp = None

      # More songs in queue, update the data/info and play next song in queue
      if len(self.queue) > 0:
        audio = await discord.FFmpegOpusAudio.from_probe(self.queue[0], **FFMPEG_OPTIONS)
        self.lp = self.queue[0]
        self.vclient.play(audio)
        self.queue.pop(0)
        self.np = self.names[0]
        self.names.pop(0)
        self.url = self.urls[0]
        self.urls.pop(0)
        self.thumbnail = self.thumbnails[0]
        self.thumbnails.pop(0)
        return
    
      # No more songs in queue
      self.np = None
      self.thumbnail = None
      self.url = None
      # Stop task loop since no more songs 
      self.check_end.cancel()
  
  # Connects the bot to a voice channel
  @commands.command()
  async def join(self, ctx):
    # Preliminary check to ensure command is used properly and connect
    if await voice_check(self, ctx, "join") is False:
      return

    await ctx.send(f'{ctx.voice_client.user.mention}' + ' has joined ' + f'{ctx.author.voice.channel.mention}!')
    # Start task loop to play songs continuously 
    self.check_end.start()

  # Disconnects the bot from a voice channel
  @commands.command()
  async def disconnect(self, ctx):
    # Preliminary check to ensure command is used properly
    if await voice_check(self, ctx) is False:
      return

    # Stop task loop since no songs should be playing when the bot is disconnected
    self.check_end.cancel()
    await ctx.send(f'{ctx.voice_client.user.mention}' + ' has disconnected from ' + f'{ctx.author.voice.channel.mention}!')
    await ctx.voice_client.disconnect()

  # Connects the bot to a voice channel and plays a song (or adds songs to the queue)
  @commands.command()
  async def play(self, ctx, url=None):
    # Preliminary check to ensure command is used properly and connect
    if await voice_check(self, ctx, "play") is False:
      return

    if url == None:
      await ctx.send("No URL provided")
      return

    # Standard ydl option to get best audio from YT video
    YDL_OPTIONS = {'format':"bestaudio"}

    try:
      with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        # Extract necessary information about YT video and store them accordingly
        info = ydl.extract_info(url, download=False)
        name = info['title']
        extract = info['formats'][0]['url']
        thumbnail = info['thumbnails'][0]['url']
        self.queue.append(extract)
        self.names.append(name)
        self.urls.append(url)
        self.thumbnails.append(thumbnail)
        # Plays song if nothing is playing
        if ctx.voice_client.is_playing() is False and ctx.voice_client.is_paused() is False:
          audio = await discord.FFmpegOpusAudio.from_probe(self.queue[0], **FFMPEG_OPTIONS)
          self.lp = self.queue[0]
          ctx.voice_client.play(audio)
          self.queue.pop(0)
          self.np = self.names[0]
          self.names.pop(0)
          self.url = self.urls[0]
          self.urls.pop(0)
          self.thumbnail = self.thumbnails[0]
          self.thumbnails.pop(0)
        # Something is currently playing, add song to queue
        else:
          await ctx.send("Song added to queue!")
        # Start task loop to autoplay song if it is not running
        if self.check_end.is_running() is False:
          self.check_end.start()
    except:
      await ctx.send("Invalid Youtube URL")
    
  # Pause or unpauses the current playing song
  @commands.command()
  async def pause(self, ctx):
    # Preliminary check to ensure command is used properly
    if await voice_check(self, ctx) is False:
      return

    if ctx.voice_client.is_playing() is False and ctx.voice_client.is_paused() is False:
      await ctx.send("No song currently playing")
      return

    # Pause or unpauses the current song accordingly
    if ctx.voice_client.is_paused() is True:
      ctx.voice_client.resume()
      await ctx.send("Unpaused!")
    else: 
      ctx.voice_client.pause()
      await ctx.send("Paused!")

  # Loop or unloops the current playing song
  @commands.command()
  async def loop(self, ctx):
    # Preliminary check to ensure command is used properly
    if await voice_check(self, ctx) is False:
      return

    # Loops or unloops the current song accordingly
    if self.loop is False:
      self.loop = True
      await ctx.send("Looping current song!")
    else:
      self.loop = False
      await ctx.send("No longer looping!")

  # Skips the current playing song
  @commands.command()
  async def skip(self, ctx):
    # Preliminary check to ensure command is used properly
    if await voice_check(self, ctx) is False:
      return

    # Stop task loop to autoplay song
    self.check_end.cancel()
 
    if ctx.voice_client.is_playing() is False and ctx.voice_client.is_paused() is False and len(self.queue) == 0:
      await ctx.send("No song currently playing!")
      return

    ctx.voice_client.stop()
    await ctx.send("Skipped!")
    # More songs in queue, play the song coming next up and update data/info
    if len(self.queue) > 0:
      audio = await discord.FFmpegOpusAudio.from_probe(self.queue[0], **FFMPEG_OPTIONS)
      self.lp = self.queue[0]
      ctx.voice_client.play(audio)
      self.queue.pop(0)
      self.np = self.names[0]
      self.names.pop(0)
      self.url = self.urls[0]
      self.urls.pop(0)
      self.thumbnail = self.thumbnails[0]
      self.thumbnails.pop(0)

    # Restart task loop to autoplay song
    self.check_end.start()

  # Displays the current playing song
  @commands.command()
  async def np(self, ctx):
    # Preliminary check to ensure commannd is used properly
    if await voice_check(self, ctx) is False:
      return

    # Display information about current playing song if one exists
    if ctx.voice_client.is_playing() is False and ctx.voice_client.is_paused() is False:
      await ctx.send("Not currently playing anything")
    else:
      embed = discord.Embed(title=self.np, url=self.url, color=discord.Color.red())
      embed.set_author(name="Now Playing", icon_url=self.bot.user.avatar_url)
      embed.set_thumbnail(url=self.thumbnail)
      await ctx.send(embed=embed)

  # Clears the queue of songs
  @commands.command()
  async def clear(self, ctx):
    # Preliminary check to ensure command is used properly
    if await voice_check(self, ctx) is False:
      return

    self.queue.clear()
    self.names.clear()
    self.urls.clear()
    self.thumbnails.clear()
    await ctx.send("Queue cleared!")

  # Moves the bot from one voice channel to another
  @commands.command()
  async def summon(self, ctx):
    # Preliminary check to ensure command is used properly
    if await voice_check(self, ctx, "summon") is False:
      return

    if ctx.voice_client.is_paused() is False:
      await ctx.voice_client.move_to(ctx.author.voice.channel)
      ctx.voice_client.pause()
      ctx.voice_client.resume()
    else:
      await ctx.voice_client.move_to(ctx.author.voice.channel)

    await ctx.send('Moved ' +  f'{ctx.voice_client.user.mention}' + ' to ' + f'{ctx.author.voice.channel.mention}!')

  # Displays the queue of songs (10 songs per page)
  @commands.command()
  async def queue(self, ctx, num=1):
    # Preliminary check to ensure command is used properly
    if await voice_check(self, ctx) is False:
      return

    if num < 1 and not type(num) is int:
      await ctx.send('Page number must be a positive integer')
      return

    if num > math.ceil(len(self.queue) / 10) and len(self.queue) != 0:
      await ctx.send('Invalid page')
      return

    embed = discord.Embed(title='Queue for ' + f'{ctx.guild}', color=discord.Color.red())
    
    # Displays current playing song if it exists
    if ctx.voice_client.is_playing() is False and ctx.voice_client.is_paused() is False:
      embed.add_field(name='__Now Playing:__', value='None', inline=False)
    else:
      embed.add_field(name='__Now Playing:__', value='[' + self.np + '](' + self.url + ')', inline=False)

    # Display the queue of songs depending on the page number provided
    if len(self.queue) == 0:
      embed.add_field(name='__Up Next:__', value=None, inline=False)
    else:
      for x in range((num-1)*10, (num-1)*10+len(self.queue) % 10):
        if x == (num-1)*10:
          embed.add_field(name='__Up Next:__', value=str(x+1) + '. [' + self.names[x] + '](' + self.urls[x] + ')', inline=False)
        else:
          embed.add_field(name='\u200b', value=str(x+1) + '. [' + self.names[x] + '](' + self.urls[x] + ')', inline=False)

    if len(self.queue) == 0:
      embed.set_footer(text='Page 1/1')
    else:
      embed.set_footer(text='Page ' + str(num) + '/' + str(math.ceil(len(self.queue) / 10)))
 
    await ctx.send(embed=embed)

  # Displays a list of valid commands for the bot
  @commands.command()
  async def help(self, ctx):
    embed = discord.Embed(title='Music Commands', color=discord.Color.red())
    embed.add_field(name='$join', value='Connects the bot to a voice channel', inline=False)
    embed.add_field(name='$disconnect', value='Disconnects the bot from a voice channel', inline=False)
    embed.add_field(name='$play [yt url]', value='Connects the bot to a voice channel and plays the song. Adds to queue if something is already playing or if there is already a queue of songs', inline=False)
    embed.add_field(name='$pause', value='Pauses/Unpauses the song', inline=False)
    embed.add_field(name='$skip', value='Skips the current song', inline=False)
    embed.add_field(name='$loop', value='Loops/Unloops the current song', inline=False)
    embed.add_field(name='$np', value='Displays current playing song', inline=False)
    embed.add_field(name='$clear', value='Clears queue of all songs', inline=False)
    embed.add_field(name='$queue [num]', value='Display page [num] of queue (10 songs/page)', inline=False)
    embed.add_field(name='$summon', value='Move the bot from one voice channel to another', inline=False)

    await ctx.send(embed=embed)

# Sets up music functionality for the bot
def setup(bot):
  bot.add_cog(Music(bot))
