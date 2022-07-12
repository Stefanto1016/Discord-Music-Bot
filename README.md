# Discord Music Bot
A Discord music bot implemented using the discord.py API wrapper that can play music when provided a Youtube URL.
The current implementation of the bot supports single-use in any one Discord server.

It extracts information like the video's thumbnail, name, and audio source using youtube_dl to play the song and
display information when needed. 

The bot supports a multitude of commands that can be listed using the "$help" command which includes:
- $join
- $disconnect
- $play
- $pause
- $skip
- $loop
- $np
- $clear
- $queue
- $summon

# References
- discord.py: https://discordpy.readthedocs.io/en/stable/
- youtube_dl: https://github.com/ytdl-org/youtube-dl
