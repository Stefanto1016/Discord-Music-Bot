import discord
from discord.ext import commands
import music

bot = commands.Bot(command_prefix='$', help_command=None)

@bot.event
async def on_message(message):
  # Ignore messages sent from the bot itself
  if message.author == await bot.fetch_user(918676569902420018):
    return
  
  
  await bot.process_commands(message)

# Set up bot with music functionality
music.setup(bot)

# Actual TOKEN hidden for anonymity 
bot.run(TOKEN)
